from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Answer'
        db.create_table('problem_builder_answer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('student_id', self.gf('django.db.models.fields.CharField')(max_length=32, db_index=True)),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('student_input', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('problem_builder', ['Answer'])

        # Adding unique constraint on 'Answer', fields ['student_id', 'course_id', 'name']
        db.create_unique('problem_builder_answer', ['student_id', 'course_id', 'name'])

    def backwards(self, orm):
        # Removing unique constraint on 'Answer', fields ['student_id', 'course_id', 'name']
        db.delete_unique('problem_builder_answer', ['student_id', 'course_id', 'name'])

        # Deleting model 'Answer'
        db.delete_table('problem_builder_answer')

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
