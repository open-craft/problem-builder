# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Harvard, edX & OpenCraft
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

import os
import sys
from setuptools import setup, find_packages
from setuptools.command.install import install


# Constants #########################################################

VERSION = '3.4.0'

# Functions #########################################################

def package_data(pkg, root_list):
    """Generic function to find package_data for `pkg` under `root`."""
    data = []
    for root in root_list:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


class VerifyTagCommand(install):
    """Custom command to verify that the git tag matches the current version."""
    description = 'verify that the git tag matches the current version'

    def run(self):
        tag = os.getenv('CIRCLE_TAG')

        if tag != 'v{}'.format(VERSION):
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                tag, VERSION
            )
            sys.exit(info)


# Main ##############################################################

BLOCKS = [
    'problem-builder = problem_builder.mentoring:MentoringBlock',
    'step-builder = problem_builder.mentoring:MentoringWithExplicitStepsBlock',
    'sb-step = problem_builder.step:MentoringStepBlock',
    'sb-review-step = problem_builder.step_review:ReviewStepBlock',
    'sb-conditional-message = problem_builder.step_review:ConditionalMessageBlock',
    'sb-review-score = problem_builder.step_review:ScoreSummaryBlock',
    'sb-review-per-question-feedback = problem_builder.step_review:PerQuestionFeedbackBlock',

    'sb-plot = problem_builder.plot:PlotBlock',
    'sb-plot-overlay = problem_builder.plot:PlotOverlayBlock',

    'pb-table = problem_builder.table:MentoringTableBlock',
    'pb-column = problem_builder.table:MentoringTableColumn',
    'pb-answer = problem_builder.answer:AnswerBlock',
    'pb-answer-recap = problem_builder.answer:AnswerRecapBlock',
    'pb-mcq = problem_builder.mcq:MCQBlock',
    'pb-swipe = problem_builder.swipe:SwipeBlock',
    'pb-rating = problem_builder.mcq:RatingBlock',
    'pb-mrq = problem_builder.mrq:MRQBlock',
    'pb-slider = problem_builder.slider:SliderBlock',
    'pb-completion = problem_builder.completion:CompletionBlock',
    'pb-message = problem_builder.message:MentoringMessageBlock',
    'pb-tip = problem_builder.tip:TipBlock',
    'pb-choice = problem_builder.choice:ChoiceBlock',

    'pb-dashboard = problem_builder.dashboard:DashboardBlock',
    'pb-data-export = problem_builder.instructor_tool:InstructorToolBlock',  # Deprecated; use 'pb-instructor-tool' now
    'pb-instructor-tool = problem_builder.instructor_tool:InstructorToolBlock',
]

setup(
    name='xblock-problem-builder',
    version=VERSION,
    description='XBlock - Problem Builder',
    packages=find_packages(),
    install_requires=[
        'XBlock>=1.2',
        'xblock-utils',
    ],
    entry_points={
        'xblock.v1': BLOCKS,
    },
    package_data=package_data("problem_builder", ["templates", "public", "migrations", "locale"]),
    cmdclass={
        'verify_tag': VerifyTagCommand,
    },
)
