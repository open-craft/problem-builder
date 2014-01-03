
# Imports ###########################################################

from mentoring.test_base import MentoringBaseTest


# Classes ###########################################################

class MentoringTableBlockTest(MentoringBaseTest):

    def test_mentoring_table(self):
        # Initially, the table should be blank, with just the titles
        table = self.go_to_page('Table 2', css_selector='.mentoring-table')
        headers = table.find_elements_by_css_selector('th')
        self.assertEqual(len(headers), 2)
        self.assertEqual(headers[0].text, 'Header Test 1')
        self.assertEqual(headers[1].text, 'Header Test 2')

        rows = table.find_elements_by_css_selector('td')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].text, '')
        self.assertEqual(rows[1].text, '')

        # Fill the answers - they should appear in the table
        mentoring = self.go_to_page('Table 1')
        answers = mentoring.find_elements_by_css_selector('textarea')
        answers[0].send_keys('This is the answer #1')
        answers[1].send_keys('This is the answer #2')
        submit = mentoring.find_element_by_css_selector('input.submit')
        submit.click()

        table = self.go_to_page('Table 2', css_selector='.mentoring-table')
        rows = table.find_elements_by_css_selector('td')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].text, 'This is the answer #1')
        self.assertEqual(rows[1].text, 'This is the answer #2')

