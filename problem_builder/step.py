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

import logging

from lazy.lazy import lazy
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import List, Scope, String
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import (NestedXBlockSpec,
                                         StudioContainerWithNestedXBlocksMixin,
                                         StudioEditableXBlockMixin,
                                         XBlockWithPreviewMixin)

from problem_builder.answer import AnswerBlock, AnswerRecapBlock
from problem_builder.completion import CompletionBlock
from problem_builder.mcq import MCQBlock, RatingBlock
from problem_builder.mixins import (
    EnumerableChildMixin, StepParentMixin, StudentViewUserStateMixin,
    StudentViewUserStateResultsTransformerMixin)
from problem_builder.mrq import MRQBlock
from problem_builder.plot import PlotBlock
from problem_builder.slider import SliderBlock
from problem_builder.table import MentoringTableBlock

from .mixins import TranslationContentMixin
from .utils import I18NService

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


# Make '_' a no-op so we can scrape strings
def _(text):
    return text


def _normalize_id(key):
    """
    Helper method to normalize a key to avoid issues where some keys have version/branch and others don't.
    e.g. self.scope_ids.usage_id != self.runtime.get_block(self.scope_ids.usage_id).scope_ids.usage_id
    """
    if hasattr(key, "for_branch"):
        key = key.for_branch(None)
    if hasattr(key, "for_version"):
        key = key.for_version(None)
    return key


class Correctness:
    CORRECT = 'correct'
    PARTIAL = 'partial'
    INCORRECT = 'incorrect'


