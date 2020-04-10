# -*- coding: utf-8 -*-
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

# Imports ###########################################################

import json
import logging
from collections import namedtuple
from decimal import ROUND_HALF_UP, Decimal
from itertools import chain

import six
from lazy.lazy import lazy
from xblock.core import XBlock
from xblock.exceptions import JsonHandlerError, NoSuchViewError
from xblock.fields import Boolean, Float, Integer, List, Scope, String
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage
from xblockutils.helpers import child_isinstance
from xblockutils.resources import ResourceLoader
from xblockutils.settings import XBlockWithSettingsMixin
from xblockutils.studio_editable import (NestedXBlockSpec,
                                         StudioContainerWithNestedXBlocksMixin,
                                         StudioEditableXBlockMixin)

from problem_builder.answer import AnswerBlock, AnswerRecapBlock
from problem_builder.completion import CompletionBlock
from problem_builder.mcq import MCQBlock, RatingBlock
from problem_builder.mrq import MRQBlock
from problem_builder.plot import PlotBlock
from problem_builder.slider import SliderBlock
from problem_builder.swipe import SwipeBlock
from problem_builder.table import MentoringTableBlock

from .message import MentoringMessageBlock, get_message_label
from .mixins import (ExpandStaticURLMixin, MessageParentMixin, QuestionMixin,
                     StepParentMixin, StudentViewUserStateMixin,
                     StudentViewUserStateResultsTransformerMixin,
                     XBlockWithTranslationServiceMixin, _normalize_id)
from .step_review import ReviewStepBlock
from .utils import I18NService

try:
    # Used to detect if we're in the workbench so we can add Font Awesome
    from workbench.runtime import WorkbenchRuntime
except ImportError:
    WorkbenchRuntime = False

# Globals ###########################################################

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)

_default_options_config = {
    'pb_mcq_hide_previous_answer': False,  # this works for both MCQs and MRQs.
    'pb_hide_feedback_if_attempts_remain': False,
}


# Make '_' a no-op so we can scrape strings
def _(text):
    return text

# Classes ###########################################################


Score = namedtuple("Score", ["raw", "percentage", "correct", "incorrect", "partially_correct"])

CORRECT = 'correct'
INCORRECT = 'incorrect'
PARTIAL = 'partial'


