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

from xblock.core import XBlock
from xblock.fields import Boolean, Scope, String

from .light_children import XBlockWithLightChildren
from .message import MentoringMessageBlock
from .utils import get_scenarios_from_path, load_resource, render_template


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class MentoringBlock(XBlockWithLightChildren):
    """
    An XBlock providing mentoring capabilities

    Composed of text, answers input fields, and a set of multiple choice quizzes with advices. 
    A set of conditions on the provided answers and quizzes choices will determine if the
    student is a) provided mentoring advices and asked to alter his answer, or b) is given the
    ok to continue.
    """
    attempted = Boolean(help="Has the student attempted this mentoring step?",
                        default=False, scope=Scope.user_state)
    completed = Boolean(help="Has the student completed this mentoring step?",
                        default=False, scope=Scope.user_state)
    next_step = String(help="url_name of the next step the student must complete (global to all blocks)",
                       default='mentoring_first', scope=Scope.preferences)
    followed_by = String(help="url_name of the step after the current mentoring block in workflow",
                         default=None, scope=Scope.content)
    url_name = String(help="Name of the current step, used for URL building",
                      default='mentoring', scope=Scope.content)
    enforce_dependency = Boolean(help="Should the next step be the current block to complete?",
                                 default=True, scope=Scope.content)
    xml_content = String(help="XML content", default='', scope=Scope.content)
    has_children = True

    def student_view(self, context):
        log.warn('xml_content => {}'.format(self.xml_content)) 
        fragment, named_children = self.get_children_fragment(context, view_name='mentoring_view',
                                                              not_instance_of=MentoringMessageBlock)

        fragment.add_content(render_template('templates/html/mentoring.html', {
            'self': self,
            'named_children': named_children,
            'missing_dependency_url': self.has_missing_dependency and self.next_step_url,
        }))
        fragment.add_css(load_resource('static/css/mentoring.css'))
        fragment.add_javascript(load_resource('static/js/vendor/underscore-min.js'))
        fragment.add_javascript(load_resource('static/js/mentoring.js'))

        # TODO-LMS-WORKAROUND: Use self.runtime.resources_url() when supported
        fragment.add_resource(load_resource('templates/html/mentoring_progress.html').format(
                completed='/static/images/correct-icon.png'),
            "text/html")

        fragment.initialize_js('MentoringBlock')

        return fragment

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

    @XBlock.json_handler
    def submit(self, submissions, suffix=''):
        log.info(u'Received submissions: {}'.format(submissions))
        self.attempted = True

        submit_results = []
        completed = True
        for child in self.get_children_objects():
            if child.name and child.name in submissions:
                submission = submissions[child.name]
                child_result = child.submit(submission)
                submit_results.append([child.name, child_result])
                child.save()
                completed = completed and child_result['completed']

        if completed:
            message = self.get_message_html('completed')
        else:
            message = ''

        if self.has_missing_dependency:
            completed = False
            message = 'You need to complete all previous steps before being able to complete '+\
                      'the current one.'
        elif completed and self.next_step == self.url_name:
            self.next_step = self.followed_by

        self.completed = bool(completed)
        return {
            'submitResults': submit_results,
            'completed': self.completed,
            'message': message,
        }

    def get_message_fragment(self, message_type):
        for child in self.get_children_objects():
            if isinstance(child, MentoringMessageBlock) and child.type == message_type:
                return self.render_child(child, 'mentoring_view', {})

    def get_message_html(self, message_type):
        fragment = self.get_message_fragment(message_type)
        if fragment:
            return fragment.body_html()
        else:
            return ''

    @staticmethod
    def workbench_scenarios():
        """
        Scenarios displayed by the workbench. Load them from external (private) repository
        """
        return get_scenarios_from_path('templates/xml')
