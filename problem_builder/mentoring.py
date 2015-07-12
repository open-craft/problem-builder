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

import logging
import json

from collections import namedtuple

from xblock.core import XBlock
from xblock.exceptions import NoSuchViewError, JsonHandlerError
from xblock.fields import Boolean, Scope, String, Integer, Float, List
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage

from .message import MentoringMessageBlock
from .step import StepParentMixin, StepMixin

from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin, StudioContainerXBlockMixin

try:
    # Used to detect if we're in the workbench so we can add Font Awesome
    from workbench.runtime import WorkbenchRuntime
except ImportError:
    WorkbenchRuntime = False

# Globals ###########################################################

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)

_default_theme_config = {
    'package': 'problem_builder',
    'locations': ['public/themes/lms.css']
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
class MentoringBlock(XBlock, StepParentMixin, StudioEditableXBlockMixin, StudioContainerXBlockMixin):
    """
    An XBlock providing mentoring capabilities

    Composed of text, answers input fields, and a set of MRQ/MCQ with advices.
    A set of conditions on the provided answers and MCQ/MRQ choices will determine if the
    student is a) provided mentoring advices and asked to alter his answer, or b) is given the
    ok to continue.
    """
    # Content
    MENTORING_MODES = ('standard', 'assessment')
    mode = String(
        display_name=_("Mode"),
        help=_("Mode of the mentoring. 'standard' or 'assessment'"),
        default='standard',
        scope=Scope.content,
        values=MENTORING_MODES
    )
    followed_by = String(
        display_name=_("Followed by"),
        help=_("url_name of the step after the current mentoring block in workflow."),
        default=None,
        scope=Scope.content
    )
    max_attempts = Integer(
        display_name=_("Max. Attempts Allowed"),
        help=_("Number of max attempts allowed for this questions"),
        default=0,
        scope=Scope.content,
        enforce_type=True
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
    show_title = Boolean(
        display_name=_("Show title"),
        help=_("Display the title?"),
        default=True,
        scope=Scope.content
    )

    # Settings
    weight = Float(
        display_name=_("Weight"),
        help=_("Defines the maximum total grade of the block."),
        default=1,
        scope=Scope.settings,
        enforce_type=True
    )
    display_name = String(
        display_name=_("Title (Display name)"),
        help=_("Title to display"),
        default=_("Mentoring Questions"),
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
    num_attempts = Integer(
        # Number of attempts a user has answered for this questions
        default=0,
        scope=Scope.user_state,
        enforce_type=True
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
        'display_name', 'mode', 'followed_by', 'max_attempts', 'enforce_dependency',
        'display_submit', 'feedback_label', 'weight', 'extended_feedback'
    )
    icon_class = 'problem'
    has_score = True
    has_children = True

    block_settings_key = 'mentoring'
    theme_key = 'theme'

    def _(self, text):
        """ translate text """
        return self.runtime.service(self, "i18n").ugettext(text)

    @property
    def is_assessment(self):
        """ Checks if mentoring XBlock is in assessment mode """
        return self.mode == 'assessment'

    def get_theme(self):
        """
        Gets theme settings from settings service. Falls back to default (LMS) theme
        if settings service is not available, xblock theme settings are not set or does
        contain mentoring theme settings.
        """
        settings_service = self.runtime.service(self, "settings")
        if settings_service:
            xblock_settings = settings_service.get_settings_bucket(self)
            if xblock_settings and self.theme_key in xblock_settings:
                return xblock_settings[self.theme_key]
        return _default_theme_config

    def get_question_number(self, question_id):
        """
        Get the step number of the question id
        """
        for child_id in self.children:
            question = self.runtime.get_block(child_id)
            if isinstance(question, StepMixin) and (question.name == question_id):
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
        steps = [self.runtime.get_block(step_id) for step_id in self.steps]
        steps_map = {q.name: q for q in steps}
        total_child_weight = sum(float(step.weight) for step in steps)
        if total_child_weight == 0:
            return Score(0, 0, [], [], [])
        points_earned = 0
        for q_name, q_details in self.student_results:
            question = steps_map.get(q_name)
            if question:
                points_earned += q_details['score'] * question.weight
        score = points_earned / total_child_weight
        correct = self.answer_mapper(CORRECT)
        incorrect = self.answer_mapper(INCORRECT)
        partially_correct = self.answer_mapper(PARTIAL)

        return Score(score, int(round(score * 100)), correct, incorrect, partially_correct)

    def include_theme_files(self, fragment):
        theme = self.get_theme()
        theme_package, theme_files = theme['package'], theme['locations']
        for theme_file in theme_files:
            fragment.add_css(ResourceLoader(theme_package).load_unicode(theme_file))

    def student_view(self, context):
        # Migrate stored data if necessary
        self.migrate_fields()

        # Validate self.step:
        num_steps = len(self.steps)
        if self.step > num_steps:
            self.step = num_steps

        fragment = Fragment()
        child_content = u""

        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            if not isinstance(child, MentoringMessageBlock):
                try:
                    if self.is_assessment and isinstance(child, StepMixin):
                        child_fragment = child.render('assessment_step_view', context)
                    else:
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

        fragment.add_content(loader.render_template('templates/html/mentoring.html', {
            'self': self,
            'title': self.display_name,
            'show_title': self.show_title,
            'child_content': child_content,
            'missing_dependency_url': self.has_missing_dependency and self.next_step_url,
        }))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder.css'))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/mentoring.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/vendor/underscore-min.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/problem_builder.js'))
        js_file = 'public/js/mentoring_{}_view.js'.format('assessment' if self.is_assessment else 'standard')
        fragment.add_javascript_url(self.runtime.local_resource_url(self, js_file))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/mentoring.js'))
        fragment.add_resource(loader.load_unicode('templates/html/mentoring_attempts.html'), "text/html")
        fragment.add_resource(loader.load_unicode('templates/html/mentoring_grade.html'), "text/html")
        fragment.add_resource(loader.load_unicode('templates/html/mentoring_review_questions.html'), "text/html")

        self.include_theme_files(fragment)
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
    def url_name(self):
        """
        Get the url_name for this block. In Studio/LMS it is provided by a mixin, so we just
        defer to super(). In the workbench or any other platform, we use the usage_id.
        """
        try:
            return super(MentoringBlock, self).url_name
        except AttributeError:
            return unicode(self.scope_ids.usage_id)

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
        self.runtime.publish(self, event_type, data)

        return {'result': 'ok'}

    def get_message(self, completed):
        """
        Get the message to display to a student following a submission in normal mode.
        """
        if completed:
            # Student has achieved a perfect score
            return self.get_message_html('completed')
        elif self.max_attempts_reached:
            # Student has not achieved a perfect score and cannot try again
            return self.get_message_html('max_attempts_reached')
        else:
            # Student did not achieve a perfect score but can try again:
            return self.get_message_html('incomplete')

    @property
    def assessment_message(self):
        """
        Get the message to display to a student following a submission in assessment mode.
        """
        if not self.max_attempts_reached:
            return self.get_message_html('on-assessment-review')
        else:
            return None

    def show_extended_feedback(self):
        return self.extended_feedback and self.max_attempts_reached

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
    def get_results(self, queries, suffix=''):
        """
        Gets detailed results in the case of extended feedback.

        Right now there are two ways to get results-- through the template upon loading up
        the mentoring block, or after submission of an AJAX request like in
        submit or get_results here.
        """
        if self.mode == 'standard':
            results, completed, show_message = self._get_standard_results()
            mentoring_completed = completed
        else:
            if not self.show_extended_feedback():
                return {
                    'results': [],
                    'error': 'Extended feedback results cannot be obtained.'
                }

            results, completed, show_message = self._get_assessment_results(queries)
            mentoring_completed = True

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
        show_message = bool(self.student_results)

        # In standard mode, all children is visible simultaneously, so need collecting responses from all of them
        for child_id in self.steps:
            child = self.runtime.get_block(child_id)
            child_result = child.get_last_result()
            results.append([child.name, child_result])
            completed = completed and (child_result.get('status', None) == 'correct')

        return results, completed, show_message

    def _get_assessment_results(self, queries):
        """
        Gets detailed results in the case of extended feedback.

        It may be a good idea to eventually have this function get results
        in the general case instead of loading them in the template in the future,
        and only using it for extended feedback situations.

        Right now there are two ways to get results-- through the template upon loading up
        the mentoring block, or after submission of an AJAX request like in
        submit or get_results here.
        """
        results = []
        completed = True
        choices = dict(self.student_results)
        # Only one child should ever be of concern with this method.
        for child_id in self.steps:
            child = self.runtime.get_block(child_id)
            if child.name and child.name in queries:
                results = [child.name, child.get_results(choices[child.name])]
                # Children may have their own definition of 'completed' which can vary from the general case
                # of the whole mentoring block being completed. This is because in standard mode, all children
                # must be correct to complete the block. In assessment mode with extended feedback, completion
                # happens when you're out of attempts, no matter how you did.
                completed = choices[child.name]['status']
                break

        return results, completed, True

    @XBlock.json_handler
    def submit(self, submissions, suffix=''):
        log.info(u'Received submissions: {}'.format(submissions))
        # server-side check that the user is allowed to submit:
        if self.max_attempts_reached:
            raise JsonHandlerError(403, "Maximum number of attempts already reached.")
        elif self.has_missing_dependency:
            raise JsonHandlerError(
                403,
                "You need to complete all previous steps before being able to complete the current one."
            )

        # This has now been attempted:
        self.attempted = True

        if self.is_assessment:
            return self.handle_assessment_submit(submissions, suffix)

        submit_results = []
        previously_completed = self.completed
        completed = True
        for child_id in self.steps:
            child = self.runtime.get_block(child_id)
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
                'max_value': 1,
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

    def handle_assessment_submit(self, submissions, suffix):
        completed = False
        current_child = None
        children = [self.runtime.get_block(child_id) for child_id in self.children]
        children = [child for child in children if not isinstance(child, MentoringMessageBlock)]
        steps = [child for child in children if isinstance(child, StepMixin)]  # Faster than the self.steps property
        assessment_message = None

        for child in children:
            if child.name and child.name in submissions:
                submission = submissions[child.name]

                # Assessment mode doesn't allow to modify answers
                # This will get the student back at the step he should be
                current_child = child
                step = steps.index(child)
                if self.step > step or self.max_attempts_reached:
                    step = self.step
                    completed = False
                    break

                self.step = step + 1

                child_result = child.submit(submission)
                if 'tips' in child_result:
                    del child_result['tips']
                self.student_results.append([child.name, child_result])
                completed = child_result['status']

        event_data = {}

        score = self.score

        if current_child == steps[-1]:
            log.info(u'Last assessment step submitted: {}'.format(submissions))
            self.runtime.publish(self, 'grade', {
                'value': score.raw,
                'max_value': 1,
                'score_type': 'proficiency',
            })
            event_data['final_grade'] = score.raw
            assessment_message = self.assessment_message

            self.num_attempts += 1
            self.completed = True

        event_data['exercise_id'] = current_child.name
        event_data['num_attempts'] = self.num_attempts
        event_data['submitted_answer'] = submissions

        self.runtime.publish(self, 'xblock.problem_builder.assessment.submitted', event_data)

        return {
            'completed': completed,
            'max_attempts': self.max_attempts,
            'num_attempts': self.num_attempts,
            'step': self.step,
            'score': score.percentage,
            'correct_answer': len(score.correct),
            'incorrect_answer': len(score.incorrect),
            'partially_correct_answer': len(score.partially_correct),
            'correct': self.correct_json(stringify=False),
            'incorrect': self.incorrect_json(stringify=False),
            'partial': self.partial_json(stringify=False),
            'extended_feedback': self.show_extended_feedback() or '',
            'assessment_message': assessment_message,
        }

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

    @property
    def max_attempts_reached(self):
        return self.max_attempts > 0 and self.num_attempts >= self.max_attempts

    def get_message_html(self, message_type):
        html = u""
        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            if isinstance(child, MentoringMessageBlock) and child.type == message_type:
                html += child.render('mentoring_view', {}).content  # TODO: frament_text_rewriting ?
        return html

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

    def author_preview_view(self, context):
        """
        Child blocks can override this to add a custom preview shown to authors in Studio when
        not editing this block's children.
        """
        fragment = self.student_view(context)
        fragment.add_content(loader.render_template('templates/html/mentoring_url_name.html', {
            "url_name": self.url_name
        }))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/mentoring_edit.css'))
        self.include_theme_files(fragment)
        return fragment

    def author_edit_view(self, context):
        """
        Add some HTML to the author view that allows authors to add child blocks.
        """
        fragment = Fragment(u'<div class="mentoring">')  # This DIV is needed for CSS to apply to the previews
        self.render_children(context, fragment, can_reorder=True, can_add=False)
        fragment.add_content(u'</div>')
        fragment.add_content(loader.render_template('templates/html/mentoring_add_buttons.html', {}))
        fragment.add_content(loader.render_template('templates/html/mentoring_url_name.html', {
            "url_name": self.url_name
        }))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder.css'))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/mentoring_edit.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/problem_builder.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/mentoring_edit.js'))
        fragment.initialize_js('MentoringEditComponents')
        return fragment

    def get_content_titles(self):
        """
        By default, each Sequential block in a course ("Subsection" in Studio parlance) will
        display the display_name of each descendant in a tooltip above the content. We don't
        want that - we only want to display the mentoring block as a whole as one item.
        Otherwise things like "Choice (yes) (Correct)" will appear in the tooltip.
        """
        return [self.display_name]

    @staticmethod
    def workbench_scenarios():
        """
        Scenarios displayed by the workbench. Load them from external (private) repository
        """
        return loader.load_scenarios_from_path('templates/xml')
