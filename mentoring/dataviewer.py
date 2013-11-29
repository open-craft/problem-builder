# -*- coding: utf-8 -*-

# Imports ###########################################################

import logging
import json

from webob import Response
from xblock.core import XBlock
from xblock.fragment import Fragment

from .models import Answer
from .utils import load_resource, render_template


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class MentoringDataViewerBlock(XBlock):
    """
    An XBlock allowing the instructor team to read/export all the student answers
    """

    def student_view(self, context):
        html = render_template('templates/html/dataviewer.html', {
            'self': self,
        })

        fragment = Fragment(html)
        fragment.add_javascript(load_resource('static/js/vendor/jquery.handsontable.full.js'))
        fragment.add_javascript(load_resource('static/js/dataviewer.js'))
        fragment.add_css(load_resource('static/css/vendor/jquery.handsontable.full.css'))
        fragment.add_css(load_resource('static/css/dataviewer.css'))

        fragment.initialize_js('MentoringDataViewerBlock')

        return fragment

    def studio_view(self, context):
        return Fragment(u'Studio view body')

    @XBlock.handler
    def get_data(self, request, suffix=''):
        response_json = json.dumps({'data': self.get_data_list()})
        return Response(response_json, content_type='application/json')

    def get_data_list(self):
        answers = Answer.objects.all().order_by('student_id', 'name')
        answers_names = Answer.objects.values_list('name', flat=True).distinct().order_by('name')

        data = [['student_id'] + list(answers_names)]
        row = []
        cur_student_id = None
        cur_col = None
        for answer in answers:
            if answer.student_id != cur_student_id:
                if row:
                    data.append(row)
                row = [answer.student_id]
                cur_student_id = answer.student_id
                cur_col = 0
            while answer.name != answers_names[cur_col]:
                row.append('')
                cur_col += 1
            row.append(answer.student_input)
            cur_col += 1
        if row:
            data.append(row)

        return data

    @staticmethod
    def workbench_scenarios():
        """
        Sample scenarios which will be displayed in the workbench
        """
        return [
            ("Mentoring - Page 999, Intructors data viewer",
                                    load_resource('templates/xml/999_dataviewer.xml')),
        ]
