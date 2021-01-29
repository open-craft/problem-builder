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

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete

from .platform_dependencies import AnonymousUserId


# Classes ###########################################################

class Answer(models.Model):
    """
    Django model used to store AnswerBlock data that need to be shared
    and queried accross XBlock instances (workaround).

    TODO: Deprecate this and move to edx-submissions
    """

    class Meta:
        # Since problem_builder isn't added to INSTALLED_APPS until it's imported,
        # specify the app_label here.
        app_label = 'problem_builder'
        unique_together = (
            ('student_id', 'course_key', 'name'),
        )

    name = models.CharField(max_length=50, db_index=True)
    student_id = models.CharField(max_length=50, db_index=True)
    course_key = models.CharField(max_length=255, db_index=True)
    student_input = models.TextField(blank=True, default=u'')
    created_on = models.DateTimeField(u'created on', auto_now_add=True)
    modified_on = models.DateTimeField(u'modified on', auto_now=True)

    def save(self, *args, **kwargs):
        # Force validation of max_length
        self.full_clean()
        super(Answer, self).save(*args, **kwargs)


class Share(models.Model):
    """
    The XBlock User Service does not permit XBlocks instantiated with non-staff users
    to query for arbitrary anonymous user IDs. In order to make sharing work, we have
    to store them here.
    """
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='problem_builder_shared_by')
    submission_uid = models.CharField(max_length=32)
    block_id = models.CharField(max_length=255, db_index=True)
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='problem_builder_shared_with')
    notified = models.BooleanField(default=False, db_index=True)

    class Meta:
        # Since problem_builder isn't added to INSTALLED_APPS until it's imported,
        # specify the app_label here.
        app_label = 'problem_builder'
        unique_together = (('shared_by', 'shared_with', 'block_id'),)


# Signals ###########################################################

def delete_anonymous_user_answers(sender, **kwargs):
    """
    Delete Answer records when an AnonymousUserId is deleted.
    """
    instance = kwargs['instance']
    Answer.objects.filter(student_id=instance.anonymous_user_id).delete()


if AnonymousUserId:
    pre_delete.connect(delete_anonymous_user_answers, sender=AnonymousUserId)
