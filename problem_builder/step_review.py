#
# Copyright (c) 2014-2015 Harvard, edX & OpenCraft
#
# This software's license gives you freedom; you can copy, convey,
# propagate, redistribute and/or modify this program under the terms of
# the GNU Affero General Public License (AGPL) as published by the Free
# Software Foundation (FSF), either version 3 of the License, or (at your
# option) any later version of the AGPL published by the FSF.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program in a file in the toplevel directory called
# "AGPLv3".  If not, see <http://www.gnu.org/licenses/>.
#

import logging

from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Scope, String
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import (NestedXBlockSpec,
                                         StudioContainerWithNestedXBlocksMixin,
                                         StudioEditableXBlockMixin,
                                         XBlockWithPreviewMixin)

from .mixins import NoSettingsMixin, XBlockWithTranslationServiceMixin
from .utils import I18NService

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


# Make '_' a no-op so we can scrape strings
def _(text):
    return text


@XBlock.needs("i18n")
class ConditionalMessageBlock(
    StudioEditableXBlockMixin, XBlockWithTranslationServiceMixin, XBlockWithPreviewMixin, XBlock
):
    """
    A message shown as part of a Step Builder review step, but only under certain conditions.
    """
    CATEGORY = 'sb-conditional-message'
    STUDIO_LABEL = _("Conditional Message")

    content = String(
        display_name=_("Message"),
        help=_("Message to display upon completion"),
        scope=Scope.content,
        default="",
        multiline_editor="html",
        resettable_editor=False,
    )

    SCORE_PERFECT, SCORE_IMPERFECT, SCORE_ANY = "perfect", "imperfect", "any"
    SCORE_CONDITIONS_DESCRIPTIONS = {
        SCORE_PERFECT: _("Show only if student got a perfect score"),
        SCORE_IMPERFECT: _("Show only if student got at least one question wrong"),
        SCORE_ANY: _("Show for any score"),
    }
    score_condition = String(
        display_name=_("Score condition"),
        default=SCORE_ANY,
        values=[{"display_name": val, "value": key} for key, val in SCORE_CONDITIONS_DESCRIPTIONS.items()],
    )

    IF_ATTEMPTS_REMAIN, IF_NO_ATTEMPTS_REMAIN, ATTEMPTS_ANY = "can_try_again", "cannot_try_again", "any"
    NUM_ATTEMPTS_COND_DESCRIPTIONS = {
        IF_ATTEMPTS_REMAIN: _("Show only if student can try again"),
        IF_NO_ATTEMPTS_REMAIN: _("Show only if student has used up all attempts"),
        ATTEMPTS_ANY: _("Show whether student can try again or not"),
    }
    num_attempts_condition = String(
        display_name=_("Try again condition"),
        default=ATTEMPTS_ANY,
        values=[{"display_name": val, "value": key} for key, val in NUM_ATTEMPTS_COND_DESCRIPTIONS.items()],
    )

    editable_fields = ('content', 'score_condition', 'num_attempts_condition')
    has_author_view = True  # Without this flag, studio will use student_view on newly-added blocks :/

    @property
    def display_name_with_default(self):
        return self._(self.STUDIO_LABEL)

    def is_applicable(self, context):
        """ Return true if this block should appear in the review step, false otherwise """
        score_summary = context['score_summary']
        attempts_remain = not score_summary['max_attempts_reached']
        if (
            (self.num_attempts_condition == self.IF_ATTEMPTS_REMAIN and not attempts_remain) or
            (self.num_attempts_condition == self.IF_NO_ATTEMPTS_REMAIN and attempts_remain)
        ):
            return False

        perfect_score = (score_summary['incorrect_answers'] == 0 and score_summary['partially_correct_answers'] == 0)
        if (
            (self.score_condition == self.SCORE_PERFECT and not perfect_score) or
            (self.score_condition == self.SCORE_IMPERFECT and perfect_score)
        ):
            return False

        return True

    def student_view_data(self, context=None):
        return {
            'block_id': str(self.scope_ids.usage_id),
            'display_name': self.display_name_with_default,
            'type': self.CATEGORY,
            'content': self.content,
            'score_condition': self.score_condition,
            'num_attempts_condition': self.num_attempts_condition,
        }

    def student_view(self, _context=None):
        """ Render this message. """
        html = f'<div class="review-conditional-message">{self.content}</div>'
        return Fragment(html)

    embedded_student_view = student_view

    def author_view(self, context=None):
        fragment = self.student_view(context)
        desc = ""
        if self.num_attempts_condition == self.ATTEMPTS_ANY and self.score_condition == self.SCORE_ANY:
            desc = self._("Always shown")
        else:
            if self.score_condition != self.SCORE_ANY:
                desc += self.SCORE_CONDITIONS_DESCRIPTIONS[self.score_condition] + "<br>"
            if self.num_attempts_condition != self.ATTEMPTS_ANY:
                desc += self.NUM_ATTEMPTS_COND_DESCRIPTIONS[self.num_attempts_condition]
        fragment.content = f'<div class="conditional-message-help"><p>{desc}</p></div>' + fragment.content
        return fragment


