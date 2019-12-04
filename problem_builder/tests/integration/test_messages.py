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
import ddt

from .base_test import ProblemBuilderBaseTest

COMPLETED, INCOMPLETE, MAX_REACHED = "completed", "incomplete", "max_attempts_reached"
MESSAGES = {
    COMPLETED: u"Great job! (completed message)",
    INCOMPLETE: u"Not quite! You can try again, though. (incomplete message)",
    MAX_REACHED: (
        u"Sorry, you have used up all of your allowed submissions. (max_attempts_reached message)"
    ),
}


@ddt.ddt
class MessagesTest(ProblemBuilderBaseTest):
    """
    Test the various types of message that can be added to a problem.
    """
    def expect_message(self, msg_type, mentoring):
        """
        Assert that the message of the specified type is shown to the user.
        """
        messages_element = mentoring.find_element_by_css_selector('.messages')
        if msg_type is None:
            self.assertFalse(messages_element.is_displayed())
        else:
            self.assertTrue(messages_element.is_displayed())
            message_text = messages_element.text.strip()
            self.assertTrue(message_text.startswith("FEEDBACK"))
            message_text = message_text[8:].lstrip()
            self.assertEqual(MESSAGES[msg_type], message_text)

    @ddt.data(
        ("One", COMPLETED),
        ("Two", COMPLETED),
        ("I don't understand", MAX_REACHED),
    )
    @ddt.unpack
    def test_one_shot(self, choice_text, expected_message_type):
        """
        Test a question that has max_attempts set to 1
        """
        mentoring = self.load_scenario("messages.xml", {"max_attempts": 1})
        self.expect_message(None, mentoring)
        self.click_choice(mentoring, choice_text)
        self.click_submit(mentoring)
        self.expect_message(expected_message_type, mentoring)

    @ddt.data(
        (2, "One", COMPLETED),
        (2, "I don't understand", MAX_REACHED),
        (0, "I don't understand", INCOMPLETE),
        (10, "I don't understand", INCOMPLETE),
    )
    @ddt.unpack
    def test_retry(self, max_attempts, choice_text, expected_message_type):
        """
        Test submitting a wrong answer, seeing a message, then submitting another answer.
        In each case, max_attempts is not 1.
        """
        mentoring = self.load_scenario("messages.xml", {"max_attempts": max_attempts})
        # First, there should be no message.
        self.expect_message(None, mentoring)
        # Let's get the question wrong:
        self.click_choice(mentoring, "I don't understand")
        self.click_submit(mentoring)
        # We should now see the INCOMPLETE message:
        self.expect_message(INCOMPLETE, mentoring)

        # Now, answer as directed and expect the given message:
        self.click_choice(mentoring, "One")  # Make sure we change our choice so we will be able to submit
        self.click_choice(mentoring, choice_text)
        self.click_submit(mentoring)
        self.expect_message(expected_message_type, mentoring)
