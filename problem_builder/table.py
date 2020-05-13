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

# Imports ###########################################################

import errno
import json

import six
from django.contrib.auth.models import User
from xblock.core import XBlock
from xblock.exceptions import JsonHandlerError
from xblock.fields import Boolean, Scope, String
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import (StudioContainerXBlockMixin,
                                         StudioEditableXBlockMixin,
                                         XBlockWithPreviewMixin)

from problem_builder.answer import AnswerRecapBlock
from problem_builder.dashboard import ExportMixin
from problem_builder.models import Share
from problem_builder.sub_api import SubmittingXBlockMixin

# Globals ###########################################################


loader = ResourceLoader(__name__)


# Make '_' a no-op so we can scrape strings
def _(text):
    return text

# Classes ###########################################################


@XBlock.wants("user")
@XBlock.wants("submissions")
class MentoringTableBlock(
    StudioEditableXBlockMixin, SubmittingXBlockMixin, StudioContainerXBlockMixin, ExportMixin, XBlock,
    XBlockWithPreviewMixin
):
    """
    Table-type display of information from mentoring blocks

    Used to present summary of information entered by the students in mentoring blocks.
    Supports different types of formatting through the `type` parameter.
    """
    CATEGORY = 'pb-table'
    STUDIO_LABEL = _(u"Answer Recap Table")

    display_name = String(
        display_name=_("Display name"),
        help=_("Title of the table"),
        default=_("Answers Table"),
        scope=Scope.settings
    )
    type = String(
        display_name=_("Special Mode"),
        help=_("Variant of the table that will display a specific background image."),
        scope=Scope.content,
        default='',
        values=[
            {"display_name": "Normal", "value": ""},
            {"display_name": "Immunity Map Assumptions", "value": "immunity-map-assumptions"},
            {"display_name": "Immunity Map", "value": "immunity-map"},
        ],
    )
    editable_fields = ("type", "allow_download")
    allow_download = Boolean(
        display_name=_("Allow Download"),
        help=_("Allow students to download a copy of the table for themselves."),
        default=False,
        scope=Scope.content
    )
    allow_sharing = Boolean(
        display_name=_("Allow Sharing"),
        help=_("Allow students to share their results with other students."),
        default=True,
        scope=Scope.content
    )
    has_children = True

    css_path = 'public/css/mentoring-table.css'
    js_path = 'public/js/review_blocks.js'

    @XBlock.json_handler
    def table_render(self, data, suffix=''):
        context = {}
        header_values = []
        content_values = []
        target_username = data.get('target_username')
        try:
            if target_username and target_username != self.current_user_key:
                share = Share.objects.get(
                    shared_by__username=target_username, shared_with__username=self.current_user_key,
                    block_id=self.block_id,
                )
                context['student_submissions_key'] = share.submission_uid
        except Share.DoesNotExist:
            raise JsonHandlerError(403, _("You are not permitted to view this student's table."))

        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            # Child should be an instance of MentoringTableColumn
            header = child.header
            # Make sure /jump_to_id/ URLs are expanded correctly
            if getattr(self.runtime, 'replace_jump_to_id_urls', None):
                header = self.runtime.replace_jump_to_id_urls(header)
            header_values.append(header)
            child_frag = child.render('mentoring_view', context)
            content_values.append(child_frag.content)
        context['header_values'] = header_values if any(header_values) else None
        context['content_values'] = content_values
        html = loader.render_django_template('templates/html/mentoring-table.html', context)
        return {'content': html}

    @property
    def current_user_key(self):
        user = self.runtime.service(self, 'user').get_current_user()
        # We may be in the SDK, in which case the username may not really be available.
        return user.opt_attrs.get('edx-platform.username', 'username')

    @XBlock.json_handler
    def get_shared_list(self, data, suffix=''):
        context = {'shared_with': Share.objects.filter(
            shared_by__username=self.current_user_key,
            block_id=self.block_id,
        ).values_list('shared_with__username', flat=True)
        }
        return {
            'content': loader.render_django_template('templates/html/mentoring-table-shared-list.html', context)
        }

    @XBlock.json_handler
    def clear_notification(self, data, suffix=''):
        """
        Clear out notifications for users who shared with this user on the last page load.
        Since more users might share with them while they're viewing the page, only remove the ones
        that they had at the time.
        """
        usernames = data.get('usernames')
        if not usernames:
            raise JsonHandlerError(400, "No usernames sent.")
        try:
            isinstance(usernames, list)
        except ValueError:
            raise JsonHandlerError(400, "Usernames must be a list.")
        Share.objects.filter(
            shared_with__username=self.current_user_key,
            shared_by__username__in=usernames,
            block_id=self.block_id,
        ).update(
            notified=True
        )

    @property
    def block_id(self):
        usage_id = self.scope_ids.usage_id
        if isinstance(usage_id, six.string_types):
            return usage_id
        try:
            return six.text_type(usage_id.replace(branch=None, version_guid=None))
        except AttributeError:
            pass
        return six.text_type(usage_id)

    @XBlock.json_handler
    def share_results(self, data, suffix=''):
        target_usernames = data.get('usernames')
        target_usernames = [username.strip().lower() for username in target_usernames if username.strip()]
        current_user = User.objects.get(username=self.current_user_key)

        failed_users = []
        if not target_usernames:
            raise JsonHandlerError(400, _('Usernames not provided.'))
        for target_username in target_usernames:
            try:
                target_user = User.objects.get(username=target_username)
            except User.DoesNotExist:
                failed_users.append(target_username)
                continue
            if current_user == target_user:
                continue
            try:
                Share.objects.get(shared_by=current_user, shared_with=target_user, block_id=self.block_id)
            except Share.DoesNotExist:
                Share(
                    shared_by=current_user, submission_uid=self.runtime.anonymous_student_id, shared_with=target_user,
                    block_id=self.block_id,
                ).save()

        if failed_users:
            raise JsonHandlerError(
                400,
                _('Some users could not be shared with. Please check these usernames: {}').format(
                    ', '.join(failed_users)
                )
            )
        return {}

    @XBlock.json_handler
    def remove_share(self, data, suffix=''):
        target_username = data.get('username')
        if not target_username:
            raise JsonHandlerError(400, _('Username not provided.'))
        Share.objects.filter(
            shared_by__username=self.current_user_key,
            shared_with__username=target_username,
            block_id=self.block_id,
        ).delete()
        return {'message': _('Removed successfully.')}

    def student_view(self, context):
        context = context.copy() if context else {}
        fragment = Fragment()

        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            # Child should be an instance of MentoringTableColumn
            child_frag = child.render('mentoring_view', context)
            fragment.add_frag_resources(child_frag)

        context['allow_sharing'] = self.allow_sharing
        context['allow_download'] = self.allow_download
        user_service = self.runtime.service(self, 'user')
        if user_service:
            context['view_options'] = Share.objects.filter(
                shared_with__username=self.current_user_key,
                block_id=self.block_id,
            ).values_list('shared_by__username', flat=True)
            context['username'] = self.current_user_key
            share_notifications = Share.objects.filter(
                shared_with__username=self.current_user_key,
                notified=False, block_id=self.block_id,
            ).values_list('shared_by__username', flat=True)
            context['share_notifications'] = share_notifications and json.dumps(list(share_notifications))

        if self.type:
            # Load an optional background image:
            context['bg_image_url'] = self.runtime.local_resource_url(self, 'public/img/{}-bg.png'.format(self.type))
            # Load an optional description for the background image, for accessibility
            try:
                context['bg_image_description'] = loader.load_unicode('static/text/table-{}.txt'.format(self.type))
            except IOError as e:
                if e.errno == errno.ENOENT:
                    pass
                else:
                    raise

        report_template = loader.render_django_template('templates/html/mentoring-table-report.html', {
            'title': self.display_name,
            'css': loader.load_unicode(AnswerRecapBlock.css_path) + loader.load_unicode(self.css_path),
            'student_name': self._get_user_full_name(),
            'course_name': self._get_course_name(),
        })

        fragment.add_content(loader.render_django_template('templates/html/mentoring-table-container.html', context))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/mentoring-table.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/vendor/jquery-shorten.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, self.js_path))
        fragment.initialize_js(
            'MentoringTableBlock', {
                'reportContentSelector': '.mentoring-table-container',
                'reportTemplate': report_template,
            }
        )

        return fragment

    def mentoring_view(self, context):
        # Allow to render within mentoring blocks, or outside
        return self.student_view(context)

    def author_edit_view(self, context):
        """
        Add some HTML to the author view that allows authors to add choices and tips.
        """
        fragment = super(MentoringTableBlock, self).author_edit_view(context)
        fragment.add_content(loader.render_django_template('templates/html/mentoring-table-add-button.html', {}))
        # Share styles with the questionnaire edit CSS:
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/questionnaire-edit.css'))
        return fragment


