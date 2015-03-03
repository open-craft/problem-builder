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

from .models import Answer

from xblock.core import XBlock
from xblock.fields import Scope, Float, Integer, String
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin
from .step import StepMixin
import uuid


# Globals ###########################################################

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)

# Classes ###########################################################


class AnswerMixin(object):
    """
    Mixin to give an XBlock the ability to read/write data to the Answers DB table.
    """
    def _get_course_id(self):
        """ Get a course ID if available """
        return getattr(self.runtime, 'course_id', 'all')

    def _get_student_id(self):
        """ Get student anonymous ID or normal ID """
        try:
            return self.runtime.anonymous_student_id
        except AttributeError:
            return self.scope_ids.user_id

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

    def validate_field_data(self, validation, data):
        """
        Validate this block's field data.
        """
        super(AnswerMixin, self).validate_field_data(validation, data)

        def add_error(msg):
            validation.add(ValidationMessage(ValidationMessage.ERROR, msg))

        if not data.name:
            add_error(u"A Question ID is required.")


class AnswerBlock(AnswerMixin, StepMixin, StudioEditableXBlockMixin, XBlock):
    """
    A field where the student enters an answer

    Must be included as a child of a mentoring block. Answers are persisted as django model instances
    to make them searchable and referenceable across xblocks.
    """
    name = String(
        display_name="Question ID (name)",
        help="The ID of this block. Should be unique unless you want the answer to be used in multiple places.",
        default="",
        scope=Scope.content
    )
    default_from = String(
        display_name="Default From",
        help="If a question ID is specified, get the default value from this answer.",
        default=None,
        scope=Scope.content
    )
    min_characters = Integer(
        display_name="Min. Allowed Characters",
        help="Minimum number of characters allowed for the answer",
        default=0,
        scope=Scope.content
    )
    question = String(
        display_name="Question",
        help="Question to ask the student",
        scope=Scope.content,
        default=""
    )
    weight = Float(
        display_name="Weight",
        help="Defines the maximum total grade of the answer block.",
        default=1,
        scope=Scope.settings,
        enforce_type=True
    )

    editable_fields = ('question', 'name', 'min_characters', 'weight', 'default_from')

    @property
    def studio_display_name(self):
        return u"Question {}".format(self.step_number) if not self.lonely_step else u"Question"

    def __getattribute__(self, name):
        """ Provide a read-only display name without adding a display_name field to the class. """
        if name == "display_name":
            return self.studio_display_name
        return super(AnswerBlock, self).__getattribute__(name)

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

    def fallback_view(self, view_name, context=None):
        context = context or {}
        context['self'] = self
        html = loader.render_template('templates/html/answer_editable.html', context)

        fragment = Fragment(html)
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/answer.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/answer.js'))
        fragment.initialize_js('AnswerBlock')
        return fragment

    def submit(self, submission):
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

        return 'correct' if answer_length_ok else 'incorrect'

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
            if answer_data.student_input != self.student_input:
                answer_data.student_input = self.student_input
                answer_data.save()

    @classmethod
    def get_template(cls, template_id):
        """
        Used to interact with Studio's create_xblock method to instantiate pre-defined templates.
        """
        # Generate a random 'name' value
        if template_id == 'studio_default':
            return {'data': {'name': uuid.uuid4().hex[:7]}}
        return {'metadata': {}, 'data': {}}


class AnswerRecapBlock(AnswerMixin, StudioEditableXBlockMixin, XBlock):
    """
    A block that displays an answer previously entered by the student (read-only).
    """
    name = String(
        display_name="Question ID",
        help="The ID of the question for which to display the student's answer.",
        scope=Scope.content,
    )
    display_name = String(
        display_name="Title",
        help="Title of this answer recap section",
        scope=Scope.content,
        default="",
    )
    description = String(
        help="Description of this answer (optional). Can include HTML.",
        scope=Scope.content,
        default="",
        display_name="Description",
    )
    editable_fields = ('name', 'display_name', 'description')

    @property
    def student_input(self):
        if self.name:
            return self.get_model_object().student_input
        return ''

    def fallback_view(self, view_name, context=None):
        context = context or {}
        context['title'] = self.display_name
        context['description'] = self.description
        context['student_input'] = self.student_input
        html = loader.render_template('templates/html/answer_read_only.html', context)

        fragment = Fragment(html)
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/answer.css'))
        return fragment
