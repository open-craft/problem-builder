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
Instructor Tool: An XBlock for instructors to export student answers from a course.

All processing is done offline.
"""
import json
from django.core.paginator import Paginator
from xblock.core import XBlock
from xblock.exceptions import JsonHandlerError
from xblock.fields import Scope, String, Dict, List
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader

loader = ResourceLoader(__name__)

PAGE_SIZE = 15


# Make '_' a no-op so we can scrape strings
def _(text):
    return text


@XBlock.needs("i18n")
@XBlock.wants('user')
class InstructorToolBlock(XBlock):
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
        return Fragment(u'<p>Instructor Tool Block</p><p>This block only works from the LMS.</p>')

    def studio_view(self, context=None):
        """ View for editing Instructor Tool block in Studio. """
        # Display friendly message explaining that the block is not editable.
        return Fragment(u'<p>This is a preconfigured block. It is not editable.</p>')

    def check_pending_export(self):
        """
        If we're waiting for an export, see if it has finished, and if so, get the result.
        """
        from .tasks import export_data as export_data_task  # Import here since this is edX LMS specific
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
                self.last_export_result = {'error': u'Unexpected result: {}'.format(repr(task_result.result))}
                self.display_data = None
        else:
            self.last_export_result = {'error': unicode(task_result.result)}
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
            return Fragment(u'<p>This interface can only be used by course staff.</p>')
        block_choices = {
            _('Multiple Choice Question'): 'MCQBlock',
            _('Rating Question'): 'RatingBlock',
            _('Long Answer'): 'AnswerBlock',
        }
        block_types = ('pb-mcq', 'pb-rating', 'pb-answer')
        flat_block_tree = []

        def get_block_id(block):
            """
            Return ID of `block`, taking into account needs of both LMS/CMS and workbench runtimes.
            """
            usage_id = block.scope_ids.usage_id
            # Try accessing block ID. If usage_id does not have it, return usage_id itself
            return unicode(getattr(usage_id, 'block_id', usage_id))

        def get_block_name(block):
            """
            Return name of `block`.

            Try attributes in the following order:
              - block.question
              - block.name (fallback for old courses)
              - block.display_name
              - block ID
            """
            # - Try "question" attribute:
            block_name = getattr(block, 'question', None)
            if not block_name:
                # Try question ID (name):
                block_name = getattr(block, 'name', None)
            if not block_name:
                # - Try display_name:
                block_name = getattr(block, 'display_name', None)
            if not block_name:
                # - Default to ID:
                block_name = get_block_id(block)
            return block_name

        def get_block_type(block):
            """
            Return type of `block`, taking into account different key styles that might be in use.
            """
            try:
                block_type = block.runtime.id_reader.get_block_type(block.scope_ids.def_id)
            except AttributeError:
                block_type = block.runtime.id_reader.get_block_type(block.scope_ids.usage_id)
            return block_type

        def build_tree(block, ancestors):
            """
            Build up a tree of information about the XBlocks descending from root_block
            """
            block_id = get_block_id(block)
            block_name = get_block_name(block)
            block_type = get_block_type(block)
            if not block_type == 'pb-choice':
                eligible = block_type in block_types
                if eligible:
                    # If this block is a question whose answers we can export,
                    # we mark all of its ancestors as exportable too
                    if ancestors and not ancestors[-1]["eligible"]:
                        for ancestor in ancestors:
                            ancestor["eligible"] = True

                new_entry = {
                    "depth": len(ancestors),
                    "id": block_id,
                    "name": block_name,
                    "eligible": eligible,
                }
                flat_block_tree.append(new_entry)
                if block.has_children and not getattr(block, "has_dynamic_children", lambda: False)():
                    for child_id in block.children:
                        build_tree(block.runtime.get_block(child_id), ancestors=(ancestors + [new_entry]))

        root_block = self
        while root_block.parent:
            root_block = root_block.get_parent()
        root_block_id = get_block_id(root_block)
        root_entry = {
            "depth": 0,
            "id": root_block_id,
            "name": "All",
        }
        flat_block_tree.append(root_entry)

        for child_id in root_block.children:
            child_block = root_block.runtime.get_block(child_id)
            build_tree(child_block, [root_entry])

        html = loader.render_template(
            'templates/html/instructor_tool.html',
            {'block_choices': block_choices, 'block_tree': flat_block_tree}
        )
        fragment = Fragment(html)
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
        from instructor_task.models import ReportStore
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
        username = data.get('username', None)
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
        if not username:
            user_id = None
        else:
            user_id = user_service.get_anonymous_user_id(username, unicode(self.runtime.course_id))
            if user_id is None:
                self.raise_error(404, _("Could not find the specified username."))

        if not root_block_id:
            root_block_id = self.scope_ids.usage_id
            # Block ID not in workbench runtime.
            root_block_id = unicode(getattr(root_block_id, 'block_id', root_block_id))

        # Launch task
        from .tasks import export_data as export_data_task  # Import here since this is edX LMS specific
        self._delete_export()
        # Make sure we nail down our state before sending off an asynchronous task.
        self.save()
        async_result = export_data_task.delay(
            # course_id not available in workbench.
            unicode(getattr(self.runtime, 'course_id', 'course_id')),
            root_block_id,
            block_types,
            user_id,
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
        from .tasks import export_data as export_data_task  # Import here since this is edX LMS specific
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
