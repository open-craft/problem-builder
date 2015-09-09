from lazy import lazy
from xblock.fields import String, Boolean, Scope
from xblockutils.helpers import child_isinstance
from xblockutils.resources import ResourceLoader


loader = ResourceLoader(__name__)


# Make '_' a no-op so we can scrape strings
def _(text):
    return text


def _normalize_id(key):
    """
    Helper method to normalize a key to avoid issues where some keys have version/branch and others don't.
    e.g. self.scope_ids.usage_id != self.runtime.get_block(self.scope_ids.usage_id).scope_ids.usage_id
    """
    if hasattr(key, "for_branch"):
        key = key.for_branch(None)
    if hasattr(key, "for_version"):
        key = key.for_version(None)
    return key


class XBlockWithTranslationServiceMixin(object):
    """
    Mixin providing access to i18n service
    """
    def _(self, text):
        """ Translate text """
        return self.runtime.service(self, "i18n").ugettext(text)


class EnumerableChildMixin(XBlockWithTranslationServiceMixin):
    CAPTION = _(u"Child")

    show_title = Boolean(
        display_name=_("Show title"),
        help=_("Display the title?"),
        default=True,
        scope=Scope.content
    )

    @lazy
    def siblings(self):
        # TODO: It might make sense to provide a default
        # implementation here that just returns normalized ID's of the
        # parent's children.
        raise NotImplementedError("Should be overridden in child class")

    @lazy
    def step_number(self):
        return list(self.siblings).index(_normalize_id(self.scope_ids.usage_id)) + 1

    @lazy
    def lonely_child(self):
        if _normalize_id(self.scope_ids.usage_id) not in self.siblings:
            message = u"{child_caption}'s parent should contain {child_caption}".format(child_caption=self.CAPTION)
            raise ValueError(message, self, self.siblings)
        return len(self.siblings) == 1

    @property
    def display_name_with_default(self):
        """ Get the title/display_name of this question. """
        if self.display_name:
            return self.display_name
        if not self.lonely_child:
            return self._(u"{child_caption} {number}").format(
                child_caption=self.CAPTION, number=self.step_number
            )
        return self._(self.CAPTION)


class StepParentMixin(object):
    """
    An XBlock mixin for a parent block containing Step children
    """

    @lazy
    def steps(self):
        """
        Get the usage_ids of all of this XBlock's children that are "Steps"
        """
        return [
            _normalize_id(child_id) for child_id in self.children if child_isinstance(self, child_id, QuestionMixin)
        ]

    def get_steps(self):
        """ Get the step children of this block, cached if possible. """
        if getattr(self, "_steps_cache", None) is None:
            self._steps_cache = [self.runtime.get_block(child_id) for child_id in self.steps]
        return self._steps_cache


class QuestionMixin(EnumerableChildMixin):
    """
    An XBlock mixin for a child block that is a "Step".

    A step is a question that the user can answer (as opposed to a read-only child).
    """
    CAPTION = _(u"Question")

    has_author_view = True

    # Fields:
    display_name = String(
        display_name=_("Question title"),
        help=_('Leave blank to use the default ("Question 1", "Question 2", etc.)'),
        default="",  # Blank will use 'Question x' - see display_name_with_default
        scope=Scope.content
    )

    @lazy
    def siblings(self):
        return self.get_parent().steps

    def author_view(self, context):
        context = context.copy() if context else {}
        context['hide_header'] = True
        return self.mentoring_view(context)

    def author_preview_view(self, context):
        context = context.copy() if context else {}
        context['hide_header'] = True
        return self.student_view(context)

    def assessment_step_view(self, context=None):
        """
        assessment_step_view is the same as mentoring_view, except its DIV will have a different
        class (.xblock-v1-assessment_step_view) that we use for assessments to hide all the
        steps with CSS and to detect which children of mentoring are "Steps" and which are just
        decorative elements/instructions.
        """
        return self.mentoring_view(context)
