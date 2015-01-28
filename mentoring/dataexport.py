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

import json
import logging
import unicodecsv

from StringIO import StringIO
from webob import Response
from xblock.core import XBlock
from xblock.fields import String, Scope
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader

from .components import AnswerBlock

# Globals ###########################################################

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)

# Utils ###########################################################


def list2csv(row):
    """
    Convert a list to a CSV string (single row)
    """
    f = StringIO()
    writer = unicodecsv.writer(f, encoding='utf-8')
    writer.writerow(row)
    result = f.getvalue()
    f.close()
    return result


# Classes ###########################################################


class MentoringDataExportBlock(XBlock):
    """
    An XBlock allowing the instructor team to export all the student answers as a CSV file
    """
    display_name = String(help="Display name of the component", default="Mentoring Data Export",
                          scope=Scope.settings)

    def student_view(self, context):
        """
        Main view of the data export block
        """
        # Count how many 'Answer' blocks are in this course:
        num_answer_blocks = sum(1 for i in self._get_answer_blocks())
        html = loader.render_template('templates/html/dataexport.html', {
            'download_url': self.runtime.handler_url(self, 'download_csv'),
            'num_answer_blocks': num_answer_blocks,
        })
        return Fragment(html)

    @XBlock.handler
    def download_csv(self, request, suffix=''):
        response = Response(content_type='text/csv')
        response.app_iter = self.get_csv()
        response.content_disposition = 'attachment; filename=course_data.csv'
        return response

    def get_csv(self):
        """
        Download all student answers as a CSV.

        Columns are: student_id, [name of each answer block is a separate column]
        """
        answers_names = []  # List of the '.name' of each answer property
        student_answers = {}  # Dict of student ID: {answer_name: answer, ...}
        for answer_block in self._get_answer_blocks():
            answers_names.append(answer_block.name)
            student_data = self._get_students_data(answer_block)  # Tuples of (student ID, student input)
            for student_id, student_answer in student_data:
                if student_id not in student_answers:
                    student_answers[student_id] = {}
                student_answers[student_id][answer_block.name] = student_answer

        # Sort things:
        answers_names.sort()
        student_answers_sorted = list(student_answers.iteritems())
        student_answers_sorted.sort(key=lambda entry: entry[0])  # Sort by student ID

        # Header line
        yield list2csv([u'student_id'] + list(answers_names))

        if answers_names:
            for student_id, answers in student_answers_sorted:
                row = [student_id]
                for name in answers_names:
                    row.append(answers.get(name, u""))
                yield list2csv(row)

    def _get_students_data(self, answer_block):
        """
        Efficiently query for the answers entered by ALL students.
        (Note: The XBlock API only allows querying for the current
        student, so we have to use other APIs)

        Yields tuples of (student_id, student_answer)
        """
        usage_id = answer_block.scope_ids.usage_id
        # Check if we're in edX:
        try:
            from courseware.models import StudentModule
            usage_id = usage_id.for_branch(None).version_agnostic()
            entries = StudentModule.objects.filter(module_state_key=unicode(usage_id)).values('student_id', 'state')
            for entry in entries:
                state = json.loads(entry['state'])
                if 'student_input_raw' in state:
                    yield (entry['student_id'], state['student_input_raw'])
        except ImportError:
            pass
        # Check if we're in the XBlock SDK:
        try:
            from workbench.models import XBlockState
            rows = XBlockState.objects.filter(scope="usage", scope_id=usage_id).exclude(user_id=None)
            for entry in rows.values('user_id', 'state'):
                state = json.loads(entry['state'])
                if 'student_input_raw' in state:
                    yield (entry['user_id'], state['student_input_raw'])
        except ImportError:
            pass
        # Something else - return only the data
        # for the current user.
        yield (answer_block.scope_ids.user_id, answer_block.student_input_raw)

    def _get_answer_blocks(self):
        """
        Generator.
        Searches the tree of XBlocks that includes this data export block
        (i.e. search the current course)
        and returns all the AnswerBlock blocks that we can see.
        """
        root_block = self
        while root_block.parent:
            root_block = root_block.get_parent()

        block_ids_left = set([root_block.scope_ids.usage_id])

        while block_ids_left:
            block = self.runtime.get_block(block_ids_left.pop())
            if isinstance(block, AnswerBlock):
                yield block
            elif block.has_children:
                block_ids_left |= set(block.children)
