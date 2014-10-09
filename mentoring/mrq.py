# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 edX
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


from .light_children import List, Scope, Boolean
from .questionnaire import QuestionnaireAbstractBlock
from .utils import loader


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class MRQBlock(QuestionnaireAbstractBlock):
    """
    An XBlock used to ask multiple-response questions
    """
    student_choices = List(help="Last submissions by the student", default=[], scope=Scope.user_state)
    hide_results = Boolean(help="Hide results", scope=Scope.content, default=False)

    def submit(self, submissions):
        log.debug(u'Received MRQ submissions: "%s"', submissions)

        score = 0

        results = []
        for choice in self.custom_choices:
            choice_completed = True
            choice_tips_fragments = []
            choice_selected = choice.value in submissions
            for tip in self.get_tips():
                if choice.value in tip.display_with_defaults:
                    choice_tips_fragments.append(tip.render())

                if ((not choice_selected and choice.value in tip.require_with_defaults) or
                        (choice_selected and choice.value in tip.reject_with_defaults)):
                    choice_completed = False

            if choice_completed:
                score += 1

            choice_result = {
                'value': choice.value,
                'selected': choice_selected,
            }
            # Only include tips/results in returned response if we want to display them
            if not self.hide_results:
                choice_result['completed'] = choice_completed
                choice_result['tips'] = loader.render_template('templates/html/tip_choice_group.html', {
                    'self': self,
                    'tips_fragments': choice_tips_fragments,
                    'completed': choice_completed,
                })

            results.append(choice_result)

        self.student_choices = submissions

        status = 'incorrect' if score <= 0 else 'correct' if score >= len(results) else 'partial'

        result = {
            'submissions': submissions,
            'status': status,
            'choices': results,
            'message': self.message,
            'weight': self.weight,
            'score': float(score) / len(results),
        }

        log.debug(u'MRQ submissions result: %s', result)
        return result
