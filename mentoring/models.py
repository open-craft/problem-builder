# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Harvard
#
# Authors:
#          Xavier Antoviaque <xavier@antoviaque.org>
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

from django.db import models


# Classes ###########################################################

class Answer(models.Model):
    """
    Django model used to store AnswerBlock data that need to be shared
    and queried accross XBlock instances (workaround).
    """

    class Meta:
        app_label = 'mentoring'
        unique_together = (('student_id', 'course_id', 'name'),)

    name = models.CharField(max_length=50, db_index=True)
    student_id = models.CharField(max_length=32, db_index=True)
    course_id = models.CharField(max_length=50, db_index=True)
    student_input = models.TextField(blank=True, default='')
    created_on = models.DateTimeField('created on', auto_now_add=True)
    modified_on = models.DateTimeField('modified on', auto_now=True)

    def save(self, *args, **kwargs):
        # Force validation of max_length
        self.full_clean()
        super(Answer, self).save(*args, **kwargs)


class LightChild(models.Model):
    """
    Django model used to store LightChild student data that need to be shared and queried accross
    XBlock instances (workaround). Since this is temporary, `data` are stored in json.
    """

    class Meta:
        app_label = 'mentoring'
        unique_together = (('student_id', 'course_id', 'name'),)

    name = models.CharField(max_length=100, db_index=True)
    student_id = models.CharField(max_length=32, db_index=True)
    course_id = models.CharField(max_length=50, db_index=True)
    student_data = models.TextField(blank=True, default='')
    created_on = models.DateTimeField('created on', auto_now_add=True)
    modified_on = models.DateTimeField('modified on', auto_now=True)
