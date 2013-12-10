"""Tests for the mentoring module"""

# Imports ###########################################################

from workbench.test.selenium_test import SeleniumTest


# Classes ###########################################################

class MentoringBlockTest(SeleniumTest):

    def setUp(self):
        super(MentoringBlockTest, self).setUp()

        # Suzy opens the browser to visit the workbench
        self.browser.get(self.live_server_url)

        # She knows it's the site by the header
        header1 = self.browser.find_element_by_css_selector('h1')
        self.assertEqual(header1.text, 'XBlock scenarios')

    def test_TODO_NAME(self):
        link = self.browser.find_element_by_link_text('001) Pre-goal brainstom')
        link.click()
