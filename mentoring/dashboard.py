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

from .dashboard_visual import DashboardVisualData
from .mcq import MCQBlock
from .sub_api import sub_api
from lazy import lazy
from webob import Response
from xblock.core import XBlock
from xblock.exceptions import XBlockNotFoundError
from xblock.fields import Scope, List, String
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage
from xblockutils.helpers import child_isinstance
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin


# Globals ###########################################################

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


def _(text):
    """ A no-op to mark strings that we need to translate """
    return text

# Classes ###########################################################


class ColorRule(object):
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


@XBlock.needs("i18n")
class DashboardBlock(StudioEditableXBlockMixin, XBlock):
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
    color_rules = String(
        display_name=_("Color Coding Rules"),
        help=_(
            "Optional rules to assign colors to possible answer values and average values. "
            "One rule per line. First matching rule will be used. "
            "Examples: {examples_here}"
        ).format(examples_here='"1: red", "0 <= x < 5: blue", "green"'),
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

    editable_fields = ('display_name', 'mentoring_ids', 'color_rules', 'visual_rules')
    css_path = 'public/css/dashboard.css'

    def get_mentoring_blocks(self):
        """
        Generator returning the specified mentoring blocks, in order.

        Returns a list. Will insert None for every invalid mentoring block ID.
        """
        for url_name in self.mentoring_ids:
            mentoring_id = self.scope_ids.usage_id.course_key.make_usage_key('problem-builder', url_name)
            try:
                yield self.runtime.get_block(mentoring_id)
            # Catch all here b/c edX runtime throws other exceptions we can't import in other contexts like workbench:
            except (XBlockNotFoundError, Exception):
                # Maybe it's using the deprecated block type "mentoring":
                mentoring_id = self.scope_ids.usage_id.course_key.make_usage_key('mentoring', url_name)
                try:
                    yield self.runtime.get_block(mentoring_id)
                except (XBlockNotFoundError, Exception):
                    yield None

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
            course_id=unicode(usage_key.course_key),
            item_id=unicode(usage_key),
            item_type=usage_key.block_type,
        )

    def color_for_value(self, value):
        """ Given a string value, get the color rule that matches, if any """
        if isinstance(value, basestring):
            if value.isnumeric():
                value = float(value)
            else:
                return None
        for rule in self.color_rules_parsed:
            if rule.matches(value):
                return rule.color_str
        return None

    def generate_content(self, include_report_link=True):
        """
        Create the HTML for this block, by getting the data and inserting it into a template.
        """
        blocks = []
        for mentoring_block in self.get_mentoring_blocks():
            if mentoring_block is None:
                continue
            block = {
                'display_name': mentoring_block.display_name,
                'mcqs': []
            }
            for child_id in mentoring_block.children:
                if child_isinstance(mentoring_block, child_id, MCQBlock):
                    # Get the student's submitted answer to this MCQ from the submissions API:
                    mcq_block = self.runtime.get_block(child_id)
                    mcq_submission_key = self._get_submission_key(child_id)
                    try:
                        value = sub_api.get_submissions(mcq_submission_key, limit=1)[0]["answer"]
                    except IndexError:
                        value = None
                    block['mcqs'].append({
                        "display_name": mcq_block.question,
                        "value": value,
                        "color": self.color_for_value(value),
                    })
            # If the values are numeric, display an average:
            numeric_values = [float(mcq['value']) for mcq in block['mcqs'] if mcq['value'] and mcq['value'].isnumeric()]
            if numeric_values:
                average_value = sum(numeric_values) / len(numeric_values)
                block['average'] = average_value
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
                visual_repr = DashboardVisualData(blocks, rules_parsed, self.color_for_value)

        return loader.render_template('templates/html/dashboard.html', {
            'blocks': blocks,
            'display_name': self.display_name,
            'visual_repr': visual_repr,
            'report_url': self.runtime.handler_url(self, "download_report") if include_report_link else None,
        })

    def student_view(self, context=None):  # pylint: disable=unused-argument
        """
        Standard view of this XBlock.
        """
        if not self.mentoring_ids:
            return Fragment(u"<h1>{}</h1><p>{}</p>".format(self.display_name, _("Not configured.")))

        fragment = Fragment(self.generate_content())
        fragment.add_css_url(self.runtime.local_resource_url(self, self.css_path))
        return fragment

    @XBlock.handler
    def download_report(self, request=None, suffix=None):  # pylint: disable=unused-argument
        if not self.mentoring_ids:
            return Response("Not generating report - it would be empty.", status=400)
        report_html = loader.render_template('templates/html/dashboard_report.html', {
            'title': self.display_name,
            'body': self.generate_content(include_report_link=False),
            'css': loader.load_unicode(self.css_path),
        })
        return Response(
            report_html,
            content_type='text/html',
            charset='utf8',
            content_disposition='attachment; filename=report.html',
        )

    def validate_field_data(self, validation, data):
        """
        Validate this block's field data.
        """
        super(DashboardBlock, self).validate_field_data(validation, data)

        def add_error(msg):
            validation.add(ValidationMessage(ValidationMessage.ERROR, msg))

        if data.color_rules:
            try:
                self.parse_color_rules_str(data.color_rules, ignore_errors=False)
            except ValueError as e:
                add_error(unicode(e))

        if data.visual_rules:
            try:
                rules = json.loads(data.visual_rules)
            except ValueError as e:
                add_error(_(u"Visual rules contains an error: {error}").format(error=e))
            else:
                if not isinstance(rules, dict):
                    add_error(_(u"Visual rules should be a JSON dictionary/object: {...}"))
