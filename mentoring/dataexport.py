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
import unicodecsv

from itertools import groupby
from StringIO import StringIO
from webob import Response
from xblock.core import XBlock
from xblock.fields import String, Scope
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader

from .components.answer import AnswerBlock, Answer

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
        course_id = getattr(self.runtime, "course_id", "all")
        answers = Answer.objects.filter(course_id=course_id).order_by('student_id', 'name')
        answers_names = answers.values_list('name', flat=True).distinct().order_by('name')

        # Header line
        yield list2csv([u'student_id'] + list(answers_names))

        if answers_names:
            for _, student_answers in groupby(answers, lambda x: x.student_id):
                row = []
                next_answer_idx = 0
                for answer in student_answers:
                    if not row:
                        row = [answer.student_id]

                    while answer.name != answers_names[next_answer_idx]:
                        # Still add answer row to CSV when they don't exist in DB
                        row.append('')
                        next_answer_idx += 1

                    row.append(answer.student_input)
                    next_answer_idx += 1

                if row:
                    yield list2csv(row)

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
