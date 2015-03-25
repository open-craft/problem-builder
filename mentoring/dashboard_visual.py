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
Visual Representation of Dashboard State.

Consists of a series of images, layered on top of each other, where the appearance of each layer
can be tied to the average value of the student's response to a particular Problem Builder
block.

For example, each layer can have its color turn green if the student's average value on MCQs in
a specific Problem Builder block was at least 3.
"""
import ast
import operator as op


class DashboardVisualData(object):
    """
    Data about the visual representation of a dashboard.
    """
    def __init__(self, blocks, rules):
        """
        Construct the data required for the optional visual representation of the dashboard.

        Data format accepted for rules is like:
        {
            "images": [
                "step1.png",
                "step2.png",
                "step3.png",
                "step4.png",
                "step5.png",
                "step6.png",
                "step7.png"
            ],
            "overlay": "overlay.png",
            "colorRules": [
                {"if": "x < 1", "hueRotate": "20"},
                {"if": "x < 2", "hueRotate": "80"},
                {"blur": "x / 2", "saturate": "0.4"}
            ],
            "width": "500",
            "height": "500"
        }
        """
        # Images is a list of images, one per PB block, in the same order as 'blocks'
        # All images are rendered layered on top of each other, and can be hidden,
        # shown, colorized, faded, etc. based on the average answer value for that PB block.
        images = rules.get("images", [])
        # Overlay is an optional images drawn on top, with no effects applied
        overlay = rules.get("overlay")
        # Background is an optional images drawn on the bottom, with no effects applied
        background = rules.get("background")
        # Color rules specify how the average value of the PB block affects that block's image.
        # Each rule is evaluated in order, and the first matching rule is used.
        # Each rule can have an "if" expression that is evaluated and if true, that rule will
        # be used.
        colorRules = rules.get("colorRules", [])
        # Width and height of the image:
        self.width = int(rules.get("width", 400))
        self.height = int(rules.get("height", 400))

        self.layers = []
        if background:
            self.layers.append({"url": background})
        for idx, block in enumerate(blocks):
            if not block.get("has_average"):
                continue  # We only use blocks with numeric averages for the visual representation
            # Now we build the 'layer_data' information to pass on to the template:
            try:
                layer_data = {"url": images[idx], "id": "layer{}".format(idx)}
            except IndexError:
                break

            # Check if a color rule applies:
            x = block["average"]
            for rule in colorRules:
                condition = rule.get("if")
                if condition and not self._safe_eval_expression(condition, x):
                    continue  # This rule does not apply
                # Rule does apply:
                layer_data["has_filter"] = True
                for key in ("hueRotate", "blur", "saturate"):
                    if key in rule:
                        layer_data[key] = self._safe_eval_expression(rule[key], x)
                break
            self.layers.append(layer_data)

        if overlay:
            self.layers.append({"url": overlay})

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

        return eval_(ast.parse(expr, mode='eval').body)
