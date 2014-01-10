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

from webob import Response
from xblock.core import XBlock
from xblock.fragment import Fragment

from .models import Answer
from .utils import load_resource, list2csv, render_template


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class MentoringDataExportBlock(XBlock):
    """
    An XBlock allowing the instructor team to export all the student answers as a CSV file
    """

    def student_view(self, context):
        html = render_template('templates/html/dataexport.html', {
            'self': self,
        })

        fragment = Fragment(html)
        fragment.add_javascript(load_resource('static/js/dataexport.js'))
        fragment.add_css(load_resource('static/css/dataexport.css'))

        fragment.initialize_js('MentoringDataExportBlock')

        return fragment

    def studio_view(self, context):
        return Fragment(u'Studio view body')

    @XBlock.handler
    def download_csv(self, request, suffix=''):
        response = Response(content_type='text/csv')
        response.app_iter = self.get_csv()
        response.content_disposition = 'attachment; filename=course_data.csv'
        return response

    def get_csv(self):
        answers = Answer.objects.all().order_by('student_id', 'name')
        answers_names = Answer.objects.values_list('name', flat=True).distinct().order_by('name')

        # Header line
        yield list2csv([u'student_id'] + list(answers_names))

        row = []
        cur_student_id = None
        cur_col = None
        for answer in answers:
            if answer.student_id != cur_student_id:
                if row:
                    yield list2csv(row)
                row = [answer.student_id]
                cur_student_id = answer.student_id
                cur_col = 0
            while answer.name != answers_names[cur_col]:
                row.append('')
                cur_col += 1
            row.append(answer.student_input)
            cur_col += 1
        if row:
            yield list2csv(row)
