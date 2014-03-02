# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Answer.course_id'
        db.add_column('mentoring_answer', 'course_id',
                      self.gf('django.db.models.fields.CharField')(default='default', max_length=50, db_index=True),
                      keep_default=False)


        # Changing field 'Answer.student_id'
        db.alter_column('mentoring_answer', 'student_id', self.gf('django.db.models.fields.CharField')(max_length=32))

    def backwards(self, orm):
        # Deleting field 'Answer.course_id'
        db.delete_column('mentoring_answer', 'course_id')


        # Changing field 'Answer.student_id'
        db.alter_column('mentoring_answer', 'student_id', self.gf('django.db.models.fields.CharField')(max_length=20))

    models = {
        'mentoring.answer': {
            'Meta': {'unique_together': "(('student_id', 'name'),)", 'object_name': 'Answer'},
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