@XBlock.needs('i18n')
class MentoringStepBlock(
    StudioEditableXBlockMixin, StudioContainerWithNestedXBlocksMixin, XBlockWithPreviewMixin,
    EnumerableChildMixin, StepParentMixin, StudentViewUserStateResultsTransformerMixin,
    StudentViewUserStateMixin, XBlock, I18NService, TranslationContentMixin
):
    """
    An XBlock for a step.
    """
    CAPTION = _("Step")
    STUDIO_LABEL = _("Mentoring Step")
    CATEGORY = 'sb-step'
    USER_STATE_FIELDS = ['student_results']

    # Settings
    display_name = String(
        display_name=_("Step Title"),
        help=_('Leave blank to use sequential numbering'),
        default="",
        scope=Scope.content
    )

    # User state
    student_results = List(
        # Store results of student choices.
        default=[],
        scope=Scope.user_state
    )

    next_button_label = String(
        display_name=_("Next Button Label"),
        help=_("Customize the text of the 'Next' button."),
        default=_("Next Step")
    )

    message = String(
        display_name=_("Message"),
        help=_("Feedback or instructional message which pops up after submitting."),
    )

    editable_fields = ('display_name', 'show_title', 'next_button_label', 'message')

    @lazy
    def siblings(self):
        return self.get_parent().step_ids

    @property
    def is_last_step(self):
        parent = self.get_parent()
        return self.step_number == len(parent.step_ids)  # pylint: disable=comparison-with-callable

    @property
    def allowed_nested_blocks(self):
        """
        Returns a list of allowed nested XBlocks. Each item can be either
        * An XBlock class
        * A NestedXBlockSpec

        If XBlock class is used it is assumed that this XBlock is enabled and allows multiple instances.
        NestedXBlockSpec allows explicitly setting disabled/enabled state, disabled reason (if any) and single/multiple
        instances
        """
        additional_blocks = []
        try:
            from xmodule.video_module.video_module import VideoBlock
            additional_blocks.append(NestedXBlockSpec(
                VideoBlock, category='video', label=_("Video")
            ))
        except ImportError:
            pass
        try:
            from imagemodal import ImageModal
            additional_blocks.append(NestedXBlockSpec(
                ImageModal, category='imagemodal', label=_("Image Modal")
            ))
        except ImportError:
            pass

        try:
            from ooyala_player.ooyala_player import OoyalaPlayerBlock
            additional_blocks.append(NestedXBlockSpec(
                OoyalaPlayerBlock, category='ooyala-player', label=_("Ooyala Player")
            ))
        except ImportError:
            pass

        return [
            NestedXBlockSpec(AnswerBlock, boilerplate='studio_default'),
            MCQBlock, RatingBlock, MRQBlock, CompletionBlock,
            NestedXBlockSpec(None, category="html", label=self._("HTML")),
            AnswerRecapBlock, MentoringTableBlock, PlotBlock, SliderBlock
        ] + additional_blocks

    @property
    def has_question(self):
        return any(getattr(child, 'answerable', False) for child in self.steps)

    def submit(self, submissions):
        """ Handle a student submission. This is called by the parent XBlock. """
        log_message = f'Received submissions: {submissions}'
        log.info(log_message)

        # Submit child blocks (questions) and gather results
        submit_results = []
        for child in self.steps:
            if child.name and child.name in submissions:
                submission = submissions[child.name]
                child_result = child.submit(submission)
                submit_results.append([child.name, child_result])
                child.save()

        # Update results stored for this step
        self.reset()
        for result in submit_results:
            self.student_results.append(result)
        self.save()

        return {
            'message': 'Success!',
            'step_status': self.answer_status,
            'results': submit_results,
        }

    @XBlock.json_handler
    def get_results(self, queries, suffix=''):
        results = {}
        answers = dict(self.student_results)
        for question in self.steps:
            previous_results = answers[question.name]
            result = question.get_results(previous_results)
            results[question.name] = result

        # Add 'message' to results? Looks like it's not used on the client ...
        return {
            'results': results,
            'step_status': self.answer_status,
        }

    def reset(self):
        while self.student_results:
            self.student_results.pop()

    @property
    def answer_status(self):
        if all(result[1]['status'] == 'correct' for result in self.student_results):
            answer_status = Correctness.CORRECT
        elif all(result[1]['status'] == 'incorrect' for result in self.student_results):
            answer_status = Correctness.INCORRECT
        else:
            answer_status = Correctness.PARTIAL
        return answer_status

    def author_edit_view(self, context):
        """
        Add some HTML to the author view that allows authors to add child blocks.
        """
        local_context = dict(context)
        local_context['author_edit_view'] = True
        fragment = super().author_edit_view(local_context)
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder.css'))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder-edit.css'))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder-tinymce-content.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/util.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/container_edit.js'))
        fragment.initialize_js('ProblemBuilderContainerEdit')
        return fragment

    def mentoring_view(self, context=None):
        """ Mentoring View """
        return self._render_view(context, 'mentoring_view')

    def _render_view(self, context, view):
        """ Actually renders a view """
        rendering_for_studio = False
        if context:  # Workbench does not provide context
            rendering_for_studio = context.get('author_preview_view')

        fragment = Fragment()
        child_contents = []

        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            if child is None:  # child should not be None but it can happen due to bugs or permission issues
                child_contents.append(f'<p>[{self._("Error: Unable to load child component.")}]</p>')
            else:
                if rendering_for_studio and isinstance(child, PlotBlock):
                    # Don't use view to render plot blocks in Studio.
                    # This is necessary because:
                    # - student_view of plot block uses submissions API to retrieve results,
                    #   which causes "SubmissionRequestError" in Studio.
                    # - author_preview_view does not supply JS code for plot that JS code for step depends on
                    #   (step calls "update" on plot to get latest data during rendering).
                    child_contents.append(f"<p>{child.display_name}</p>")
                else:
                    child_fragment = self._render_child_fragment(child, context, view)
                    fragment.add_fragment_resources(child_fragment)
                    child_contents.append(child_fragment.content)

        fragment.add_content(loader.render_django_template('templates/html/step.html', {
            'self': self,
            'title': self.display_name,
            'show_title': self.show_title,
            'child_contents': child_contents,
        }, i18n_service=self.i18n_service))

        fragment.add_javascript(self.get_translation_content())
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/step.js'))
        fragment.initialize_js('MentoringStepBlock')

        return fragment

    def student_view_data(self, context=None):
        """
        Returns a JSON representation of the student_view of this XBlock,
        retrievable from the Course XBlock API.
        """
        components = []

        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            if hasattr(child, 'student_view_data'):
                components.append(child.student_view_data(context))

        return {
            'block_id': str(self.scope_ids.usage_id),
            'display_name': self.display_name_with_default,
            'type': self.CATEGORY,
            'title': self.display_name_with_default,
            'show_title': self.show_title,
            'next_button_label': self.next_button_label,
            'message': self.message,
            'components': components,
        }