@XBlock.needs("i18n")
class ScoreSummaryBlock(XBlockWithTranslationServiceMixin, XBlockWithPreviewMixin,
                        NoSettingsMixin, XBlock, I18NService):
    """
    Summarize the score that the student earned.
    """
    CATEGORY = 'sb-review-score'
    STUDIO_LABEL = _("Score Summary")
    has_author_view = True  # Without this flag, studio will use student_view on newly-added blocks :/

    @property
    def display_name_with_default(self):
        return self._(self.STUDIO_LABEL)

    def student_view(self, context=None):
        """ Render the score summary message. """
        context = context or {}
        html = loader.render_django_template("templates/html/sb-review-score.html",
                                             context.get("score_summary", {}),
                                             i18n_service=self.i18n_service)
        return Fragment(html)

    def student_view_data(self, context=None):
        return {
            'block_id': str(self.scope_ids.usage_id),
            'display_name': self.display_name_with_default,
            'type': self.CATEGORY,
        }

    embedded_student_view = student_view

    def author_view(self, context=None):
        context = context or {}
        if not context.get("score_summary"):
            context["score_summary"] = {
                'score': 75,
                'correct_answers': 3,
                'incorrect_answers': 1,
                'partially_correct_answers': 0,
                'correct': [],
                'incorrect': [],
                'partial': [],
                'complete': True,
                'max_attempts_reached': False,
                'show_extended_review': False,
                'is_example': True,
            }
        return self.student_view(context)


@XBlock.needs("i18n")
class PerQuestionFeedbackBlock(XBlockWithTranslationServiceMixin, XBlockWithPreviewMixin, NoSettingsMixin, XBlock,
                               I18NService):
    """
    Display any on-assessment-review-question messages.
    These messages are defined within individual questions and are only displayed if the student
    got that particular question wrong.
    """
    CATEGORY = 'sb-review-per-question-feedback'
    STUDIO_LABEL = _("Per-Question Feedback")
    has_author_view = True  # Without this flag, studio will use student_view on newly-added blocks :/

    @property
    def display_name_with_default(self):
        return self._(self.STUDIO_LABEL)

    def student_view(self, context=None):
        """ Render the per-question feedback, if any. """
        review_tips = (context or {}).get("score_summary", {}).get("review_tips")
        if review_tips:
            html = loader.render_django_template("templates/html/sb-review-per-question-feedback.html", {
                'tips': review_tips,
            }, i18n_service=self.i18n_service)
        else:
            html = ""
        return Fragment(html)

    def student_view_data(self, context=None):
        return {
            'block_id': str(self.scope_ids.usage_id),
            'display_name': self.display_name_with_default,
            'type': self.CATEGORY,
        }

    embedded_student_view = student_view

    def author_view(self, context=None):
        """ Show example content in Studio """
        context = context or {}
        if not context.get("per_question_review_tips"):
            example = self._("(Example tip:) Since you got Question 1 wrong, review Chapter 12 of your textbook.")
            context["score_summary"] = {"review_tips": [example]}
        return self.student_view(context)


@XBlock.needs("i18n")
class ReviewStepBlock(
    StudioContainerWithNestedXBlocksMixin,
    XBlockWithTranslationServiceMixin,
    XBlockWithPreviewMixin,
    NoSettingsMixin,
    XBlock
):
    """
    A dedicated step for reviewing results as the last step of a Step Builder sequence.
    """
    CATEGORY = 'sb-review-step'
    STUDIO_LABEL = _("Review Step")

    display_name = String(
        default="Review Step"
    )

    @property
    def allowed_nested_blocks(self):
        """
        Returns a list of allowed nested XBlocks. Each item can be either
        * An XBlock class
        * A NestedXBlockSpec

        If XBlock class is used it is assumed that this XBlock is enabled and allows multiple instances.
        NestedXBlockSpec allows explicitly setting disabled/enabled state,
        disabled reason (if any) and single/multiple instances.
        """
        return [
            ConditionalMessageBlock,
            NestedXBlockSpec(None, category='html', label=self._("HTML")),
            NestedXBlockSpec(ScoreSummaryBlock, single_instance=True),
            NestedXBlockSpec(PerQuestionFeedbackBlock, single_instance=True),
        ]

    def student_view(self, context=None):
        """
        Normal view of the review step.

        The parent Step Builder block should pass in appropriate context information:
        - score_summary
        """
        context = context.copy() if context else {}
        fragment = Fragment()

        if "score_summary" not in context:
            fragment.add_content("Error: This block only works inside a Step Builder block.")
        elif not context["score_summary"]:
            # Note: The following text should never be seen (in theory) so does not need to be translated.
            fragment.add_content("Your score and review messages will appear here.")
        else:
            for child_id in self.children:
                child = self.runtime.get_block(child_id)
                if child is None:  # child should not be None but it can happen due to bugs or permission issues
                    fragment.add_content('<p>[Error: Unable to load child component.]</p>')
                else:
                    if hasattr(child, 'is_applicable'):
                        if not child.is_applicable(context):
                            continue  # Hide conditional messages that don't meet their criteria
                    # Render children as "embedded_student_view" rather than "student_view" so
                    # that Studio doesn't wrap with with unwanted controls and the XBlock SDK
                    # workbench doesn't add the acid-aside to the fragment.
                    child_fragment = self._render_child_fragment(child, context, view="embedded_student_view")
                    fragment.add_fragment_resources(child_fragment)
                    fragment.add_content(child_fragment.content)

        return fragment

    def student_view_data(self, context=None):
        context = context.copy() if context else {}
        components = []

        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            if hasattr(child, 'student_view_data'):
                if hasattr(context, 'score_summary') and hasattr(child, 'is_applicable'):
                    if not child.is_applicable(context):
                        continue
                components.append(child.student_view_data(context))

        return {
            'block_id': str(self.scope_ids.usage_id),
            'display_name': self.display_name,
            'type': self.CATEGORY,
            'title': self.display_name,
            'components': components,
        }

    mentoring_view = student_view

    def author_edit_view(self, context):
        """
        Add some HTML to the author view that allows authors to add child blocks.
        """
        fragment = super().author_edit_view(context)
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder.css'))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder-edit.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/util.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/container_edit.js'))
        fragment.initialize_js('ProblemBuilderContainerEdit')
        return fragment
