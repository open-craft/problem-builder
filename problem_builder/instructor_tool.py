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
Instructor Tool: An XBlock for instructors to export student answers from a course.

All processing is done offline.
"""
import json

from django.core.paginator import Paginator
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.exceptions import JsonHandlerError
from xblock.fields import Dict, List, Scope, String
from xblockutils.resources import ResourceLoader

from .mixins import TranslationContentMixin, XBlockWithTranslationServiceMixin
from .utils import I18NService

loader = ResourceLoader(__name__)

PAGE_SIZE = 15

# URL Path to the Course Blocks REST API.
# Note that we add a trailing slash to avoid the API's redirect hit.
COURSE_BLOCKS_API = '/api/courses/v1/blocks/'


# Make '_' a no-op so we can scrape strings
def _(text):
    return text


@XBlock.needs("i18n")
@XBlock.wants('user')
class InstructorToolBlock(XBlock, I18NService, TranslationContentMixin, XBlockWithTranslationServiceMixin):
    """
    InstructorToolBlock: An XBlock for instructors to export student answers from a course.

    All processing is done offline.
    """
    display_name = String(
        display_name=_("Title (Display name)"),
        help=_("Title to display"),
        default=_("Instructor Tool"),
        scope=Scope.settings
    )
    active_export_task_id = String(
        # The UUID of the celery AsyncResult for the most recent export,
        # IF we are sill waiting for it to finish
        default="",
        scope=Scope.user_state,
    )
    last_export_result = Dict(
        # The info dict returned by the most recent successful export.
        # If the export failed, it will have an "error" key set.
        default=None,
        scope=Scope.user_state,
    )
    display_data = List(
        # The list of results associated with the most recent successful export.
        # Stored separately to avoid the overhead of sending it to the client.
        default=None,
        scope=Scope.user_state,
    )
    has_author_view = True

    @property
    def display_name_with_default(self):
        return "Instructor Tool"

    def author_view(self, context=None):
        """ Studio View """
        # Warn the user that this block will only work from the LMS. (Since the CMS uses
        # different celery queues; our task listener is waiting for tasks on the LMS queue)
        return Fragment('<p>Instructor Tool Block</p><p>This block only works from the LMS.</p>')

    def studio_view(self, context=None):
        """ View for editing Instructor Tool block in Studio. """
        # Display friendly message explaining that the block is not editable.
        return Fragment('<p>This is a preconfigured block. It is not editable.</p>')

    def check_pending_export(self):
        """
        If we're waiting for an export, see if it has finished, and if so, get the result.
        """
        from .tasks import \
            export_data as \
            export_data_task  # Import here since this is edX LMS specific
        if self.active_export_task_id:
            async_result = export_data_task.AsyncResult(self.active_export_task_id)
            if async_result.ready():
                self._save_result(async_result)

    def _save_result(self, task_result):
        """ Given an AsyncResult or EagerResult, save it. """
        self.active_export_task_id = ''
        if task_result.successful():
            if isinstance(task_result.result, dict) and not task_result.result.get('error'):
                self.display_data = task_result.result['display_data']
                del task_result.result['display_data']
                self.last_export_result = task_result.result
            else:
                self.last_export_result = {'error': f'Unexpected result: {repr(task_result.result)}'}
                self.display_data = None
        else:
            self.last_export_result = {'error': str(task_result.result)}
            self.display_data = None

    @XBlock.json_handler
    def get_result_page(self, data, suffix=''):
        """ Return requested page of `last_export_result`. """
        paginator = Paginator(self.display_data, PAGE_SIZE)
        page = data.get('page', None)
        return {
            'display_data': paginator.page(page).object_list,
            'num_results': len(self.display_data),
            'page_size': PAGE_SIZE
        }

    def student_view(self, context=None):
        """ Normal View """
        if not self.user_is_staff():
            return Fragment('<p>This interface can only be used by course staff.</p>')
        block_choices = {
            self._('Multiple Choice Question'): 'MCQBlock',
            self._('Multiple Response Question'): 'MRQBlock',
            self._('Rating Question'): 'RatingBlock',
            self._('Long Answer'): 'AnswerBlock',
        }

        html = loader.render_django_template('templates/html/instructor_tool.html', {
            'block_choices': block_choices,
            'course_blocks_api': COURSE_BLOCKS_API,
            'root_block_id': str(getattr(self.runtime, 'course_id', 'course_id')),
        }, i18n_service=self.i18n_service)
        fragment = Fragment(html)
        fragment.add_javascript(self.get_translation_content())
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/instructor_tool.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/instructor_tool.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/vendor/underscore-min.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/vendor/backbone-min.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/vendor/backbone.paginator.min.js'))
        fragment.initialize_js('InstructorToolBlock')
        return fragment

    @property
    def download_url_for_last_report(self):
        """ Get the URL for the last report, if any """
        # Unfortunately this is a bit inefficient due to the ReportStore API
        if not self.last_export_result or self.last_export_result['error'] is not None:
            return None
        from lms.djangoapps.instructor_task.models import ReportStore
        report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
        course_key = getattr(self.scope_ids.usage_id, 'course_key', None)
        return dict(report_store.links_for(course_key)).get(self.last_export_result['report_filename'])

    def _get_status(self):
        self.check_pending_export()
        return {
            'export_pending': bool(self.active_export_task_id),
            'last_export_result': self.last_export_result,
            'download_url': self.download_url_for_last_report,
        }

    def raise_error(self, code, message):
        """
        Raises an error and marks the block with a simulated failed task dict.
        """
        self.last_export_result = {
            'error': message,
        }
        self.display_data = None
        raise JsonHandlerError(code, message)

    @XBlock.json_handler
    def get_status(self, data, suffix=''):
        return self._get_status()

    @XBlock.json_handler
    def delete_export(self, data, suffix=''):
        self._delete_export()
        return self._get_status()

    def _delete_export(self):
        self.last_export_result = None
        self.display_data = None
        self.active_export_task_id = ''

    @XBlock.json_handler
    def start_export(self, data, suffix=''):
        """ Start a new asynchronous export """
        block_types = data.get('block_types', None)
        usernames = data.get('usernames', None)
        root_block_id = data.get('root_block_id', None)
        match_string = data.get('match_string', None)

        # Process user-submitted data
        if block_types == 'all':
            block_types = []
        else:
            block_types = [block_types]

        user_service = self.runtime.service(self, 'user')
        if not self.user_is_staff():
            return {'error': 'permission denied'}
        if not usernames:
            user_ids = None
        else:
            user_ids = []
            for username in usernames.split(','):
                username = username.strip()
                user_id = user_service.get_anonymous_user_id(username, str(self.runtime.course_id))
                if user_id:
                    user_ids.append(user_id)
            if not user_ids:
                self.raise_error(404, self._("Could not find any of the specified usernames."))

        if not root_block_id:
            root_block_id = self.scope_ids.usage_id
            # Block ID not in workbench runtime.
            root_block_id = str(getattr(root_block_id, 'block_id', root_block_id))

        # Launch task
        from .tasks import \
            export_data as \
            export_data_task  # Import here since this is edX LMS specific
        self._delete_export()
        # Make sure we nail down our state before sending off an asynchronous task.
        self.save()
        async_result = export_data_task.delay(
            # course_id not available in workbench.
            str(getattr(self.runtime, 'course_id', 'course_id')),
            root_block_id,
            block_types,
            user_ids,
            match_string,
        )
        if async_result.ready():
            # In development mode, the task may have executed synchronously.
            # Store the result now, because we won't be able to retrieve it later :-/
            if async_result.successful():
                # Make sure the result can be represented as JSON, since the non-eager celery
                # requires that
                json.dumps(async_result.result)
            self._save_result(async_result)
        else:
            # The task is running asynchronously. Store the result ID so we can query its progress:
            self.active_export_task_id = async_result.id
        return self._get_status()

    @XBlock.json_handler
    def cancel_export(self, request, suffix=''):
        from .tasks import \
            export_data as \
            export_data_task  # Import here since this is edX LMS specific
        if self.active_export_task_id:
            async_result = export_data_task.AsyncResult(self.active_export_task_id)
            async_result.revoke()
            self._delete_export()

    def _get_user_attr(self, attr):
        """Get an attribute of the current user."""
        user_service = self.runtime.service(self, 'user')
        if user_service:
            # May be None when creating bok choy test fixtures
            return user_service.get_current_user().opt_attrs.get(attr)
        return None

    def user_is_staff(self):
        """Return a Boolean value indicating whether the current user is a member of staff."""
        return self._get_user_attr('edx-platform.user_is_staff')
