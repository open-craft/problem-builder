# -*- coding: utf-8 -*-

import logging
import pkg_resources

from xblock.problem import ProblemBlock
from xblock.fields import Integer, Scope, String
from xblock.fragment import Fragment

log = logging.getLogger(__name__)


class MentoringBlock(ProblemBlock):
    """
    An XBlock providing mentoring capabilities

    Each block is composed of a text prompt, an input field for a free answer from the student,
    and a set of multiple choice questions. The student submits his text answer, and is then asked
    the multiple-choice questions. A set of conditions on the answers provided to the multiple-
    choices will determine if the student is a) provided mentoring advices and asked to alter
    his answer, or b) is given the ok to continue.
    """

    prompt = String(help="Initial text displayed with the text input", default='Your answer?', scope=Scope.content)
    completed = Integer(help="How many times the student has completed this", default=0, scope=Scope.user_state)
    has_children = True

    @classmethod
    def parse_xml(cls, node, runtime, keys):
        log.info(u'cls={}, node={}, runtime={}, keys={}'.format(cls, node, runtime, keys))

        block = runtime.construct_xblock_from_class(cls, keys)

        # Find <script> children, turn them into script content.
        for child in node:
            if child.tag == "script":
                block.script += child.text
            else:
                block.runtime.add_node_as_child(block, child)

        return block

    def _TODO_student_view(self, context):
        """
        Create a fragment used to display the XBlock to a student.
        `context` is a dictionary used to configure the display (unused)

        Returns a `Fragment` object specifying the HTML, CSS, and JavaScript
        to display.
        """

        log.info(self.prompt)
        # Load the HTML fragment from within the package and fill in the template
        html_str = pkg_resources.resource_string(__name__, "../static/html/mentoring.html")
        frag = Fragment(unicode(html_str).format(self=self, prompt=self.prompt))

        # Load CSS
        css_str = pkg_resources.resource_string(__name__, "../static/css/mentoring.css")
        frag.add_css(unicode(css_str))

        # Load JS
        js_str = pkg_resources.resource_string(__name__, "../static/js/mentoring.js")
        frag.add_javascript(unicode(js_str))
        frag.initialize_js('MentoringBlock')

        return frag

    def studio_view(self, context):
        return Fragment(u'Studio view body')

    @staticmethod
    def workbench_scenarios():
        """Default scenario"""
        return [
            ("mentoring",
            """\
                <vertical>
                    <mentoring>
                        <html>
                            <h3>Pre-Goal Brainstrom</h3>
                            <p>What goals are you considering working on? Before choosing your goal, it’s helpful to do some reflection exercises.</p>
                            <p>Think about what would you most like to get better at, or improve upon. The goal you choose to work on during the course--</p>
                            <ul>
                                <li>should be a “personal growth” goal vs. a “therapy goal”—e.g., ‘to be more decisive,’ ‘to be a better listener,’ ‘to speak up more,’ “to be more spontaneous,’ ‘to be better organized,’ ‘to be less critical.’ Not: ‘to get over my depression,’ ‘come to terms with my parents’ divorce,’ ‘work through a trauma.’</li>
                                <li>should be something you’ve tried to succeed at in the past, but have not made the progress you wanted (or the progress has been too temporary) [this will almost ensure you are picking an ‘adaptive’ vs. a ‘technical’ improvement goal]</li>
                                <li>should matter to you enough that you will want to stay connected to it throughout the course, but should not feel so sensitive or raw that you would be uncomfortable sharing it with the members of your online section (if you choose to do so). The teaching team will always be able to see your diary.</li>
                                <li>Do not edit yourself at this point. There are no wrong answers. Use this space to brainstorm.</li>
                            </ul>
                        </html>

                        <html><p>What is $a+$b?</p></html>
                        <answer name="brainstorm_goals" />

                        <equality name="sum_checker" left="./sum_input/@student_input" right="$c" />
                        <script>
                            import random
                            a = random.randint(2, 5)
                            b = random.randint(1, 4)
                            c = a + b
                        </script>
                    </mentoring>
                </vertical>
             """)
        ]