class MentoringTableColumn(StudioEditableXBlockMixin, StudioContainerXBlockMixin, XBlock):
    """
    A column in a mentoring table. Has a header and can contain HTML and AnswerRecapBlocks.
    """
    display_name = String(display_name=_("Display Name"), default="Column")
    header = String(
        display_name=_("Header"),
        help=_("Header of this column"),
        default="",
        scope=Scope.content,
        multiline_editor="html",
    )
    editable_fields = ("header", )
    has_children = True

    def mentoring_view(self, context=None):
        """ Render this XBlock within a mentoring block. """
        context = context.copy() if context else {}
        fragment = Fragment()
        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            if child.scope_ids.block_type == "html":
                # HTML block current doesn't support "mentoring_view" and if "student_view" is used, it gets wrapped
                # with HTML we don't want. So just grab its HTML directly.
                child_frag = Fragment(child.data)
            else:
                child_frag = child.render('mentoring_view', context)
            fragment.add_content(child_frag.content)
            fragment.add_frag_resources(child_frag)
        return fragment

    def author_preview_view(self, context):
        return self.mentoring_view(context)

    def student_view(self, context=None):
        """ Normal view of this XBlock, identical to mentoring_view """
        return self.mentoring_view(context)

    def author_edit_view(self, context):
        """
        Add some HTML to the author view that allows authors to add choices and tips.
        """
        fragment = super(MentoringTableColumn, self).author_edit_view(context)
        fragment.content = u"<div style=\"font-weight: bold;\">{}</div>".format(self.header) + fragment.content
        fragment.add_content(loader.render_django_template('templates/html/mentoring-column-add-button.html', {}))
        # Share styles with the questionnaire edit CSS:
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/questionnaire-edit.css'))
        return fragment
