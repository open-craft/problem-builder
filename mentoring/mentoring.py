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

from lxml import etree
from StringIO import StringIO

from xblock.core import XBlock
from xblock.fields import Boolean, Scope, String, Integer, Float, List
from xblock.fragment import Fragment

from components import TitleBlock, SharedHeaderBlock, MentoringMessageBlock
from components.step import StepParentMixin, StepMixin

from xblockutils.resources import ResourceLoader

# Globals ###########################################################

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)

default_xml_content = loader.render_template('templates/xml/mentoring_default.xml', {})

# Classes ###########################################################

Score = namedtuple("Score", ["raw", "percentage", "correct", "incorrect", "partially_correct"])


class MentoringBlock(XBlock, StepParentMixin):
    """
    An XBlock providing mentoring capabilities

    Composed of text, answers input fields, and a set of MRQ/MCQ with advices.
    A set of conditions on the provided answers and MCQ/MRQ choices will determine if the
    student is a) provided mentoring advices and asked to alter his answer, or b) is given the
    ok to continue.
    """

    @staticmethod
    def is_default_xml_content(value):
        return value == default_xml_content

    # Content
    MENTORING_MODES = ('standard', 'assessment')
    mode = String(
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
        default='mentoring-default',  # TODO in future: set this to xblock.fields.UNIQUE_ID and remove self.url_name_with_default
        scope=Scope.content
    )
    enforce_dependency = Boolean(
        help="Should the next step be the current block to complete?",
        default=False,
        scope=Scope.content,
        enforce_type=True
    )
    display_submit = Boolean(help="Allow to submit current block?", default=True, scope=Scope.content)
    xml_content = String(help="XML content", default=default_xml_content, scope=Scope.content)

    # Settings
    weight = Float(
        help="Defines the maximum total grade of the block.",
        default=1,
        scope=Scope.settings,
        enforce_type=True
    )
    display_name = String(
        help="Display name of the component",
        default="Mentoring XBlock",
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

    icon_class = 'problem'
    has_score = True
    has_children = True

    FLOATING_BLOCKS = (TitleBlock, MentoringMessageBlock, SharedHeaderBlock)

    @property
    def is_assessment(self):
        return self.mode == 'assessment'

    @property
    def score(self):
        """Compute the student score taking into account the weight of each step."""
        weights = (float(self.runtime.get_block(step_id).weight) for step_id in self.steps)
        total_child_weight = sum(weights)
        if total_child_weight == 0:
            return (0, 0, 0, 0)
        score = sum(r[1]['score'] * r[1]['weight'] for r in self.student_results) / total_child_weight
        correct = sum(1 for r in self.student_results if r[1]['status'] == 'correct')
        incorrect = sum(1 for r in self.student_results if r[1]['status'] == 'incorrect')
        partially_correct = sum(1 for r in self.student_results if r[1]['status'] == 'partial')

        return Score(score, int(round(score * 100)), correct, incorrect, partially_correct)

    def student_view(self, context):
        # Migrate stored data if necessary
        self.migrate_fields()


        fragment = Fragment()
        title = u""
        header = u""
        child_content = u""

        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            if isinstance(child, TitleBlock):
                title = child.content
            elif isinstance(child, SharedHeaderBlock):
                header = child.render('mentoring_view', context).content
            elif isinstance(child, MentoringMessageBlock):
                pass  # TODO
            else:
                child_fragment = child.render('mentoring_view', context)
                fragment.add_frag_resources(child_fragment)
                child_content += child_fragment.content

        fragment.add_content(loader.render_template('templates/html/mentoring.html', {
            'self': self,
            'title': title,
            'header': header,
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
    def title(self):
        """
        Returns the title child.
        """
        for child in self.get_children_objects():
            if isinstance(child, TitleBlock):
                return child
        return None

    @property
    def header(self):
        """
        Return the header child.
        """
        for child in self.get_children_objects():
            if isinstance(child, SharedHeaderBlock):
                return child
        return None

    @property
    def has_missing_dependency(self):
        """
        Returns True if the student needs to complete another step before being able to complete
        the current one, and False otherwise
        """
        return self.enforce_dependency and (not self.completed) and (self.next_step != self.url_name_with_default)  # TODO: Fix

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
        children = [child for child in children if not isinstance(child, self.FLOATING_BLOCKS)]
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

    def studio_view(self, context):
        """
        Editing view in Studio
        """
        fragment = Fragment()
        fragment.add_content(loader.render_template('templates/html/mentoring_edit.html', {
            'self': self,
            'xml_content': self.xml_content,
        }))
        fragment.add_javascript_url(
            self.runtime.local_resource_url(self, 'public/js/mentoring_edit.js'))
        fragment.add_css_url(
            self.runtime.local_resource_url(self, 'public/css/mentoring_edit.css'))

        fragment.initialize_js('MentoringEditBlock')

        return fragment

    @XBlock.json_handler
    def studio_submit(self, submissions, suffix=''):
        log.info(u'Received studio submissions: {}'.format(submissions))

        success = True
        xml_content = submissions['xml_content']
        try:
            content = etree.parse(StringIO(xml_content))
        except etree.XMLSyntaxError as e:
            response = {
                'result': 'error',
                'message': e.message
            }
            success = False
        else:
            root = content.getroot()
            if 'mode' in root.attrib:
                if root.attrib['mode'] not in self.MENTORING_MODES:
                    response = {
                        'result': 'error',
                        'message': "Invalid mentoring mode: should be 'standard' or 'assessment'"
                    }
                    success = False
                elif root.attrib['mode'] == 'assessment' and 'max_attempts' not in root.attrib:
                    # assessment has a default of 2 max_attempts
                    root.attrib['max_attempts'] = '2'

            if success:
                response = {
                    'result': 'success',
                }
                self.xml_content = etree.tostring(content, pretty_print=True)

        log.debug(u'Response from Studio: {}'.format(response))
        return response

    @property
    def url_name_with_default(self):
        """
        Ensure the `url_name` is set to a unique, non-empty value.
        In future once hte pinned version of XBlock is updated,
        we can remove this and change the field to use the
        xblock.fields.UNIQUE_ID flag instead.
        """
        if self.url_name == 'mentoring-default':
            return self.scope_ids.usage_id
        else:
            return self.url_name

    @staticmethod
    def workbench_scenarios():
        """
        Scenarios displayed by the workbench. Load them from external (private) repository
        """
        return loader.load_scenarios_from_path('templates/xml')
