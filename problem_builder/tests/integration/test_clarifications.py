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
"""
Test that <span class="pb-clarification"> elements are transformed into LMS-like tooltips.
"""

from cgi import escape

# Imports ###########################################################
import ddt
from xblockutils.base_test import SeleniumXBlockTest

# Classes ###########################################################


@ddt.ddt
class ClarificationTest(SeleniumXBlockTest):
    """
    Test that the content of span.pb-clarification elements is transformed into
    tooltip elements.
    """

    clarification_text = 'Let me clarify...'

    mcq_template = """
        <problem-builder>
            <pb-mcq question="Who was your favorite character? {clarify_escaped}">
                <pb-choice value="gaius">Gaius Baltar</pb-choice>
                <pb-choice value="adama">Admiral William Adama {clarify}</pb-choice>
                <pb-choice value="starbuck">Starbuck</pb-choice>
            </pb-mcq>
        </problem-builder>
    """

    mrq_template = """
        <problem-builder>
            <pb-mrq question="What makes a great {clarify_escaped} MRQ {clarify_escaped}?">
                <pb-choice value="1">Lots of choices</pb-choice>
                <pb-choice value="2">Funny{clarify} choices</pb-choice>
                <pb-choice value="3">Not sure {clarify}</pb-choice>
            </pb-mrq>
        </problem-builder>
    """

    rating_template = """
        <problem-builder>
            <pb-rating name="rating_1_1" question="How do you rate {clarify_escaped} Battlestar Galactica?">
                <pb-choice value="6">More than 5 stars {clarify}</pb-choice>
            </pb-rating>
        </problem-builder>
    """

    long_answer_template = """
        <problem-builder>
            <pb-answer question="What did you think {clarify_escaped} of the ending?" />
        </problem-builder>
    """

    html_block_template = """
        <problem-builder>
            <html_demo><p>This is some raw {clarify} HTML code.</p></html_demo>
        </problem-builder>
    """

    def prepare_xml_scenario(self, xml_template):
        span = '<span class="pb-clarification">{}</span>'.format(self.clarification_text)
        escaped_span = escape(span, quote=True)
        return xml_template.format(
            clarify=span,
            clarify_escaped=escaped_span
        )

    @ddt.data(
        (mcq_template, 2),
        (mrq_template, 4),
        (rating_template, 2),
        (long_answer_template, 1),
        (html_block_template, 1),
    )
    @ddt.unpack
    def test_title(self, xml_template, tooltip_count):
        self.set_scenario_xml(self.prepare_xml_scenario(xml_template))
        pb_element = self.go_to_view()
        clarifications = pb_element.find_elements_by_css_selector('span.pb-clarification')

        self.assertEqual(len(clarifications), tooltip_count)

        for clarification in clarifications:
            tooltip = clarification.find_element_by_css_selector('i[data-tooltip]')
            self.assertEqual(tooltip.get_attribute('data-tooltip'), self.clarification_text)

            sr = clarification.find_element_by_css_selector('span.sr')
            self.assertEqual(sr.text, self.clarification_text)
