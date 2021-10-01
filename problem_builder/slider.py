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

# Imports ###########################################################

import logging
import uuid

from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Float, Scope, String
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

from .mixins import (QuestionMixin, StudentViewUserStateMixin,
                     XBlockWithTranslationServiceMixin)
from .sub_api import SubmittingXBlockMixin, sub_api

# Globals ###########################################################

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


# Make '_' a no-op so we can scrape strings
def _(text):
    return text

# Classes ###########################################################


@XBlock.needs("i18n")
class SliderBlock(
    SubmittingXBlockMixin, QuestionMixin, StudioEditableXBlockMixin, XBlockWithTranslationServiceMixin,
    StudentViewUserStateMixin, XBlock,
):
    """
    An XBlock used by students to indicate a numeric value on a sliding scale.
    The student's answer is always considered "correct".
    """
    CATEGORY = 'pb-slider'
    STUDIO_LABEL = _("Ranged Value Slider")
    USER_STATE_FIELDS = ['student_value']

    answerable = True

    min_label = String(
        display_name=_("Low"),
        help=_("Label for low end of the range"),
        scope=Scope.content,
        default=_("0%"),
    )
    max_label = String(
        display_name=_("High"),
        help=_("Label for high end of the range"),
        scope=Scope.content,
        default=_("100%"),
    )

    question = String(
        display_name=_("Question"),
        help=_("Question to ask the student (optional)"),
        scope=Scope.content,
        default="",
        multiline_editor=True,
    )

    student_value = Float(
        # The value selected by the student
        default=None,
        scope=Scope.user_state,
    )

    editable_fields = ('min_label', 'max_label', 'display_name', 'question', 'show_title')

    @property
    def url_name(self):
        """
        Get the url_name for this block. In Studio/LMS it is provided by a mixin, so we just
        defer to super(). In the workbench or any other platform, we use the name.
        """
        try:
            return super().url_name
        except AttributeError:
            return self.name

    def mentoring_view(self, context):
        """ Main view of this block """
        context = context.copy() if context else {}
        context['question'] = self.question
        context['slider_id'] = f'pb-slider-{uuid.uuid4().hex[:20]}'
        context['initial_value'] = int(self.student_value*100) if self.student_value is not None else 50
        context['min_label'] = self.min_label
        context['max_label'] = self.max_label
        context['title'] = self.display_name_with_default
        context['hide_header'] = context.get('hide_header', False) or not self.show_title
        context['instructions_string'] = self._("Select a value from {min_label} to {max_label}").format(
            min_label=self.min_label, max_label=self.max_label
        )
        html = loader.render_django_template('templates/html/slider.html', context)

        fragment = Fragment(html)
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/slider.js'))
        fragment.initialize_js('SliderBlock')
        return fragment

    student_view = mentoring_view
    preview_view = mentoring_view

    def student_view_data(self, context=None):
        return {
            'id': self.name,
            'block_id': str(self.scope_ids.usage_id),
            'display_name': self.display_name_with_default,
            'type': self.CATEGORY,
            'question': self.question,
            'min_label': self.min_label,
            'max_label': self.max_label,
            'title': self.display_name_with_default,
            'hide_header': not self.show_title,
        }

    def author_view(self, context):
        """
        Add some HTML to the author view that allows authors to see the ID of the block, so they
        can refer to it in other blocks such as Plot blocks.
        """
        context['hide_header'] = True  # Header is already shown in the Studio wrapper
        fragment = self.student_view(context)
        fragment.add_content(loader.render_django_template('templates/html/slider_edit_footer.html', {
            "url_name": self.url_name
        }))
        return fragment

    def get_last_result(self):
        """ Return the current/last result in the required format """
        if self.student_value is None:
            return {}
        return {
            'submission': self.student_value,
            'status': 'correct',
            'tips': [],
            'weight': self.weight,
            'score': 1,
        }

    def get_results(self, _previous_result_unused=None):
        """ Alias for get_last_result() """
        return self.get_last_result()

    def submit(self, value):
        log.debug('Received Slider submission: "%s"', value)
        if value < 0 or value > 1:
            return {}  # Invalid
        self.student_value = value
        if sub_api:
            # Also send to the submissions API:
            sub_api.create_submission(self.student_item_key, value)
        result = self.get_last_result()
        log.debug('Slider submission result: %s', result)
        return result

    def get_submission_display(self, submission):
        """
        Get the human-readable version of a submission value
        """
        return submission * 100

    def validate_field_data(self, validation, data):
        """
        Validate this block's field data.
        """
        super().validate_field_data(validation, data)
