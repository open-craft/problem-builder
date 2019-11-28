# -*- coding: utf-8 -*-
from django.db.utils import DatabaseError

from south.db import db
from south.v2 import DataMigration


class Migration(DataMigration):

    def forwards(self, orm):
        """
        Copy student data from old table to the new one.

        Problem Builder stores student answers in 'problem_builder_answer'.
        However earlier versions [may have] used 'mentoring_answer'.
        If a 'mentoring' app is currently installed on this instance, copy the student data over
        to the new table in case it is being used.
        """
        try:
            db.execute(
                'INSERT INTO problem_builder_answer ('
                'name, student_id, course_id, student_input, created_on, modified_on '
                ') SELECT '
                'name, student_id, course_id, student_input, created_on, modified_on '
                'FROM mentoring_answer'
            )
        except DatabaseError:  # Would like to just catch 'Table does not exist' but can't do that in a db-agnostic way
            print(" - Seems like mentoring_answer does not exist. No data migration needed.")

    def backwards(self, orm):
        raise RuntimeError("Cannot safely reverse this migration.")

    models = {
        'problem_builder.answer': {
            'Meta': {'unique_together': "(('student_id', 'course_id', 'name'),)", 'object_name': 'Answer'},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'student_id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'student_input': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        }
    }

    complete_apps = ['problem_builder']
    symmetrical = True
