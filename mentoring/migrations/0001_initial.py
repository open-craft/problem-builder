# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Answer'
        db.create_table('mentoring_answer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('student_id', self.gf('django.db.models.fields.CharField')(max_length=20, db_index=True)),
            ('student_input', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('mentoring', ['Answer'])

        # Adding unique constraint on 'Answer', fields ['student_id', 'name']
        db.create_unique('mentoring_answer', ['student_id', 'name'])


    def backwards(self, orm):
        # Removing unique constraint on 'Answer', fields ['student_id', 'name']
        db.delete_unique('mentoring_answer', ['student_id', 'name'])

        # Deleting model 'Answer'
        db.delete_table('mentoring_answer')


    models = {
        'mentoring.answer': {
            'Meta': {'unique_together': "(('student_id', 'name'),)", 'object_name': 'Answer'},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'student_id': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'student_input': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        }
    }

    complete_apps = ['mentoring']