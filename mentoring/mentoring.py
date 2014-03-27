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
import uuid

from lxml import etree
from StringIO import StringIO

from xblock.core import XBlock
from xblock.fields import Boolean, Scope, String
from xblock.fragment import Fragment

from .light_children import XBlockWithLightChildren
from .message import MentoringMessageBlock
from .utils import get_scenarios_from_path, load_resource, render_template


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class MentoringBlock(XBlockWithLightChildren):
    """
    An XBlock providing mentoring capabilities

    Composed of text, answers input fields, and a set of MRQ/MCQ with advices.
    A set of conditions on the provided answers and MCQ/MRQ choices will determine if the
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
                      default='mentoring-default', scope=Scope.content)
    enforce_dependency = Boolean(help="Should the next step be the current block to complete?",
                                 default=False, scope=Scope.content)
    display_submit = Boolean(help="Allow to submit current block?", default=True, scope=Scope.content)
    xml_content = String(help="XML content", default='', scope=Scope.content)
    icon_class = 'problem'

    def student_view(self, context):
        fragment, named_children = self.get_children_fragment(context, view_name='mentoring_view',
                                                              not_instance_of=MentoringMessageBlock)

        fragment.add_content(render_template('templates/html/mentoring.html', {
            'self': self,
            'named_children': named_children,
            'missing_dependency_url': self.has_missing_dependency and self.next_step_url,
        }))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/mentoring.css'))
        fragment.add_javascript_url(
                    self.runtime.local_resource_url(self, 'public/js/vendor/underscore-min.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/mentoring.js'))
        fragment.add_resource(load_resource('templates/html/mentoring_progress.html'), "text/html")
        fragment.add_resource(load_resource('templates/html/mrqblock_attempts.html'), "text/html")

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

        # Once it has been completed once, keep completion even if user changes values
        if self.completed:
            completed = True

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
            'attempted': self.attempted,
            'message': message,
        }

    def get_message_fragment(self, message_type):
        for child in self.get_children_objects():
            if isinstance(child, MentoringMessageBlock) and child.type == message_type:
                frag = self.render_child(child, 'mentoring_view', {})
                return self.fragment_text_rewriting(frag)

    def get_message_html(self, message_type):
        fragment = self.get_message_fragment(message_type)
        if fragment:
            return fragment.body_html()
        else:
            return ''

    def studio_view(self, context):
        """
        Editing view in Studio
        """
        fragment = Fragment()
        fragment.add_content(render_template('templates/html/mentoring_edit.html', {
            'self': self,
            'xml_content': self.xml_content or self.default_xml_content,
        }))
        fragment.add_javascript(load_resource('public/js/mentoring_edit.js'))
        fragment.add_css(load_resource('public/css/mentoring_edit.css'))

        fragment.initialize_js('MentoringEditBlock')

        return fragment

    @XBlock.json_handler
    def studio_submit(self, submissions, suffix=''):
        log.info(u'Received studio submissions: {}'.format(submissions))

        xml_content = submissions['xml_content']
        try:
            xml = etree.parse(StringIO(xml_content))
            root = xml.getroot()
            self.url_name = root.attrib['url_name']
        except etree.XMLSyntaxError as e:
            response = {
                'result': 'error',
                'message': e.message
            }
        except KeyError as e:
            response = {
                'result': 'error',
                'message': 'mentoring "url_name" attribute is missing'
            }
        else:
            response = {
                'result': 'success',
            }
            self.xml_content = xml_content

        log.debug(u'Response from Studio: {}'.format(response))
        return response

    @property
    def default_xml_content(self):
        return render_template('templates/xml/mentoring_default.xml', {
            'self': self,
            'url_name': self.url_name_with_default,
        })

    @property
    def url_name_with_default(self):
        """
        Ensure the `url_name` is set to a unique, non-empty value.
        This should ideally be handled by Studio, but we need to declare the attribute
        to be able to use it from the workbench, and when this happen Studio doesn't set
        a unique default value - this property gives either the set value, or if none is set
        a randomized default value
        """
        if self.url_name == 'mentoring-default':
            return 'mentoring-{}'.format(uuid.uuid4())
        else:
            return self.url_name

    @staticmethod
    def workbench_scenarios():
        """
        Scenarios displayed by the workbench. Load them from external (private) repository
        """
        return get_scenarios_from_path('templates/xml')
