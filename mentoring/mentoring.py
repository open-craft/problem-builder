
import logging
import pkg_resources

from xblock.core import XBlock
from xblock.fields import Integer, Scope, String
from xblock.fragment import Fragment

log = logging.getLogger(__name__)


class MentoringBlock(XBlock):
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

    def student_view(self, context):
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
                    <mentoring prompt="What is your answer?" />
                </vertical>
             """)
        ]