@XBlock.needs("i18n")
@XBlock.wants('settings')
class BaseMentoringBlock(
    XBlock, XBlockWithTranslationServiceMixin, XBlockWithSettingsMixin,
    StudioEditableXBlockMixin, MessageParentMixin, StudentViewUserStateMixin,
    ExpandStaticURLMixin
):
    """
    An XBlock that defines functionality shared by mentoring blocks.
    """
    # Content
    show_title = Boolean(
        display_name=_("Show title"),
        help=_("Display the title?"),
        default=True,
        scope=Scope.content
    )
    max_attempts = Integer(
        display_name=_("Max. attempts allowed"),
        help=_("Maximum number of times students are allowed to attempt the questions belonging to this block"),
        default=0,
        scope=Scope.content,
        enforce_type=True
    )
    weight = Float(
        display_name=_("Weight"),
        help=_("Defines the maximum total grade of the block."),
        default=1,
        scope=Scope.settings,
        enforce_type=True
    )

    # User state
    num_attempts = Integer(
        # Number of attempts a user has answered for this questions
        default=0,
        scope=Scope.user_state,
        enforce_type=True
    )

    has_children = True
    has_score = True  # The Problem/Step Builder XBlocks produce scores. (Their children do not send scores to the LMS.)

    icon_class = 'problem'
    block_settings_key = 'mentoring'
    options_key = 'options'

    @property
    def url_name(self):
        """
        Get the url_name for this block. In Studio/LMS it is provided by a mixin, so we just
        defer to super(). In the workbench or any other platform, we use the usage_id.
        """
        try:
            return super(BaseMentoringBlock, self).url_name
        except AttributeError:
            return six.text_type(self.scope_ids.usage_id)

    @property
    def review_tips_json(self):
        return json.dumps(self.review_tips)

    @property
    def max_attempts_reached(self):
        return self.max_attempts > 0 and self.num_attempts >= self.max_attempts

    def get_content_titles(self):
        """
        By default, each Sequential block in a course ("Subsection" in Studio parlance) will
        display the display_name of each descendant in a tooltip above the content. We don't
        want that - we only want to display one title for this mentoring block as a whole.
        Otherwise things like "Choice (yes) (Correct)" will appear in the tooltip.

        If this block has no title set, don't display any title. Then, if this is the only block
        in the unit, the unit's title will be used. (Why isn't it always just used?)
        """
        has_explicitly_set_title = self.fields['display_name'].is_set_on(self)
        if has_explicitly_set_title:
            return [self.display_name]
        return []

    def get_options(self):
        """
        Get options settings for this block from settings service.

        Fall back on default options if xblock settings have not been customized at all
        or no customizations for options available.
        """
        xblock_settings = self.get_xblock_settings(default={})
        if xblock_settings and self.options_key in xblock_settings:
            return xblock_settings[self.options_key]
        return _default_options_config

    def get_option(self, option):
        """
        Get value of a specific instance-wide `option`.
        """
        return self.get_options().get(option)

    @XBlock.json_handler
    def view(self, data, suffix=''):
        """
        Current HTML view of the XBlock, for refresh by client
        """
        frag = self.student_view({})
        return {'html': frag.content}

    @XBlock.json_handler
    def publish_event(self, data, suffix=''):
        """
        Publish data for analytics purposes
        """
        event_type = data.pop('event_type')
        if (event_type == 'grade'):
            # This handler can be called from the browser. Don't allow the browser to submit arbitrary grades ;-)
            raise JsonHandlerError(403, "Posting grade events from the browser is forbidden.")

        self.runtime.publish(self, event_type, data)
        return {'result': 'ok'}

    def author_preview_view(self, context):
        """
        Child blocks can override this to add a custom preview shown to
        authors in Studio when not editing this block's children.
        """
        fragment = self.student_view(context)
        fragment.add_content(loader.render_django_template('templates/html/mentoring_url_name.html', {
            "url_name": self.url_name
        }))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder-edit.css'))
        return fragment

    def max_score(self):
        """ Maximum score. We scale all scores to a maximum of 1.0 so this is always 1.0 """
        return 1.0


