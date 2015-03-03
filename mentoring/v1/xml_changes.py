# -*- coding: utf-8 -*-
"""
Each class in this file represents a change made to the XML schema between v1 and v2.
"""
from lxml import etree
import warnings


class Change(object):
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


class RemoveTitle(Change):
    """ The old <title> element is now an attribute of <mentoring> """
    @staticmethod
    def applies_to(node):
        return node.tag == "title" and node.getparent().tag == "mentoring"

    def apply(self):
        title = self.node.text.strip()
        p = self.node.getparent()
        old_display_name = p.get("display_name")
        if old_display_name and old_display_name != title:
            warnings.warn('Replacing display_name="{}" with <title> value "{}"'.format(p.attrib["display_name"], title))
        p.attrib["display_name"] = title
        p.remove(self.node)


class UnwrapHTML(Change):
    """ <choice>,<tip>, <header>, and <message> now contain HTML without an explicit <html> wrapper. """
    @staticmethod
    def applies_to(node):
        return node.tag == "html" and node.getparent().tag in ("choice", "tip", "message", "header")

    def apply(self):
        p = self.node.getparent()
        if self.node.text:
            p.text = (p.text if p.text else u"") + self.node.text
        index = list(p).index(self.node)
        for child in list(self.node):
            index += 1
            p.insert(index, child)
        p.remove(self.node)


class TableColumnHeader(Change):
    """
    Replace:
    <mentoring-table>
         <column>
             <header>Answer 1</header>
             <answer name="answer_1" />
         </column>
    </mentoring-table>
    with
    <mentoring-table>
         <mentoring-column header="Answer 1">
             <answer-recap name="answer_1" />
         </mentoring-column>
    </mentoring-table>
    """
    @staticmethod
    def applies_to(node):
        return node.tag == "column" and node.getparent().tag == "mentoring-table"

    def apply(self):
        self.node.tag = "mentoring-column"
        header_html = u""
        to_remove = []
        for child in list(self.node):
            if child.tag == "header":
                if child.text:
                    header_html += child.text
                for grandchild in list(child):
                    header_html += etree.tostring(grandchild)
                to_remove.append(child)
            elif child.tag == "answer":
                child.tag = "answer-recap"
                if "read_only" in child.attrib:
                    del child.attrib["read_only"]
            elif child.tag != "html":
                warnings.warn("Invalid <column> element: Unexpected <{}>".format(child.tag))
                return
        for child in to_remove:
            self.node.remove(child)
        self.node.text = None
        if header_html:
            self.node.attrib["header"] = header_html


class PrefixMessageElements(Change):
    """
    <message> is renamed to <mentoring-message> since it only works as a direct child of
    <mentoring> and <message> could collide with other future XBlocks.
    """
    @staticmethod
    def applies_to(node):
        return node.tag == "message" and node.getparent().tag == "mentoring"

    def apply(self):
        self.node.tag = "mentoring-message"


class QuizzToMCQ(Change):
    """ <quizz> element was an alias for <mcq>. In v2 we only have <mcq> """
    @staticmethod
    def applies_to(node):
        return node.tag == "quizz"

    def apply(self):
        self.node.tag = "mcq"


class MCQToRating(Change):
    """ <mcq type="rating"> is now just <rating>, and we never use type="choices" on MCQ/MRQ """
    @staticmethod
    def applies_to(node):
        return node.tag in ("mcq", "mrq") and "type" in node.attrib

    def apply(self):
        if self.node.tag == "mcq" and self.node.get("type") == "rating":
            self.node.tag = "rating"
        self.node.attrib.pop("type")  # Type attribute is no longer used.


class ReadOnlyAnswerToRecap(Change):
    """ <answer read_only="true"> is now <answer-recap/> """
    @staticmethod
    def applies_to(node):
        return node.tag == "answer" and node.get("read_only") == "true"

    def apply(self):
        self.node.tag = "answer-recap"
        self.node.attrib
        self.node.attrib.pop("read_only")
        for name in self.node.attrib:
            if name != "name":
                warnings.warn("Invalid attribute found on <answer>: {}".format(name))


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
        parent_tags = ("answer", "mcq", "mrq", "rating")
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
        return node.tag == "message" and node.get("type") == "on-submit" and node.getparent().tag in ("mcq", "mrq")

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
        return node.tag == "tip" and node.getparent().tag in ("mcq", "mrq", "rating")

    def apply(self):
        p = self.node.getparent()

        def add_to_list(list_name, value):
            if list_name in p.attrib:
                p.attrib[list_name] += ",{}".format(value)
            else:
                p.attrib[list_name] = value

        if len(self.node.attrib) > 1:
            warnings.warn("Invalid <tip> element found.")
            return
        mode = self.node.attrib.keys()[0]
        value = self.node.attrib[mode]
        if p.tag == "mrq":
            if mode == "display":
                add_to_list("ignored_choices", value)
            elif mode == "require":
                add_to_list("required_choices", value)
            elif mode != "reject":
                warnings.warn("Invalid <tip> element: has {}={}".format(mode, value))
                return
        else:
            # This is an MCQ or Rating question:
            if mode == "display":
                add_to_list("correct_choices", value)
            elif mode != "reject":
                warnings.warn("Invalid <tip> element: has {}={}".format(mode, value))
                return
        self.node.attrib["values"] = value
        self.node.attrib.pop(mode)


class SharedHeaderToHTML(Change):
    """ <shared-header> element no longer exists. Just use <html> """
    @staticmethod
    def applies_to(node):
        return node.tag == "shared-header" and node.getparent().tag == "mentoring"

    def apply(self):
        self.node.tag = "html"


# An *ordered* list of all XML schema changes:
xml_changes = (
    RemoveTitle,
    UnwrapHTML,
    TableColumnHeader,
    PrefixMessageElements,
    QuizzToMCQ,
    MCQToRating,
    ReadOnlyAnswerToRecap,
    QuestionToField,
    QuestionSubmitMessageToField,
    TipChanges,
    SharedHeaderToHTML,
)


def convert_xml_v1_to_v2(node):
    """
    Given an XML node, re-structure it as needed to convert it from v1 style to v2 style XML.
    """
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
