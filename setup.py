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

    'mentoring-table = mentoring.components:MentoringTableBlock',
    'column = mentoring.components:MentoringTableColumnBlock',
    'header = mentoring.components:MentoringTableColumnHeaderBlock',
    'answer = mentoring.components:AnswerBlock',
    'quizz = mentoring.components:MCQBlock',
    'mcq = mentoring.components:MCQBlock',
    'mrq = mentoring.components:MRQBlock',
    'message = mentoring.components:MentoringMessageBlock',
    'tip = mentoring.components:TipBlock',
    'choice = mentoring.components:ChoiceBlock',
    'html = mentoring.components:HTMLBlock',
    'title = mentoring.components:TitleBlock',
    'shared-header = mentoring.components:SharedHeaderBlock',
]

setup(
    name='xblock-mentoring',
    version='0.1',
    description='XBlock - Mentoring',
    packages=['mentoring'],
    install_requires=[
        'XBlock',
        'xblock-utils',
    ],
    dependency_links = ['http://github.com/edx-solutions/xblock-utils/tarball/master#egg=xblock-utils'],
    entry_points={
        'xblock.v1': BLOCKS,
    },
    package_data=package_data("mentoring", ["components", "templates", "public", "migrations"]),
)