class MentoringBlock(
    StudentViewUserStateResultsTransformerMixin, I18NService,
    BaseMentoringBlock, StudioContainerWithNestedXBlocksMixin, StepParentMixin,
):
    """
    An XBlock providing mentoring capabilities

    Composed of text, answers input fields, and a set of MRQ/MCQ with advices.
    A set of conditions on the provided answers and MCQ/MRQ choices will determine if the
    student is a) provided mentoring advices and asked to alter his answer, or b) is given the
    ok to continue.
    """
    # Content
    USER_STATE_FIELDS = ['completed', 'num_attempts', 'student_results']
    followed_by = String(
        display_name=_("Followed by"),
        help=_("url_name of the step after the current mentoring block in workflow."),
        default=None,
        scope=Scope.content
    )
    enforce_dependency = Boolean(
        display_name=_("Enforce Dependency"),
        help=_("Should the next step be the current block to complete?"),
        default=False,
        scope=Scope.content,
        enforce_type=True
    )
    display_submit = Boolean(
        display_name=_("Show Submit Button"),
        help=_("Allow submission of the current block?"),
        default=True,
        scope=Scope.content,
        enforce_type=True
    )
    xml_content = String(
        display_name=_("XML content"),
        help=_("Not used for version 2. This field is here only to preserve the data needed to upgrade from v1 to v2."),
        default='',
        scope=Scope.content,
        multiline_editor=True
    )

    # Settings
    display_name = String(
        display_name=_("Title (Display name)"),
        help=_("Title to display"),
        default=_("Problem Builder"),
        scope=Scope.settings
    )
    feedback_label = String(
        display_name=_("Feedback Header"),
        help=_("Header for feedback messages"),
        default=_("Feedback"),
        scope=Scope.content
    )

    # User state
    attempted = Boolean(
        # Has the student attempted this mentoring step?
        default=False,
        scope=Scope.user_state
        # TODO: Does anything use this 'attempted' field? May want to delete it.
    )
    completed = Boolean(
        # Has the student completed this mentoring step?
        default=False,
        scope=Scope.user_state
    )
    step = Integer(
        # Keep track of the student assessment progress.
        default=0,
        scope=Scope.user_state,
        enforce_type=True
    )
    student_results = List(
        # Store results of student choices.
        default=[],
        scope=Scope.user_state
    )
    extended_feedback = Boolean(
        help=_("Show extended feedback details when all attempts are used up."),
        default=False,
        Scope=Scope.content
    )

    # Global user state
    next_step = String(
        # url_name of the next step the student must complete (global to all blocks)
        default='mentoring_first',
        scope=Scope.preferences
    )

    editable_fields = (
        'display_name', 'followed_by', 'max_attempts', 'enforce_dependency',
        'display_submit', 'feedback_label', 'weight', 'extended_feedback'
    )

    @property
    def allowed_nested_blocks(self):
        """
        Returns a list of allowed nested XBlocks. Each item can be either
        * An XBlock class
        * A NestedXBlockSpec

        If XBlock class is used it is assumed that this XBlock is enabled and allows multiple instances.
        NestedXBlockSpec allows explicitly setting disabled/enabled state, disabled reason (if any) and single/multiple
        instances
        """
        additional_blocks = []
        try:
            from xmodule.video_module.video_module import VideoDescriptor
            additional_blocks.append(NestedXBlockSpec(
                VideoDescriptor, category='video', label=_(u"Video")
            ))
        except ImportError:
            pass
        try:
            from imagemodal import ImageModal
            additional_blocks.append(NestedXBlockSpec(
                ImageModal, category='imagemodal', label=_(u"Image Modal")
            ))
        except ImportError:
            pass

        try:
            from xblock_django.models import XBlockConfiguration
            opt = XBlockConfiguration.objects.filter(name="pb-swipe")
            if opt.count() and opt.first().enabled:
                additional_blocks.append(SwipeBlock)
        except ImportError:
            pass

        try:
            from ooyala_player import OoyalaPlayerBlock
            additional_blocks.append(NestedXBlockSpec(
                OoyalaPlayerBlock, category='ooyala-player', label=_(u"Ooyala Player")
            ))
        except ImportError:
            pass

        message_block_shims = [
            NestedXBlockSpec(
                MentoringMessageBlock,
                category='pb-message',
                boilerplate=message_type,
                label=get_message_label(message_type),
            )
            for message_type in (
                'completed',
                'incomplete',
                'max_attempts_reached',
            )
        ]

        return [
            NestedXBlockSpec(AnswerBlock, boilerplate='studio_default'),
            MCQBlock, RatingBlock, MRQBlock, CompletionBlock,
            NestedXBlockSpec(None, category="html", label=self._("HTML")),
            AnswerRecapBlock, MentoringTableBlock, PlotBlock, SliderBlock
        ] + additional_blocks + message_block_shims

    def get_question_number(self, question_id):
        """
        Get the step number of the question id
        """
        for child_id in self.children:
            question = self.runtime.get_block(child_id)
            if isinstance(question, QuestionMixin) and (question.name == question_id):
                return question.step_number
        raise ValueError("Question ID in answer set not a step of this Mentoring Block!")

    def answer_mapper(self, answer_status):
        """
        Create a JSON-dumpable object with readable key names from a list of student answers.
        """
        answer_map = []
        for answer in self.student_results:
            if answer[1]['status'] == answer_status:
                try:
                    answer_map.append({
                        'number': self.get_question_number(answer[0]),
                        'id': answer[0],
                        'details': answer[1],
                    })
                except ValueError:
                    pass  # The question has been deleted since the student answered it.
        return answer_map

    @property
    def score(self):
        """Compute the student score taking into account the weight of each step."""
        steps = self.steps
        steps_map = {q.name: q for q in steps}
        total_child_weight = sum(float(step.weight) for step in steps)
        if total_child_weight == 0:
            return Score(0, 0, [], [], [])
        points_earned = 0
        for q_name, q_details in self.student_results:
            question = steps_map.get(q_name)
            if question:
                points_earned += q_details['score'] * question.weight
        score = Decimal(points_earned) / Decimal(total_child_weight)
        correct = self.answer_mapper(CORRECT)
        incorrect = self.answer_mapper(INCORRECT)
        partially_correct = self.answer_mapper(PARTIAL)

        return Score(
            float(score),
            int(Decimal(score * 100).quantize(Decimal('1.'), rounding=ROUND_HALF_UP)),
            correct,
            incorrect,
            partially_correct
        )

    @XBlock.supports("multi_device")  # Mark as mobile-friendly
    def student_view(self, context):
        from .questionnaire import QuestionnaireAbstractBlock  # Import here to avoid circular dependency

        # Migrate stored data if necessary
        self.migrate_fields()

        # Validate self.step:
        num_steps = len(self.steps)
        if self.step > num_steps:
            self.step = num_steps

        fragment = Fragment()
        child_content = u""

        mcq_hide_previous_answer = self.get_option('pb_mcq_hide_previous_answer')

        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            if child is None:  # child should not be None but it can happen due to bugs or permission issues
                child_content += u"<p>[{}]</p>".format(self._(u"Error: Unable to load child component."))
            elif not isinstance(child, MentoringMessageBlock):
                try:
                    if mcq_hide_previous_answer and isinstance(child, QuestionnaireAbstractBlock):
                        context['hide_prev_answer'] = True
                    else:
                        context['hide_prev_answer'] = False
                    child_fragment = child.render('mentoring_view', context)
                except NoSuchViewError:
                    if child.scope_ids.block_type == 'html' and getattr(self.runtime, 'is_author_mode', False):
                        # html block doesn't support mentoring_view, and if we use student_view Studio will wrap
                        # it in HTML that we don't want in the preview. So just render its HTML directly:
                        child_fragment = Fragment(child.data)
                    else:
                        child_fragment = child.render('student_view', context)
                fragment.add_frag_resources(child_fragment)
                child_content += child_fragment.content

        fragment.add_content(loader.render_django_template('templates/html/mentoring.html', {
            'self': self,
            'title': self.display_name,
            'show_title': self.show_title,
            'child_content': child_content,
            'missing_dependency_url': self.has_missing_dependency and self.next_step_url,
        }, i18n_service=self.i18n_service))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/vendor/underscore-min.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/util.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/mentoring_standard_view.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/mentoring.js'))
        fragment.add_resource(loader.load_unicode('templates/html/mentoring_attempts.underscore'), "text/html")

        # Workbench doesn't have font awesome, so add it:
        if WorkbenchRuntime and isinstance(self.runtime, WorkbenchRuntime):
            fragment.add_css_url('//maxcdn.bootstrapcdn.com/font-awesome/4.3.0/css/font-awesome.min.css')

        fragment.initialize_js('MentoringBlock')

        if not self.display_submit:
            self.runtime.publish(self, 'progress', {})

        return fragment

    def migrate_fields(self):
        """
        Migrate data stored in the fields, when a format change breaks backward-compatibility with
        previous data formats
        """
        # Partial answers replaced the `completed` with `status` in `self.student_results`
        if self.student_results and 'completed' in self.student_results[0][1]:
            # Rename the field and use the new value format (text instead of boolean)
            for result in self.student_results:
                result[1]['status'] = 'correct' if result[1]['completed'] else 'incorrect'
                del result[1]['completed']

    @property
    def additional_publish_event_data(self):
        return {
            'user_id': self.scope_ids.user_id,
            'component_id': self.url_name,
        }

    @property
    def has_missing_dependency(self):
        """
        Returns True if the student needs to complete another step before being able to complete
        the current one, and False otherwise
        """
        return self.enforce_dependency and (not self.completed) and (self.next_step != self.url_name)

    @property
    def next_step_url(self):
        """
        Returns the URL of the next step's page
        """
        return '/jump_to_id/{}'.format(self.next_step)

    @property
    def hide_feedback(self):
        return self.get_option("pb_hide_feedback_if_attempts_remain") and not self.max_attempts_reached

    def get_message(self, completed):
        """
        Get the message to display to a student following a submission.
        """
        if completed:
            # Student has achieved a perfect score
            return self.get_message_content('completed')
        elif self.max_attempts_reached:
            # Student has not achieved a perfect score and cannot try again
            return self.get_message_content('max_attempts_reached')
        else:
            # Student did not achieve a perfect score but can try again:
            return self.get_message_content('incomplete')

    @property
    def review_tips(self):
        review_tips = []
        return review_tips

    def show_extended_feedback(self):
        return self.extended_feedback and self.max_attempts_reached

    @XBlock.json_handler
    def get_results(self, queries, suffix=''):
        """
        Gets detailed results in the case of extended feedback.

        Right now there are two ways to get results-- through the template upon loading up
        the mentoring block, or after submission of an AJAX request like in
        submit or get_results here.
        """
        results, completed, show_message = self._get_standard_results()
        mentoring_completed = completed

        result = {
            'results': results,
            'completed': completed,
            'step': self.step,
            'max_attempts': self.max_attempts,
            'num_attempts': self.num_attempts,
        }

        if show_message:
            result['message'] = self.get_message(mentoring_completed)

        return result

    def _get_standard_results(self):
        """
        Gets previous submissions results as if submit was called with exactly the same values as last time.
        """
        results = []
        completed = True
        show_message = (not self.hide_feedback) and bool(self.student_results)

        # All children are visible simultaneously, so need to collect results for all of them
        for child in self.steps:
            child_result = child.get_last_result()
            results.append([child.name, child_result])
            completed = completed and (child_result.get('status', None) == 'correct')

        return results, completed, show_message

    @XBlock.json_handler
    def submit(self, submissions, suffix=''):
        log.info(u'Received submissions: {}'.format(submissions))
        # server-side check that the user is allowed to submit:
        if self.max_attempts_reached:
            raise JsonHandlerError(403, "Maximum number of attempts already reached.")
        if self.has_missing_dependency:
            raise JsonHandlerError(
                403,
                "You need to complete all previous steps before being able to complete the current one."
            )

        # This has now been attempted:
        self.attempted = True

        submit_results = []
        previously_completed = self.completed
        completed = True
        for child in self.steps:
            if child.name and child.name in submissions:
                submission = submissions[child.name]
                child_result = child.submit(submission)
                submit_results.append([child.name, child_result])
                child.save()
                completed = completed and (child_result['status'] == 'correct')

        if completed and self.next_step == self.url_name:
            self.next_step = self.followed_by

        # Update the score and attempts, unless the user had already achieved a perfect score ("completed"):
        if not previously_completed:
            # Update the results
            while self.student_results:
                self.student_results.pop()
            for result in submit_results:
                self.student_results.append(result)

            # Save the user's latest score
            self.runtime.publish(self, 'grade', {
                'value': self.score.raw,
                'max_value': self.max_score(),
            })

            # Mark this as having used an attempt:
            if self.max_attempts > 0:
                self.num_attempts += 1

        # Save the completion status.
        # Once it has been completed once, keep completion even if user changes values
        self.completed = bool(completed) or previously_completed

        message = self.get_message(completed)
        raw_score = self.score.raw

        self.runtime.publish(self, 'xblock.problem_builder.submitted', {
            'num_attempts': self.num_attempts,
            'submitted_answer': submissions,
            'grade': raw_score,
        })

        return {
            'results': submit_results,
            'completed': self.completed,
            'message': message,
            'max_attempts': self.max_attempts,
            'num_attempts': self.num_attempts,
        }

    def feedback_dispatch(self, target_data, stringify):
        if self.show_extended_feedback():
            if stringify:
                return json.dumps(target_data)
            else:
                return target_data

    def correct_json(self, stringify=True):
        return self.feedback_dispatch(self.score.correct, stringify)

    def incorrect_json(self, stringify=True):
        return self.feedback_dispatch(self.score.incorrect, stringify)

    def partial_json(self, stringify=True):
        return self.feedback_dispatch(self.score.partially_correct, stringify)

    @XBlock.json_handler
    def try_again(self, data, suffix=''):

        if self.max_attempts_reached:
            return {
                'result': 'error',
                'message': 'max attempts reached'
            }

        # reset
        self.step = 0
        self.completed = False

        while self.student_results:
            self.student_results.pop()

        return {
            'result': 'success'
        }

    def validate(self):
        """
        Validates the state of this XBlock except for individual field values.
        """
        validation = super(MentoringBlock, self).validate()
        a_child_has_issues = False
        message_types_present = set()
        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            # Check if the child has any errors:
            if not child.validate().empty:
                a_child_has_issues = True
            # Ensure there is only one "message" block of each type:
            if isinstance(child, MentoringMessageBlock):
                msg_type = child.type
                if msg_type in message_types_present:
                    validation.add(ValidationMessage(
                        ValidationMessage.ERROR,
                        self._(u"There should only be one '{msg_type}' message component.").format(msg_type=msg_type)
                    ))
                message_types_present.add(msg_type)
        if a_child_has_issues:
            validation.add(ValidationMessage(
                ValidationMessage.ERROR,
                self._(u"A component inside this mentoring block has issues.")
            ))
        return validation

    def author_edit_view(self, context):
        """
        Add some HTML to the author view that allows authors to add child blocks.
        """
        local_context = context.copy()
        local_context['author_edit_view'] = True
        fragment = super(MentoringBlock, self).author_edit_view(local_context)
        fragment.add_content(loader.render_django_template('templates/html/mentoring_url_name.html', {
            'url_name': self.url_name
        }))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder.css'))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder-edit.css'))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder-tinymce-content.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/util.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/container_edit.js'))
        fragment.initialize_js('ProblemBuilderContainerEdit')

        return fragment

    @staticmethod
    def workbench_scenarios():
        """
        Scenarios displayed by the workbench. Load them from external (private) repository
        """
        return loader.load_scenarios_from_path('templates/xml')

    def student_view_data(self, context=None):
        """
        Returns a JSON representation of the student_view of this XBlock,
        retrievable from the Course Block API.
        """
        components = []
        for child_id in self.children:
            block = self.runtime.get_block(child_id)
            if hasattr(block, 'student_view_data'):
                components.append(block.student_view_data())

        return {
            'block_id': six.text_type(self.scope_ids.usage_id),
            'display_name': self.display_name,
            'max_attempts': self.max_attempts,
            'extended_feedback': self.extended_feedback,
            'feedback_label': self.feedback_label,
            'components': components,
            'messages': {
                message_type: self.expand_static_url(self.get_message_content(message_type))
                for message_type in (
                        'completed',
                        'incomplete',
                        'max_attempts_reached',
                )
            }
        }


