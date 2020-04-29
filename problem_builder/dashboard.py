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
Dashboard: Summarize the results of self-assessments done by a student with Problem Builder MCQ
blocks.

The author of this block specifies a list of Problem Builder blocks containing MCQs. This block
will then display a table summarizing the values that the student chose for each of those MCQs.
"""
# Imports ###########################################################

import ast
import json
import logging
import operator as op

import six
from django.template.defaultfilters import floatformat
from lazy import lazy
from xblock.core import XBlock
from xblock.fields import Boolean, Dict, List, Scope, String
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage
from xblockutils.helpers import child_isinstance
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

from .dashboard_visual import DashboardVisualData
from .mcq import MCQBlock
from .sub_api import sub_api

# Globals ###########################################################

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


def _(text):
    """ A no-op to mark strings that we need to translate """
    return text

# Classes ###########################################################


class ExportMixin:
    """
    Used by blocks which need to provide a downloadable export.
    """
    def _get_user_full_name(self):
        """
        Get the full name of the current user, for the downloadable report.
        """
        user_service = self.runtime.service(self, 'user')
        if user_service:
            return user_service.get_current_user().full_name
        return ""

    def _get_course_name(self):
        """
        Get the name of the current course, for the downloadable report.
        """
        try:
            course_key = self.scope_ids.usage_id.course_key
        except AttributeError:
            return ""  # We are not in an edX runtime
        try:
            course_root_key = course_key.make_usage_key('course', 'course')
            return self.runtime.get_block(course_root_key).display_name
        except Exception:  # ItemNotFoundError most likely, but we can't import that exception in non-edX environments
            # We may be on old mongo:
            try:
                course_root_key = course_key.make_usage_key('course', course_key.run)
                return self.runtime.get_block(course_root_key).display_name
            except Exception:
                return ""


class ColorRule:
    """
    A rule used to conditionally set colors

    >>> rule1 = ColorRule("3 < x <= 5", color_str="#ff0000")
    >>> rule1.matches(2)
    False
    >>> rule1.matches(4)
    True
    """
    def __init__(self, rule_str, color_str):
        """
        Instantiate a ColorRule with the given rule expression string and color value.
        """
        try:
            self._rule_parsed = ast.parse(rule_str, mode='eval').body
            # Once it's been parsed, also try evaluating it with a test value:
            self._safe_eval_expression(self._rule_parsed, x=0)
        except (TypeError, SyntaxError) as e:
            raise ValueError("Invalid Expression: {}".format(e))
        except ZeroDivisionError:
            pass  # This may depend on the value of 'x' which we set to zero but don't know yet.
        self.color_str = color_str

    def matches(self, x):
        """ Does this rule apply for the value x? """
        try:
            return bool(self._safe_eval_expression(self._rule_parsed, x))
        except ZeroDivisionError:
            return False

    @staticmethod
    def _safe_eval_expression(expr, x=0):
        """
        Safely evaluate a mathematical or boolean expression involving the value x

        >>> _safe_eval_expression('2*x', x=3)
        6
        >>> _safe_eval_expression('x >= 0 and x < 2', x=3)
        False

        We use python syntax for the expressions, so the parsing and evaluation is mostly done
        using Python's built-in asbstract syntax trees and operator implementations.

        The expression can only contain: numbers, mathematical operators, boolean operators,
        comparisons, and a placeholder variable called "x"
        """
        # supported operators:
        operators = {
            # Allow +, -, *, /, %, negative:
            ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv, ast.Mod: op.mod, ast.USub: op.neg,
            # Allow comparison:
            ast.Eq: op.eq, ast.NotEq: op.ne, ast.Lt: op.lt, ast.LtE: op.le, ast.Gt: op.gt, ast.GtE: op.ge,
        }

        def eval_(node):
            """ Recursive evaluation of syntax tree node 'node' """
            if isinstance(node, ast.Num):  # <number>
                return node.n
            elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
                return operators[type(node.op)](eval_(node.left), eval_(node.right))
            elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
                return operators[type(node.op)](eval_(node.operand))
            elif isinstance(node, ast.Name) and node.id == "x":
                return x
            elif isinstance(node, ast.BoolOp):  # Boolean operator: either "and" or "or" with two or more values
                if type(node.op) == ast.And:
                    return all(eval_(val) for val in node.values)
                else:  # Or:
                    for val in node.values:
                        result = eval_(val)
                        if result:
                            return result
                    return result  # or returns the final value even if it's falsy
            elif isinstance(node, ast.Compare):  # A comparison expression, e.g. "3 > 2" or "5 < x < 10"
                left = eval_(node.left)
                for comparison_op, right_expr in zip(node.ops, node.comparators):
                    right = eval_(right_expr)
                    if not operators[type(comparison_op)](left, right):
                        return False
                    left = right
                return True
            else:
                raise TypeError(node)

        if not isinstance(expr, ast.AST):
            expr = ast.parse(expr, mode='eval').body
        return eval_(expr)


class InvalidUrlName(ValueError):
    """ Exception raised by DashboardBlock.get_mentoring_blocks() if a url_name is invalid """
    pass


@XBlock.needs("i18n")
@XBlock.wants("user")
class DashboardBlock(StudioEditableXBlockMixin, ExportMixin, XBlock):
    """
    A block to summarize self-assessment results.
    """
    display_name = String(
        display_name=_("Display Name"),
        help=_("Display name for this module"),
        scope=Scope.settings,
        default=_('Self-Assessment Summary'),
    )
    mentoring_ids = List(
        display_name=_("Mentoring Blocks"),
        help=_(
            "This should be an ordered list of the url_names of each mentoring block whose multiple choice question "
            "values are to be shown on this dashboard. The list should be in JSON format. Example: {example_here}"
        ).format(example_here='["2754b8afc03a439693b9887b6f1d9e36", "215028f7df3d4c68b14fb5fea4da7053"]'),
        scope=Scope.settings,
    )
    exclude_questions = Dict(
        display_name=_("Questions to be hidden"),
        help=_(
            "Optional rules to exclude specific questions both from displaying in dashboard and from the calculated "
            "average. Rules must start with the url_name of a mentoring block, followed by list of question numbers "
            "to exclude. Rule set must be in JSON format. Question numbers are one-based (the first question being "
            "number 1). Must be in JSON format. Examples: {examples_here}"
        ).format(
            examples_here='{"2754b8afc03a439693b9887b6f1d9e36":[1,2], "215028f7df3d4c68b14fb5fea4da7053":[1,5]}'
        ),
        scope=Scope.content,
        multiline_editor=True,
        resettable_editor=False,
    )
    color_rules = String(
        display_name=_("Color Coding Rules"),
        help=_(
            "Optional rules to assign colors to possible answer values and average values. "
            "One rule per line. First matching rule will be used. Light colors are recommended. "
            "Examples: {examples_here}"
        ).format(examples_here='"1: LightCoral", "0 <= x < 5: LightBlue", "LightGreen"'),
        scope=Scope.content,
        default="",
        multiline_editor=True,
        resettable_editor=False,
    )
    visual_rules = String(
        display_name=_("Visual Representation"),
        default="",
        help=_("Optional: Enter the JSON configuration of the visual representation desired (Advanced)."),
        scope=Scope.content,
        multiline_editor=True,
        resettable_editor=False,
    )
    visual_title = String(
        display_name=_("Visual Representation Title"),
        default=_("Visual Representation"),
        help=_("This text is not displayed visually but is exposed to screen reader users who may not see the image."),
        scope=Scope.content,
    )
    visual_desc = String(
        display_name=_("Visual Repr. Description"),
        default=_("The data represented in this image is available in the tables below."),
        help=_(
            "This longer description is not displayed visually but is exposed to screen reader "
            "users who may not see the image."
        ),
        scope=Scope.content,
    )
    average_labels = Dict(
        display_name=_("Label for average value"),
        help=_(
            "This settings allows overriding label for the calculated average per mentoring block. Must be in JSON "
            "format. Examples: {examples_here}."
        ).format(
            examples_here='{"2754b8afc03a439693b9887b6f1d9e36": "Avg.", "215028f7df3d4c68b14fb5fea4da7053": "Mean"}'
        ),
        scope=Scope.content,
    )
    show_numbers = Boolean(
        display_name=_("Display values"),
        default=True,
        help=_("Toggles if numeric values are displayed"),
        scope=Scope.content
    )
    header_html = String(
        display_name=_("Header HTML"),
        default="",
        help=_("Custom text to include at the beginning of the report."),
        multiline_editor="html",
        resettable_editor=False,
        scope=Scope.content,
    )
    footer_html = String(
        display_name=_("Footer HTML"),
        default="",
        help=_("Custom text to include at the end of the report."),
        multiline_editor="html",
        resettable_editor=False,
        scope=Scope.content,
    )

    editable_fields = (
        'display_name', 'mentoring_ids', 'exclude_questions', 'average_labels', 'show_numbers',
        'color_rules', 'visual_rules', 'visual_title', 'visual_desc', 'header_html', 'footer_html',
    )
    css_path = 'public/css/dashboard.css'
    js_path = 'public/js/review_blocks.js'

    def get_mentoring_blocks(self, mentoring_ids, ignore_errors=True):
        """
        Generator returning the specified mentoring blocks, in order.

        Will yield None for every invalid mentoring block ID, or if
        ignore_errors is False, will raise InvalidUrlName.
        """
        for url_name in mentoring_ids:
            try:
                mentoring_id = self.scope_ids.usage_id.course_key.make_usage_key('problem-builder', url_name)
                yield self.runtime.get_block(mentoring_id)
            except Exception:  # Catch-all b/c we could get XBlockNotFoundError, ItemNotFoundError, InvalidKeyError, ...
                # Maybe it's using the deprecated block type "mentoring":
                try:
                    mentoring_id = self.scope_ids.usage_id.course_key.make_usage_key('mentoring', url_name)
                    yield self.runtime.get_block(mentoring_id)
                except Exception:
                    if ignore_errors:
                        yield None
                    else:
                        raise InvalidUrlName(url_name)

    def parse_color_rules_str(self, color_rules_str, ignore_errors=True):
        """
        Parse the color rules. Returns a list of ColorRule objects.

        Color rules are like: "0 < x < 4: red" or "blue" (for a catch-all rule)
        """
        rules = []
        for lineno, line in enumerate(color_rules_str.splitlines()):
            line = line.strip()
            if line:
                try:
                    if ":" in line:
                        condition, value = line.split(':')
                        value = value.strip()
                        if condition.isnumeric():  # A condition just listed as an exact value
                            condition = "x == " + condition
                    else:
                        condition = "1"  # Always true
                        value = line
                    rules.append(ColorRule(condition, value))
                except ValueError:
                    if ignore_errors:
                        continue
                    raise ValueError(
                        _("Invalid color rule on line {line_number}").format(line_number=lineno + 1)
                    )
        return rules

    @lazy
    def color_rules_parsed(self):
        """
        Caching property to get parsed color rules. Returns a list of ColorRule objects.
        """
        return self.parse_color_rules_str(self.color_rules) if self.color_rules else []

    def _get_submission_key(self, usage_key):
        """
        Given the usage_key of an MCQ block, get the dict key needed to look it up with the
        submissions API.
        """
        return dict(
            student_id=self.runtime.anonymous_student_id,
            course_id=six.text_type(usage_key.course_key),
            item_id=six.text_type(usage_key),
            item_type=usage_key.block_type,
        )

    def color_for_value(self, value):
        """ Given a string value, get the color rule that matches, if any """
        if isinstance(value, six.string_types):
            if value.isnumeric():
                value = float(value)
            else:
                return None
        for rule in self.color_rules_parsed:
            if rule.matches(value):
                return rule.color_str
        return None

    def _get_problem_questions(self, mentoring_block):
        """ Generator returning only children of specified block that are MCQs """
        for child_id in mentoring_block.children:
            if child_isinstance(mentoring_block, child_id, MCQBlock):
                yield child_id

    @XBlock.supports("multi_device")  # Mark as mobile-friendly
    def student_view(self, context=None):  # pylint: disable=unused-argument
        """
        Standard view of this XBlock.
        """
        if not self.mentoring_ids:
            return Fragment(u"<h1>{}</h1><p>{}</p>".format(self.display_name, _("Not configured.")))

        blocks = []
        for mentoring_block in self.get_mentoring_blocks(self.mentoring_ids):
            if mentoring_block is None:
                continue
            block = {
                'display_name': mentoring_block.display_name,
                'mcqs': []
            }
            try:
                hide_questions = self.exclude_questions.get(mentoring_block.url_name, [])
            except Exception:  # pylint: disable=broad-except-clause
                log.exception("Cannot parse exclude_questions setting - probably malformed: %s", self.exclude_questions)
                hide_questions = []

            for question_number, child_id in enumerate(self._get_problem_questions(mentoring_block), 1):
                try:
                    if question_number in hide_questions:
                        continue
                except TypeError:
                    log.exception(
                        "Cannot check question number - expected list of ints got: %s",
                        hide_questions
                    )

                # Get the student's submitted answer to this MCQ from the submissions API:
                mcq_block = self.runtime.get_block(child_id)
                mcq_submission_key = self._get_submission_key(child_id)
                try:
                    value = sub_api.get_submissions(mcq_submission_key, limit=1)[0]["answer"]
                except IndexError:
                    value = None

                block['mcqs'].append({
                    "display_name": mcq_block.display_name_with_default,
                    "value": value,
                    "accessible_value": _("Score: {score}").format(score=value) if value else _("No value yet"),
                    "color": self.color_for_value(value) if value is not None else None,
                })
            # If the values are numeric, display an average:
            numeric_values = [
                float(mcq['value']) for mcq in block['mcqs']
                if mcq['value'] is not None and mcq['value'].isnumeric()
            ]
            if numeric_values:
                average_value = sum(numeric_values) / len(numeric_values)
                block['average'] = average_value
                # average block is shown only if average value exists, so accessible text for no data is not required
                block['accessible_average'] = _("Score: {score}").format(
                    score=floatformat(average_value)
                )
                block['average_label'] = self.average_labels.get(mentoring_block.url_name, _("Average"))
                block['has_average'] = True
                block['average_color'] = self.color_for_value(average_value)
            blocks.append(block)

        visual_repr = None
        if self.visual_rules:
            try:
                rules_parsed = json.loads(self.visual_rules)
            except ValueError:
                pass  # JSON errors should be shown as part of validation
            else:
                visual_repr = DashboardVisualData(
                    blocks, rules_parsed, self.color_for_value, self.visual_title, self.visual_desc
                )

        report_template = loader.render_django_template('templates/html/dashboard_report.html', {
            'title': self.display_name,
            'css': loader.load_unicode(self.css_path),
            'student_name': self._get_user_full_name(),
            'course_name': self._get_course_name(),
        })

        html = loader.render_django_template('templates/html/dashboard.html', {
            'blocks': blocks,
            'display_name': self.display_name,
            'visual_repr': visual_repr,
            'show_numbers': self.show_numbers,
            'header_html': self.header_html,
            'footer_html': self.footer_html,
        })

        fragment = Fragment(html)
        fragment.add_css_url(self.runtime.local_resource_url(self, self.css_path))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, self.js_path))
        fragment.initialize_js(
            'PBDashboardBlock', {
                'reportTemplate': report_template,
                'reportContentSelector': '.dashboard-report'
            })
        return fragment

    def validate_field_data(self, validation, data):
        """
        Validate this block's field data.
        """
        super(DashboardBlock, self).validate_field_data(validation, data)

        def add_error(msg):
            validation.add(ValidationMessage(ValidationMessage.ERROR, msg))

        try:
            list(self.get_mentoring_blocks(data.mentoring_ids, ignore_errors=False))
        except InvalidUrlName as e:
            add_error(_(u'Invalid block url_name given: "{bad_url_name}"').format(bad_url_name=six.text_type(e)))

        if data.exclude_questions:
            for key, value in six.iteritems(data.exclude_questions):
                if not isinstance(value, list):
                    add_error(
                        _(u"'Questions to be hidden' is malformed: value for key {key} is {value}, "
                          u"expected list of integers")
                        .format(key=key, value=value)
                    )

                if key not in data.mentoring_ids:
                    add_error(
                        _(u"'Questions to be hidden' is malformed: mentoring url_name {url_name} "
                          u"is not added to Dashboard")
                        .format(url_name=key)
                    )

        if data.average_labels:
            for key, value in six.iteritems(data.average_labels):
                if not isinstance(value, six.string_types):
                    add_error(
                        _(u"'Label for average value' is malformed: value for key {key} is {value}, expected string")
                        .format(key=key, value=value)
                    )

                if key not in data.mentoring_ids:
                    add_error(
                        _(u"'Label for average value' is malformed: mentoring url_name {url_name} "
                          u"is not added to Dashboard")
                        .format(url_name=key)
                    )

        if data.color_rules:
            try:
                self.parse_color_rules_str(data.color_rules, ignore_errors=False)
            except ValueError as e:
                add_error(six.text_type(e))

        if data.visual_rules:
            try:
                rules = json.loads(data.visual_rules)
            except ValueError as e:
                add_error(_(u"Visual rules contains an error: {error}").format(error=e))
            else:
                if not isinstance(rules, dict):
                    add_error(_(u"Visual rules should be a JSON dictionary/object: {...}"))
