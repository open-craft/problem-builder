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

import time

from workbench import scenarios
from workbench.test.selenium_test import SeleniumTest

from .utils import load_scenarios_from_path


# Classes ###########################################################

class MentoringBaseTest(SeleniumTest):

    def setUp(self):
        super(MentoringBaseTest, self).setUp()

        # Use test scenarios
        self.browser.get(self.live_server_url) # Needed to load tests once
        scenarios.SCENARIOS.clear()
        scenarios_list = load_scenarios_from_path('../tests/xml')
        for identifier, title, xml in scenarios_list:
            scenarios.add_xml_scenario(identifier, title, xml)
            self.addCleanup(scenarios.remove_scenario, identifier)

        # Suzy opens the browser to visit the workbench
        self.browser.get(self.live_server_url)

        # She knows it's the site by the header
        header1 = self.browser.find_element_by_css_selector('h1')
        self.assertEqual(header1.text, 'XBlock scenarios')

    def go_to_page(self, page_name, css_selector='div.mentoring'):
        """
        Navigate to the page `page_name`, as listed on the workbench home
        Returns the DOM element on the visited page located by the `css_selector`
        """
        self.browser.get(self.live_server_url)
        self.browser.find_element_by_link_text(page_name).click()
        time.sleep(1)
        mentoring = self.browser.find_element_by_css_selector(css_selector)
        return mentoring