class MentoringWithExplicitStepsBlock(BaseMentoringBlock, StudioContainerWithNestedXBlocksMixin,
                                      I18NService):
    """
    An XBlock providing mentoring capabilities with explicit steps
    """
    USER_STATE_FIELDS = ['num_attempts']

    # Content
    extended_feedback = Boolean(
        display_name=_("Extended feedback"),
        help=_("Show extended feedback when all attempts are used up?"),
        default=False,
        Scope=Scope.content
    )

    # Settings
    display_name = String(
        display_name=_("Title (display name)"),
        help=_("Title to display"),
        default=_("Step Builder"),
        scope=Scope.settings
    )

    # User state
    active_step = Integer(
        # Keep track of the student progress.
        default=0,
        scope=Scope.user_state,
        enforce_type=True
    )

    editable_fields = ('display_name', 'max_attempts', 'extended_feedback', 'weight')

    def build_user_state_data(self, context=None):
        user_state_data = super(MentoringWithExplicitStepsBlock, self).build_user_state_data()
        user_state_data['active_step'] = self.active_step_safe
        user_state_data['score_summary'] = self.get_score_summary()
        return user_state_data

    @lazy
    def question_ids(self):
        """
        Get the usage_ids of all of this XBlock's children that are "Questions".
        """
        return list(chain.from_iterable(self.runtime.get_block(step_id).step_ids for step_id in self.step_ids))

    @lazy
    def questions(self):
        """
        Get all questions associated with this block.
        """
        return [self.runtime.get_block(question_id) for question_id in self.question_ids]

    @property
    def active_step_safe(self):
        """
        Get self.active_step and double-check that it is a valid value.
        The stored value could be invalid if this block has been edited and new steps were
        added/deleted.
        """
        active_step = self.active_step
        if 0 <= active_step < len(self.step_ids):
            return active_step
        if active_step == -1 and self.has_review_step:
            return active_step  # -1 indicates the review step
        return 0

    def get_active_step(self):
        """ Get the active step as an instantiated XBlock """
        block = self.runtime.get_block(self.step_ids[self.active_step_safe])
        if block is None:
            log.error("Unable to load step builder step child %s", self.step_ids[self.active_step_safe])
        return block

    @lazy
    def step_ids(self):
        """
        Get the usage_ids of all of this XBlock's children that are steps.
        """
        from .step import MentoringStepBlock  # Import here to avoid circular dependency
        return [
            _normalize_id(child_id) for child_id in self.children if
            child_isinstance(self, child_id, MentoringStepBlock)
        ]

    @lazy
    def steps(self):
        """
        Get the step children of this block.
        """
        return [self.runtime.get_block(step_id) for step_id in self.step_ids]

    def get_question_number(self, question_name):
        question_names = [q.name for q in self.questions]
        return question_names.index(question_name) + 1

    def answer_mapper(self, answer_status):
        steps = self.steps
        answer_map = []
        for step in steps:
            for answer in step.student_results:
                if answer[1]['status'] == answer_status:
                    answer_map.append({
                        'id': answer[0],
                        'details': answer[1],
                        'step': step.step_number,
                        'number': self.get_question_number(answer[0]),
                    })
        return answer_map

    @property
    def has_review_step(self):
        return any(child_isinstance(self, child_id, ReviewStepBlock) for child_id in self.children)

    @property
    def review_step(self):
        """ Get the Review Step XBlock child, if any. Otherwise returns None """
        for step_id in self.children:
            if child_isinstance(self, step_id, ReviewStepBlock):
                return self.runtime.get_block(step_id)

    @property
    def score(self):
        questions = self.questions
        total_child_weight = sum(float(question.weight) for question in questions)
        if total_child_weight == 0:
            return Score(0, 0, [], [], [])
        steps = self.steps
        questions_map = {question.name: question for question in questions}
        points_earned = 0
        for step in steps:
            for question_name, question_results in step.student_results:
                question = questions_map.get(question_name)
                if question:  # Under what conditions would this evaluate to False?
                    points_earned += question_results['score'] * question.weight
        score = Decimal(points_earned) / Decimal(total_child_weight)
        correct = self.answer_mapper(CORRECT)
        incorrect = self.answer_mapper(INCORRECT)
        partially_correct = self.answer_mapper(PARTIAL)

        return Score(
            float(score),
            int((Decimal(score) * 100).quantize(Decimal('1.'), rounding=ROUND_HALF_UP)),
            correct,
            incorrect,
            partially_correct
        )

    @property
    def complete(self):
        return not self.score.incorrect and not self.score.partially_correct

    @property
    def review_tips(self):
        """ Get review tips, shown for wrong answers. """
        if self.max_attempts > 0 and self.num_attempts >= self.max_attempts:
            # Review tips are only shown if the student is allowed to try again.
            return []
        review_tips = []
        status_cache = dict()
        steps = self.steps
        for step in steps:
            status_cache.update(dict(step.student_results))
        for question in self.questions:
            result = status_cache.get(question.name)
            if result and result.get('status') != 'correct':
                # The student got this wrong. Check if there is a review tip to show.
                tip_html = question.get_review_tip()
                if tip_html:
                    if getattr(self.runtime, 'replace_jump_to_id_urls', None) is not None:
                        tip_html = self.runtime.replace_jump_to_id_urls(tip_html)
                    review_tips.append(tip_html)
        return review_tips

    def show_extended_feedback(self):
        return self.extended_feedback and self.max_attempts_reached

    @XBlock.supports("multi_device")  # Mark as mobile-friendly
    def student_view(self, context):
        fragment = Fragment()
        children_contents = []

        context = context or {}
        context['hide_prev_answer'] = True  # For Step Builder, we don't show the users' old answers when they try again
        context['score_summary'] = self.get_score_summary()
        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            if child is None:  # child should not be None but it can happen due to bugs or permission issues
                child_content = u"<p>[{}]</p>".format(self._(u"Error: Unable to load child component."))
            else:
                child_fragment = self._render_child_fragment(child, context, view='mentoring_view')
                fragment.add_frag_resources(child_fragment)
                child_content = child_fragment.content
            children_contents.append(child_content)

        fragment.add_content(loader.render_django_template('templates/html/mentoring_with_steps.html', {
            'self': self,
            'title': self.display_name,
            'show_title': self.show_title,
            'children_contents': children_contents,
        }, i18n_service=self.i18n_service))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/vendor/underscore-min.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/step_util.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/mentoring_with_steps.js'))

        fragment.add_resource(loader.load_unicode('templates/html/mentoring_attempts.underscore'), "text/html")
        fragment.initialize_js('MentoringWithStepsBlock', {
            'show_extended_feedback': self.show_extended_feedback(),
        })

        return fragment

    @property
    def allowed_nested_blocks(self):
        """
        Returns a list of allowed nested XBlocks. Each item can be either
        * An XBlock class
        * A NestedXBlockSpec

        If XBlock class is used it is assumed that this XBlock is enabled and allows multiple instances.
        NestedXBlockSpec allows explicitly setting disabled/enabled state, disabled reason (if any) and single/multiple
        instances
        """
        # Import here to avoid circular dependency
        from .step import MentoringStepBlock
        return [
            MentoringStepBlock,
            NestedXBlockSpec(ReviewStepBlock, single_instance=True),
        ]

    @XBlock.json_handler
    def submit(self, data, suffix=None):
        """
        Called when the user has submitted the answer[s] for the current step.
        """
        # First verify that active_step is correct:
        if data.get("active_step") != self.active_step_safe:
            raise JsonHandlerError(400, "Invalid Step. Refresh the page and try again.")

        # The step child will process the data:
        step_block = self.get_active_step()
        if not step_block:
            raise JsonHandlerError(500, "Unable to load the current step block.")
        response_data = step_block.submit(data)

        # Update the active step:
        new_value = self.active_step_safe + 1
        if new_value < len(self.step_ids):
            self.active_step = new_value
        elif new_value == len(self.step_ids):
            # The user just completed the final step.
            # Update the number of attempts:
            self.num_attempts += 1
            # Do we need to render a review (summary of the user's score):
            if self.has_review_step:
                self.active_step = -1
                response_data['review_html'] = self.runtime.render(self.review_step, "mentoring_view", {
                    'score_summary': self.get_score_summary(),
                }).content
            response_data['num_attempts'] = self.num_attempts
            # And publish the score:
            score = self.score
            grade_data = {
                'value': score.raw,
                'max_value': self.max_score(),
            }
            self.runtime.publish(self, 'grade', grade_data)

        response_data['active_step'] = self.active_step
        return response_data

    def get_score_summary(self):
        if self.num_attempts == 0:
            return {}
        score = self.score
        return {
            'score': score.percentage,
            'correct_answers': len(score.correct),
            'incorrect_answers': len(score.incorrect),
            'partially_correct_answers': len(score.partially_correct),
            'correct': score.correct,
            'incorrect': score.incorrect,
            'partial': score.partially_correct,
            'complete': self.complete,
            'max_attempts_reached': self.max_attempts_reached,
            'show_extended_review': self.show_extended_feedback(),
            'review_tips': self.review_tips,
        }

    @XBlock.json_handler
    def get_num_attempts(self, data, suffix):
        return {
            'num_attempts': self.num_attempts
        }

    @XBlock.json_handler
    def try_again(self, data, suffix=''):
        self.active_step = 0

        step_blocks = [self.runtime.get_block(child_id) for child_id in self.step_ids]

        for step in step_blocks:
            step.reset()

        return {
            'active_step': self.active_step
        }

    def author_preview_view(self, context):
        return self.student_view(context)

    def author_edit_view(self, context):
        """
        Add some HTML to the author view that allows authors to add child blocks.
        """
        fragment = super(MentoringWithExplicitStepsBlock, self).author_edit_view(context)
        fragment.add_content(loader.render_django_template('templates/html/mentoring_url_name.html', {
            "url_name": self.url_name
        }))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder.css'))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder-edit.css'))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder-tinymce-content.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/util.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/container_edit.js'))
        fragment.initialize_js('ProblemBuilderContainerEdit')
        return fragment

    def student_view_data(self, context=None):
        components = []

        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            if hasattr(child, 'student_view_data'):
                components.append(child.student_view_data(context))

        return {
            'title': self.display_name,
            'block_id': six.text_type(self.scope_ids.usage_id),
            'display_name': self.display_name,
            'show_title': self.show_title,
            'weight': self.weight,
            'extended_feedback': self.extended_feedback,
            'max_attempts': self.max_attempts,
            'components': components,
        }
