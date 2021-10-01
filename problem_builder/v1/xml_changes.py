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
Each class in this file represents a change made to the XML schema between v1 and v2.
"""
import json
import warnings

from lxml import etree


class Change:
    @staticmethod
    def applies_to(node):
        """
        Does this change affect the given XML node?
        n.b. prior Changes will already be applied to the node.
        """
        raise NotImplementedError

    def __init__(self, node):
        """
        Prepare to upgrade 'node' at some point in the future
        """
        self.node = node

    def apply(self):
        raise NotImplementedError


class RenameMentoringTag(Change):
    """
    Replace <mentoring> with <problem-builder>
    """
    @staticmethod
    def applies_to(node):
        return node.tag == "mentoring"

    def apply(self):
        self.node.tag = "problem-builder"


class PrefixTags(Change):
    """ Most old elements now get a pb- prefix """
    @staticmethod
    def applies_to(node):
        return node.tag in ("tip", "choice", "answer", "mcq", "mrq", "rating", "column", "message")

    def apply(self):
        self.node.tag = "pb-" + self.node.tag


class HideTitle(Change):
    """
    If no <title> element is present, set hide_title="true"
    """
    @staticmethod
    def applies_to(node):
        return node.tag == "problem-builder" and node.find("title") is None

    def apply(self):
        self.node.attrib["show_title"] = "false"


class RemoveTitle(Change):
    """ The old <title> element is now an attribute of <problem-builder> """
    @staticmethod
    def applies_to(node):
        return node.tag == "title" and node.getparent().tag == "problem-builder"

    def apply(self):
        title = self.node.text.strip() if self.node.text else ''
        p = self.node.getparent()
        old_display_name = p.get("display_name")
        if old_display_name and old_display_name != title:
            warnings.warn(
                f'Replacing display_name="{p.attrib["display_name"]}" with <title> value "{title}"'
            )
        p.attrib["display_name"] = title
        p.remove(self.node)


class UnwrapHTML(Change):
    """ <pb-choice>,<pb-tip>, <header>, and <pb-message> now contain HTML without an explicit <html> wrapper. """
    @staticmethod
    def applies_to(node):
        return node.tag == "html" and node.getparent().tag in ("pb-choice", "pb-tip", "pb-message", "header")

    def apply(self):
        p = self.node.getparent()
        if self.node.text:
            p.text = (p.text if p.text else "") + self.node.text
        index = list(p).index(self.node)
        for child in list(self.node):
            index += 1
            p.insert(index, child)
        p.remove(self.node)


class RenameTableTag(Change):
    """
    Replace <mentoring-table> with <pb-table>
    """
    @staticmethod
    def applies_to(node):
        return node.tag == "mentoring-table"

    def apply(self):
        self.node.tag = "pb-table"


class TableColumnHeader(Change):
    """
    Replace:
    <pb-table>
         <pb-column>
             <header>Answer 1</header>
             <answer name="answer_1" />
         </pb-column>
    </pb-table>
    with
    <pb-table>
         <pb-column header="Answer 1">
             <answer-recap name="answer_1" />
         </pb-column>
    </pb-table>
    """
    @staticmethod
    def applies_to(node):
        return node.tag == "pb-column" and node.getparent().tag == "pb-table"

    def apply(self):
        header_html = ""
        to_remove = []
        for child in list(self.node):
            if child.tag == "header":
                if child.text:
                    header_html += child.text
                for grandchild in list(child):
                    header_html += etree.tostring(grandchild).decode('utf-8')
                to_remove.append(child)
            elif child.tag == "pb-answer":
                child.tag = "pb-answer-recap"
                if "read_only" in child.attrib:
                    del child.attrib["read_only"]
            elif child.tag != "html":
                warnings.warn(f"Invalid <pb-column> element: Unexpected <{child.tag}>")
                return
        for child in to_remove:
            self.node.remove(child)
        self.node.text = None
        if header_html:
            self.node.attrib["header"] = header_html


class QuizzToMCQ(Change):
    """ <quizz> element was an alias for <mcq>. In v2 we only have <pb-mcq> """
    @staticmethod
    def applies_to(node):
        return node.tag == "quizz"

    def apply(self):
        self.node.tag = "pb-mcq"


class MCQToRating(Change):
    """ <mcq type="rating"> is now just <rating>, and we never use type="choices" on MCQ/MRQ """
    @staticmethod
    def applies_to(node):
        return node.tag in ("pb-mcq", "pb-mrq") and "type" in node.attrib

    def apply(self):
        if self.node.tag == "pb-mcq" and self.node.get("type") == "rating":
            self.node.tag = "pb-rating"
        self.node.attrib.pop("type")  # Type attribute is no longer used.


class ReadOnlyAnswerToRecap(Change):
    """ <answer read_only="true"> is now <pb-answer-recap/> """
    @staticmethod
    def applies_to(node):
        return node.tag == "pb-answer" and node.get("read_only") == "true"

    def apply(self):
        self.node.tag = "pb-answer-recap"
        self.node.attrib.pop("read_only")
        for name in self.node.attrib:
            if name != "name":
                warnings.warn(f"Invalid attribute found on <answer>: {name}")


class QuestionToField(Change):
    """
    <answer/mcq/mrq/rating>
        <question>What is the answer?</question>
    </answer/mcq/mrq/rating>

    has become

    <answer/mcq/mrq question="What is the answer?"></answer>
    """
    @staticmethod
    def applies_to(node):
        parent_tags = ("pb-answer", "pb-mcq", "pb-mrq", "pb-rating")
        return node.tag == "question" and node.getparent().tag in parent_tags

    def apply(self):
        if list(self.node):
            warnings.warn("Ignoring unexpected children of a <question> element. HTML may be lost.")
        p = self.node.getparent()
        p.attrib["question"] = self.node.text
        p.remove(self.node)


class QuestionSubmitMessageToField(Change):
    """
    <mcq/mrq>
        <message type="on-submit">Thank you for answering!</message>
    </mcq/mrq>

    has become

    <mcq/mrq message="Thank you for answering!"></answer>
    """
    @staticmethod
    def applies_to(node):
        return (
            node.tag == "pb-message" and
            node.get("type") == "on-submit" and
            node.getparent().tag in ("pb-mcq", "pb-mrq")
        )

    def apply(self):
        if list(self.node):
            warnings.warn("Ignoring unexpected children of a <message> element. HTML may be lost.")
        p = self.node.getparent()
        p.attrib["message"] = self.node.text
        p.remove(self.node)


class TipChanges(Change):
    """
    Changes to <tip></tip> elements.
    The main one being that the correctness of each choice is now stored on the MRQ/MCQ block, not on the <tip>s.
    """
    @staticmethod
    def applies_to(node):
        return node.tag == "pb-tip" and node.getparent().tag in ("pb-mcq", "pb-mrq", "pb-rating")

    def apply(self):
        p = self.node.getparent()

        def add_to_list(list_name, value):
            if list_name in p.attrib:
                p.attrib[list_name] += f",{value}"
            else:
                p.attrib[list_name] = value

        if p.tag == "pb-mrq":
            if self.node.attrib.get("display"):
                value = self.node.attrib.pop("display")
                add_to_list("ignored_choices", value)
            elif self.node.attrib.get("require"):
                value = self.node.attrib.pop("require")
                add_to_list("required_choices", value)
            elif self.node.attrib.get("reject"):
                value = self.node.attrib.pop("reject")
            else:
                warnings.warn(f"Invalid <tip> element found: {etree.tostring(self.node)}")
                return
        else:
            # This is an MCQ or Rating question:
            if self.node.attrib.get("display"):
                value = self.node.attrib.pop("display")
                add_to_list("correct_choices", value)
            elif self.node.attrib.get("reject"):
                value = self.node.attrib.pop("reject")
            elif self.node.attrib.get("require"):
                value = self.node.attrib.pop("require")
                add_to_list("correct_choices", value)
                warnings.warn("<tip> element in an MCQ/Rating used 'require' rather than 'display'")
            else:
                warnings.warn(f"Invalid <tip> element found: {etree.tostring(self.node)}")
                return
        self.node.attrib["values"] = value
        if (self.node.text is None or self.node.text.strip() == "") and not list(self.node):
            # This tip is blank.
            p.remove(self.node)


class SharedHeaderToHTML(Change):
    """ <shared-header> element no longer exists. Just use <html> """
    @staticmethod
    def applies_to(node):
        return node.tag == "shared-header" and node.getparent().tag == "problem-builder"

    def apply(self):
        self.node.tag = "html"


class CommaSeparatedListToJson(Change):
    APPLY_TO_ATTRIBUTES = ("values", "correct_choices", "required_choices", "ignored_choices")

    def _convert_value(self, raw_value):
        return json.dumps([str(val).strip() for val in raw_value.split(',')])

    @staticmethod
    def applies_to(node):
        return node.tag in ("pb-tip", "pb-mrq", "pb-mcq", "pb-rating")

    def apply(self):
        for attribute in self.APPLY_TO_ATTRIBUTES:
            if attribute in self.node.attrib:
                self.node.attrib[attribute] = self._convert_value(self.node.attrib[attribute])


class OptionalShowTitleDefaultToFalse(Change):
    """
    In recent versions of mentoring, show_title defaults to True. In old versions there were no
    titles. If upgrading an old version, show_title should be set False.
    """
    @staticmethod
    def applies_to(node):
        return node.tag in ("pb-answer", "pb-mrq", "pb-mcq", "pb-rating") and ("show_title" not in node.attrib)

    def apply(self):
        self.node.attrib["show_title"] = "false"


def convert_xml_to_v2(node, from_version="v1"):
    """
    Given an XML node, re-structure it as needed to convert it from v1 style to v2 style XML.

    If from_version is set to "v0", then the "show_title" attribute on each question will be set
    to False, for compatibility with old versions of the mentoring block that didn't have
    question titles at all.
    """

    # An *ordered* list of all XML schema changes:
    xml_changes = [
        RenameMentoringTag,
        PrefixTags,
        HideTitle,
        RemoveTitle,
        UnwrapHTML,
        RenameTableTag,
        TableColumnHeader,
        QuizzToMCQ,
        MCQToRating,
        ReadOnlyAnswerToRecap,
        QuestionToField,
        QuestionSubmitMessageToField,
        TipChanges,
        SharedHeaderToHTML,
        CommaSeparatedListToJson,
    ]

    if from_version == "v0":
        xml_changes.append(OptionalShowTitleDefaultToFalse)

    # Apply each individual type of change one at a time:
    for change in xml_changes:
        # Walk the XML tree once and figure out all the changes we will need.
        # This lets us avoid modifying the tree while walking it.
        changes_needed = []
        for element in node.iter():
            if change.applies_to(element):
                changes_needed.append(change(element))
        for change in changes_needed:
            change.apply()
