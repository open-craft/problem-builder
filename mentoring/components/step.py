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

class StepParentMixin(object):
    """
    An XBlock mixin for a parent block containing Step children
    """

    @property
    def steps(self):
        """
        Generator returning the usage_id for all of this XBlock's 
        children that are "Steps"
        """
        step_ids = []
        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            if isinstance(child, StepMixin):
                step_ids.append(child_id)
        return step_ids


class StepMixin(object):
    """
    An XBlock mixin for a child block that is a "Step"
    """
    @property
    def step_number(self):
        return list(self.get_parent().steps).index(self.scope_ids.usage_id) + 1

    @property
    def lonely_step(self):
        if self.scope_ids.usage_id not in self.get_parent().steps:
            raise ValueError("Step's parent should contain Step", self, self.get_parent().steps)
        return len(self.get_parent().steps) == 1
