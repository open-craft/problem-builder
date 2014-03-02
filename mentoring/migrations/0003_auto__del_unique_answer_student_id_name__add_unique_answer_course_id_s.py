# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Answer', fields ['student_id', 'name']
        db.delete_unique('mentoring_answer', ['student_id', 'name'])

        # Adding unique constraint on 'Answer', fields ['course_id', 'student_id', 'name']
        db.create_unique('mentoring_answer', ['course_id', 'student_id', 'name'])


    def backwards(self, orm):
        # Removing unique constraint on 'Answer', fields ['course_id', 'student_id', 'name']
        db.delete_unique('mentoring_answer', ['course_id', 'student_id', 'name'])

        # Adding unique constraint on 'Answer', fields ['student_id', 'name']
        db.create_unique('mentoring_answer', ['student_id', 'name'])


    models = {
        'mentoring.answer': {
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

    complete_apps = ['mentoring']