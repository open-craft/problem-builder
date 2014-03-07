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
    'mentoring = mentoring:MentoringBlock',
    'mentoring-dataexport = mentoring:MentoringDataExportBlock',
]

BLOCKS_CHILDREN = [
    'mentoring-table = mentoring:MentoringTableBlock',
    'column = mentoring:MentoringTableColumnBlock',
    'header = mentoring:MentoringTableColumnHeaderBlock',
    'answer = mentoring:AnswerBlock',
    'quizz = mentoring:QuizzBlock',
    'message = mentoring:MentoringMessageBlock',
    'tip = mentoring:QuizzTipBlock',
    'choice = mentoring:QuizzChoiceBlock',
    'html = mentoring:HTMLBlock',
]

setup(
    name='xblock-mentoring',
    version='0.1',
    description='XBlock - Mentoring',
    packages=['mentoring', 'mentoring.migrations'],
    install_requires=[
        'XBlock',
    ],
    entry_points={
        'xblock.v1': BLOCKS,
        'xblock.light_children': BLOCKS_CHILDREN,
    },
    package_data=package_data("mentoring", ["static", "templates", "public"]),
)
