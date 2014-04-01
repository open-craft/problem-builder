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


from .light_children import Scope, String
from .questionnaire import QuestionnaireAbstractBlock
from .utils import render_template


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class MCQBlock(QuestionnaireAbstractBlock):
    """
    An XBlock used to ask multiple-choice questions
    """
    type = String(help="Type of MCQ", scope=Scope.content, default="choices")
    student_choice = String(help="Last input submitted by the student", default="", scope=Scope.user_state)
    low = String(help="Label for low ratings", scope=Scope.content, default="Less")
    high = String(help="Label for high ratings", scope=Scope.content, default="More")

    valid_types = ('rating', 'choices')

    def submit(self, submission):
        log.debug(u'Received MCQ submission: "%s"', submission)

        completed = True
        tips_fragments = []
        for tip in self.get_tips():
            completed = completed and self.is_tip_completed(tip, submission)
            if submission in tip.display_with_defaults:
                tips_fragments.append(tip.render())

        if self.type == 'rating':
            formatted_tips = render_template('templates/html/tip_question_group.html', {
                'self': self,
                'tips_fragments': tips_fragments,
                'submission': submission,
                'submission_display': self.get_submission_display(submission),
            })
        else:
            formatted_tips = render_template('templates/html/tip_choice_group.html', {
                'self': self,
                'tips_fragments': tips_fragments,
                'completed': completed,
            })

        self.student_choice = submission
        result = {
            'type': self.type,
            'submission': submission,
            'completed': completed,
            'tips': formatted_tips,
        }
        log.debug(u'MCQ submission result: %s', result)
        return result

    def is_tip_completed(self, tip, submission):
        if not submission:
            return False

        if submission in tip.reject_with_defaults:
            return False

        return True
