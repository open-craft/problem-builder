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

from xblock.fields import String
from xblockutils.base_test import SeleniumBaseTest

# Studio adds a url_name property to each XBlock but Workbench doesn't.
# Since we rely on it, we need to mock url_name support so it can be set via XML and
# accessed like a normal field.
from mentoring import MentoringBlock
MentoringBlock.url_name = String()


class MentoringBaseTest(SeleniumBaseTest):
    module_name = __name__
    default_css_selector = 'div.mentoring'
