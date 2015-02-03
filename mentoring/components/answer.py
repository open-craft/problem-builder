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
from lazy import lazy

from mentoring.models import Answer

from xblock.core import XBlock
from xblock.fields import Scope, Boolean, Float, Integer, String
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader
from .step import StepMixin


# Globals ###########################################################

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)

# Classes ###########################################################


class AnswerBlock(XBlock, StepMixin):
    """
    A field where the student enters an answer

    Must be included as a child of a mentoring block. Answers are persisted as django model instances
    to make them searchable and referenceable across xblocks.
    """
    name = String(
        help="The ID of this block. Should be unique unless you want the answer to be used in multiple places.",
        default="",
        scope=Scope.content
    )
    read_only = Boolean(
        help="Display as a read-only field",
        default=False,
        scope=Scope.content
    )
    default_from = String(
        help="If specified, get the default value from this answer.",
        default=None,
        scope=Scope.content
    )
    min_characters = Integer(
        help="Minimum number of characters allowed for the answer",
        default=0,
        scope=Scope.content
    )
    question = String(
        help="Question to ask the student",
        scope=Scope.content,
        default=""
    )
    weight = Float(
        help="Defines the maximum total grade of the answer block.",
        default=1,
        scope=Scope.settings,
        enforce_type=True
    )

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        block = runtime.construct_xblock_from_class(cls, keys)

        # Load XBlock properties from the XML attributes:
        for name, value in node.items():
            setattr(block, name, value)

        for xml_child in node:
            if xml_child.tag == 'question':
                block.question = xml_child.text
            else:
                block.runtime.add_node_as_child(block, xml_child, id_generator)

        return block

    def _get_course_id(self):
        """ Get a course ID if available """
        return getattr(self.runtime, 'course_id', 'all')

    def _get_student_id(self):
        """ Get student anonymous ID or normal ID """
        try:
            return self.runtime.anonymous_student_id
        except AttributeError:
            return self.scope_ids.user_id

    @lazy
    def student_input(self):
        """
        The student input value, or a default which may come from another block.
        Read from a Django model, since XBlock API doesn't yet support course-scoped
        fields or generating instructor reports across many student responses.
        """
        # Only attempt to locate a model object for this block when the answer has a name
        if not self.name:
            return ''

        student_input = self.get_model_object().student_input

        # Default value can be set from another answer's current value
        if not student_input and self.default_from:
            student_input = self.get_model_object(name=self.default_from).student_input

        return student_input

    def mentoring_view(self, context=None):
        if not self.read_only:
            html = loader.render_template('templates/html/answer_editable.html', {
                'self': self,
            })
        else:
            html = loader.render_template('templates/html/answer_read_only.html', {
                'self': self,
            })

        fragment = Fragment(html)
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/answer.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/answer.js'))
        fragment.initialize_js('AnswerBlock')
        return fragment

    def mentoring_table_view(self, context=None):
        html = loader.render_template('templates/html/answer_table.html', {
            'self': self,
        })
        fragment = Fragment(html)
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/answer_table.css'))
        return fragment

    def submit(self, submission):
        if not self.read_only:
            self.student_input = submission[0]['value'].strip()
            self.save()
            log.info(u'Answer submitted for`{}`: "{}"'.format(self.name, self.student_input))
        return {
            'student_input': self.student_input,
            'status': self.status,
            'weight': self.weight,
            'score': 1 if self.status == 'correct' else 0,
        }

    @property
    def status(self):
        answer_length_ok = self.student_input
        if self.min_characters > 0:
            answer_length_ok = len(self.student_input.strip()) >= self.min_characters

        return 'correct' if (self.read_only or answer_length_ok) else 'incorrect'

    @property
    def completed(self):
        return self.status == 'correct'

    def save(self):
        """
        Replicate data changes on the related Django model used for sharing of data accross XBlocks
        """
        super(AnswerBlock, self).save()

        student_id = self._get_student_id()
        if not student_id:
            return  # save() gets called from the workbench homepage sometimes when there is no student ID

        # Only attempt to locate a model object for this block when the answer has a name
        if self.name:
            answer_data = self.get_model_object()
            if answer_data.student_input != self.student_input and not self.read_only:
                answer_data.student_input = self.student_input
                answer_data.save()

    def get_model_object(self, name=None):
        """
        Fetches the Answer model object for the answer named `name`
        """
        # By default, get the model object for the current answer's name
        if not name:
            name = self.name
        # Consistency check - we should have a name by now
        if not name:
            raise ValueError('AnswerBlock.name field need to be set to a non-null/empty value')

        student_id = self._get_student_id()
        course_id = self._get_course_id()

        answer_data, _ = Answer.objects.get_or_create(
            student_id=student_id,
            course_id=course_id,
            name=name,
        )
        return answer_data
