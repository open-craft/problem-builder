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
Data Export: An XBlock for instructors to export student answers from a course.

All processing is done offline.
"""
import json
from xblock.core import XBlock
from xblock.fields import Scope, String, Dict
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader

loader = ResourceLoader(__name__)


@XBlock.wants('user')
class DataExportBlock(XBlock):
    """
    DataExportBlock: An XBlock for instructors to export student answers from a course.

    All processing is done offline.
    """
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
    has_author_view = True

    @property
    def display_name_with_default(self):
        return "Data Export"

    def author_view(self, context=None):
        """ Studio View """
        # Warn the user that this block will only work from the LMS. (Since the CMS uses
        # different celery queues; our task listener is waiting for tasks on the LMS queue)
        return Fragment(u"<p>Data Export Block</p><p>This block only works from the LMS.</p>")

    def studio_view(self, context=None):
        """ 'Edit' form view in Studio """
        return Fragment(u"<p>This block has no configuration options.</p>")

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
        self.active_export_task_id = ""
        if task_result.successful():
            if isinstance(task_result.result, dict) and not task_result.result.get('error'):
                self.last_export_result = task_result.result
            else:
                self.last_export_result = {"error": u"Unexpected result: {}".format(repr(task_result.result))}
        else:
            self.last_export_result = {"error": unicode(task_result.result)}

    def student_view(self, context=None):
        """ Normal View """
        # TODO: Verify instructor permissions
        # Check if any pending export has finished:
        self.check_pending_export()
        # Render our HTML:
        html = loader.render_template('templates/html/data_export.html', {
            'export_pending': bool(self.active_export_task_id),
            'last_export_result': self.last_export_result,
            'download_url': self.download_url_for_last_report,
        })
        fragment = Fragment(html)
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/data_export.js'))
        fragment.initialize_js('DataExportBlock')
        return fragment

    @property
    def download_url_for_last_report(self):
        """ Get the URL for the last report, if any """
        # Unfortunately this is a bit inefficient due to the ReportStore API
        if not self.last_export_result or self.last_export_result["error"] is not None:
            return None
        from instructor_task.models import ReportStore
        report_store = ReportStore.from_config()
        course_key = self.scope_ids.usage_id.course_key
        return dict(report_store.links_for(course_key)).get(self.last_export_result["report_filename"], None)

    @XBlock.json_handler
    def delete_export(self, request, suffix=''):
        self._delete_export()
        return {"result": "ok"}

    def _delete_export(self):
        self.last_export_result = None
        self.active_export_task_id = ""

    @XBlock.json_handler
    def start_export(self, request, suffix=''):
        """ Start a new asynchronous export """
        from .tasks import export_data as export_data_task  # Import here since this is edX LMS specific
        # TODO: Verify instructor permissions
        self._delete_export()
        async_result = export_data_task.delay(unicode(self.scope_ids.usage_id), self.get_user_id())
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
        return {"result": "started"}

    def get_user_id(self):
        """
        Get the ID of the current user.
        """
        user_service = self.runtime.service(self, 'user')
        if user_service:
            # May be None when creating bok choy test fixtures
            user_id = user_service.get_current_user().opt_attrs.get('edx-platform.user_id', None)
        else:
            user_id = None
        return user_id
