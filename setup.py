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
from setuptools import setup


# Functions #########################################################

def package_data(pkg, root_list):
    """Generic function to find package_data for `pkg` under `root`."""
    data = []
    for root in root_list:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


# Main ##############################################################

BLOCKS = [
    'problem-builder = problem_builder:MentoringBlock',

    'pb-table = problem_builder:MentoringTableBlock',
    'pb-column = problem_builder:MentoringTableColumn',
    'pb-answer = problem_builder:AnswerBlock',
    'pb-answer-recap = problem_builder:AnswerRecapBlock',
    'pb-mcq = problem_builder:MCQBlock',
    'pb-rating = problem_builder:RatingBlock',
    'pb-mrq = problem_builder:MRQBlock',
    'pb-message = problem_builder:MentoringMessageBlock',
    'pb-tip = problem_builder:TipBlock',
    'pb-choice = problem_builder:ChoiceBlock',

    'pb-dashboard = problem_builder:DashboardBlock',
    # Deprecated. You can temporarily uncomment and run 'python setup.py develop' if you have these blocks
    # installed from testing mentoring v2 and need to get past an error message.
    #'mentoring = problem_builder:MentoringBlock',  # Deprecated alias for problem-builder
    #'answer = problem_builder:AnswerBlock',
    #'mentoring-answer = problem_builder:AnswerBlock',
    #'answer-recap = problem_builder:AnswerRecapBlock',
    #'mentoring-answer-recap = problem_builder:AnswerRecapBlock',
    #'mcq = problem_builder:MCQBlock',
    #'mentoring-mcq = problem_builder:MCQBlock',
    #'rating = problem_builder:RatingBlock',
    #'mentoring-rating = problem_builder:RatingBlock',
    #'mrq = problem_builder:MRQBlock',
    #'mentoring-mrq = problem_builder:MRQBlock',
    #'tip = problem_builder:TipBlock',
    #'mentoring-tip = problem_builder:TipBlock',
    #'choice = problem_builder:ChoiceBlock',
    #'mentoring-choice = problem_builder:ChoiceBlock',
]

setup(
    name='xblock-problem-builder',
    version='2.0',
    description='XBlock - Problem Builder',
    packages=['problem_builder', 'problem_builder.v1'],
    install_requires=[
        'XBlock',
        'xblock-utils',
    ],
    entry_points={
        'xblock.v1': BLOCKS,
    },
    package_data=package_data("problem_builder", ["templates", "public", "migrations"]),
)
