# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Harvard
#
# Authors:
#          Xavier Antoviaque <xavier@antoviaque.org>
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

from collections import namedtuple

from xblock.core import XBlock
from xblock.exceptions import NoSuchViewError
from xblock.fields import Boolean, Scope, String, Integer, Float, List
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage

from components import MentoringMessageBlock
from components.step import StepParentMixin, StepMixin

from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin, StudioContainerXBlockMixin

# Globals ###########################################################

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)

# Classes ###########################################################

Score = namedtuple("Score", ["raw", "percentage", "correct", "incorrect", "partially_correct"])


@XBlock.needs("i18n")
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
        display_name="Mode",
        help="Mode of the mentoring. 'standard' or 'assessment'",
        default='standard',
        scope=Scope.content,
        values=MENTORING_MODES
    )
    followed_by = String(
        help="url_name of the step after the current mentoring block in workflow.",
        default=None,
        scope=Scope.content
    )
    max_attempts = Integer(
        help="Number of max attempts for this questions",
        default=0,
        scope=Scope.content,
        enforce_type=True
    )
    url_name = String(
        help="Name of the current step, used for URL building",
        default='mentoring-default',
        scope=Scope.content
        # TODO in future: set this field's default to xblock.fields.UNIQUE_ID
        # and remove self.url_name_with_default. Waiting until UNIQUE_ID support
        # is available in edx-platform's pinned version of xblock. (See XBlock PR 249)
    )
    enforce_dependency = Boolean(
        help="Should the next step be the current block to complete?",
        default=False,
        scope=Scope.content,
        enforce_type=True
    )
    display_submit = Boolean(
        help="Allow submission of the current block?",
        default=True,
        scope=Scope.content,
        enforce_type=True
    )
    xml_content = String(
        help="Not used for version 2. This field is here only to preserve the data needed to upgrade from v1 to v2.",
        display_name="XML content",
        default='',
        scope=Scope.content,
        multiline_editor=True
    )

    # Settings
    weight = Float(
        help="Defines the maximum total grade of the block.",
        default=1,
        scope=Scope.settings,
        enforce_type=True
    )
    display_name = String(
        help="Title to display",
        default="Mentoring Questions",
        scope=Scope.settings
    )

    # User state
    attempted = Boolean(
        help="Has the student attempted this mentoring step?",
        default=False,
        scope=Scope.user_state
    )
    completed = Boolean(
        help="Has the student completed this mentoring step?",
        default=False,
        scope=Scope.user_state
    )
    num_attempts = Integer(
        help="Number of attempts a user has answered for this questions",
        default=0,
        scope=Scope.user_state,
        enforce_type=True
    )
    step = Integer(
        help="Keep track of the student assessment progress.",
        default=0,
        scope=Scope.user_state,
        enforce_type=True
    )
    student_results = List(
        help="Store results of student choices.",
        default=[],
        scope=Scope.user_state
    )

    # Global user state
    next_step = String(
        help="url_name of the next step the student must complete (global to all blocks)",
        default='mentoring_first',
        scope=Scope.preferences
    )

    editable_fields = (
        'mode', 'followed_by', 'max_attempts', 'enforce_dependency',
        'display_submit', 'weight', 'display_name',
    )
    icon_class = 'problem'
    has_score = True
    has_children = True

    def _(self, text):
        """ translate text """
        return self.runtime.service(self, "i18n").ugettext(text)

    @property
    def is_assessment(self):
        return self.mode == 'assessment'

    @property
    def score(self):
        """Compute the student score taking into account the weight of each step."""
        weights = (float(self.runtime.get_block(step_id).weight) for step_id in self.steps)
        total_child_weight = sum(weights)
        if total_child_weight == 0:
            return Score(0, 0, 0, 0, 0)
        score = sum(r[1]['score'] * r[1]['weight'] for r in self.student_results) / total_child_weight
        correct = sum(1 for r in self.student_results if r[1]['status'] == 'correct')
        incorrect = sum(1 for r in self.student_results if r[1]['status'] == 'incorrect')
        partially_correct = sum(1 for r in self.student_results if r[1]['status'] == 'partial')

        return Score(score, int(round(score * 100)), correct, incorrect, partially_correct)

    def student_view(self, context):
        # Migrate stored data if necessary
        self.migrate_fields()

        fragment = Fragment()
        child_content = u""

        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            if isinstance(child, MentoringMessageBlock):
                pass  # TODO
            else:
                child_fragment = child.render('mentoring_view', context)
                fragment.add_frag_resources(child_fragment)
                child_content += child_fragment.content

        fragment.add_content(loader.render_template('templates/html/mentoring.html', {
            'self': self,
            'title': self.display_name,
            'child_content': child_content,
            'missing_dependency_url': self.has_missing_dependency and self.next_step_url,
        }))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/mentoring.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/vendor/underscore-min.js'))
        js_file = 'public/js/mentoring_{}_view.js'.format('assessment' if self.is_assessment else 'standard')
        fragment.add_javascript_url(self.runtime.local_resource_url(self, js_file))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/mentoring.js'))
        fragment.add_resource(loader.load_unicode('templates/html/mentoring_attempts.html'), "text/html")
        fragment.add_resource(loader.load_unicode('templates/html/mentoring_grade.html'), "text/html")

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
            'component_id': self.url_name_with_default,
        }

    @property
    def has_missing_dependency(self):
        """
        Returns True if the student needs to complete another step before being able to complete
        the current one, and False otherwise
        """
        return self.enforce_dependency and (not self.completed) and (self.next_step != self.url_name_with_default)

    @property
    def next_step_url(self):
        """
        Returns the URL of the next step's page
        """
        return '/jump_to_id/{}'.format(self.next_step)

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

    @XBlock.json_handler
    def submit(self, submissions, suffix=''):
        log.info(u'Received submissions: {}'.format(submissions))
        self.attempted = True

        if self.is_assessment:
            return self.handleAssessmentSubmit(submissions, suffix)

        submit_results = []
        completed = True
        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            if child.name and child.name in submissions:
                submission = submissions[child.name]
                child_result = child.submit(submission)
                submit_results.append([child.name, child_result])
                child.save()
                completed = completed and (child_result['status'] == 'correct')

        if self.max_attempts_reached:
            message = self.get_message_html('max_attempts_reached')
        elif completed:
            message = self.get_message_html('completed')
        else:
            message = self.get_message_html('incomplete')

        # Once it has been completed once, keep completion even if user changes values
        if self.completed:
            completed = True

        # server-side check to not set completion if the max_attempts is reached
        if self.max_attempts_reached:
            completed = False

        if self.has_missing_dependency:
            completed = False
            message = 'You need to complete all previous steps before being able to complete the current one.'
        elif completed and self.next_step == self.url_name_with_default:
            self.next_step = self.followed_by

        # Once it was completed, lock score
        if not self.completed:
            # save user score and results
            while self.student_results:
                self.student_results.pop()
            for result in submit_results:
                self.student_results.append(result)

            self.runtime.publish(self, 'grade', {
                'value': self.score.raw,
                'max_value': 1,
            })

        if not self.completed and self.max_attempts > 0:
            self.num_attempts += 1

        self.completed = completed is True

        raw_score = self.score.raw

        self.runtime.publish(self, 'xblock.mentoring.submitted', {
            'num_attempts': self.num_attempts,
            'submitted_answer': submissions,
            'grade': raw_score,
        })

        return {
            'submitResults': submit_results,
            'completed': self.completed,
            'attempted': self.attempted,
            'message': message,
            'max_attempts': self.max_attempts,
            'num_attempts': self.num_attempts
        }

    def handleAssessmentSubmit(self, submissions, suffix):

        completed = False
        current_child = None
        children = [self.runtime.get_block(child_id) for child_id in self.children]
        children = [child for child in children if not isinstance(child, MentoringMessageBlock)]
        steps = [child for child in children if isinstance(child, StepMixin)]  # Faster than the self.steps property

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
            if not self.max_attempts_reached:
                self.runtime.publish(self, 'grade', {
                    'value': score.raw,
                    'max_value': 1,
                    'score_type': 'proficiency',
                })
                event_data['final_grade'] = score.raw

            self.num_attempts += 1
            self.completed = True

        event_data['exercise_id'] = current_child.name
        event_data['num_attempts'] = self.num_attempts
        event_data['submitted_answer'] = submissions

        self.runtime.publish(self, 'xblock.mentoring.assessment.submitted', event_data)

        return {
            'completed': completed,
            'attempted': self.attempted,
            'max_attempts': self.max_attempts,
            'num_attempts': self.num_attempts,
            'step': self.step,
            'score': score.percentage,
            'correct_answer': score.correct,
            'incorrect_answer': score.incorrect,
            'partially_correct_answer': score.partially_correct,
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

    def clean_studio_edits(self, data):
        """
        Given POST data dictionary 'data', clean the data before validating it.
        e.g. fix capitalization, remove trailing spaces, etc.
        """
        if data.get('mode') == 'assessment' and 'max_attempts' not in data:
            # assessment has a default of 2 max_attempts
            data['max_attempts'] = 2

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
                        self._(u"There should only be one '{}' message component.".format(msg_type))
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
        return fragment

    def author_edit_view(self, context):
        """
        Add some HTML to the author view that allows authors to add child blocks.
        """
        fragment = super(MentoringBlock, self).author_edit_view(context)
        fragment.add_content(loader.render_template('templates/html/mentoring_add_buttons.html', {}))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/mentoring_edit.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/mentoring_edit.js'))
        fragment.initialize_js('MentoringEditComponents')
        return fragment

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        To avoid collisions with e.g. the existing <html> XBlock in edx-platform,
        we prefix all of the mentoring block tags with "mentoring-". However,
        using that prefix in the XML is optional. This method adds that prefix
        in when parsing XML in a mentoring context.
        """
        PREFIX_TAGS = ("answer", "answer-recap", "quizz", "mcq", "mrq", "rating", "message", "tip", "choice", "column")
        for element in node.iter():
            # We have prefixed all our XBlock entry points with "mentoring-". But using the "mentoring-"
            # prefix in the XML is optional:
            if element.tag in PREFIX_TAGS:
                element.tag = "mentoring-{}".format(element.tag)
        return super(MentoringBlock, cls).parse_xml(node, runtime, keys, id_generator)

    @staticmethod
    def workbench_scenarios():
        """
        Scenarios displayed by the workbench. Load them from external (private) repository
        """
        return loader.load_scenarios_from_path('templates/xml')
