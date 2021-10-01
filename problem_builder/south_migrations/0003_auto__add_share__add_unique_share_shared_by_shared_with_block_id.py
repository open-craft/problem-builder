from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Share'
        db.create_table('problem_builder_share', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('shared_by', self.gf('django.db.models.fields.related.ForeignKey')(
                related_name='problem_builder_shared_by', to=orm['auth.User']
            )),
            ('submission_uid', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('block_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('shared_with', self.gf('django.db.models.fields.related.ForeignKey')(
                related_name='problem_builder_shared_with', to=orm['auth.User']
            )),
            ('notified', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
        ))
        db.send_create_signal('problem_builder', ['Share'])

        # Adding unique constraint on 'Share', fields ['shared_by', 'shared_with', 'block_id']
        db.create_unique('problem_builder_share', ['shared_by_id', 'shared_with_id', 'block_id'])

    def backwards(self, orm):
        # Removing unique constraint on 'Share', fields ['shared_by', 'shared_with', 'block_id']
        db.delete_unique('problem_builder_share', ['shared_by_id', 'shared_with_id', 'block_id'])

        # Deleting model 'Share'
        db.delete_table('problem_builder_share')

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {
                'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'
            })
        },
        'auth.permission': {
            'Meta': {
                'ordering': "('content_type__app_label', 'content_type__model', 'codename')",
                'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'
            },
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {
                'to': "orm['contenttypes.ContentType']"
            }),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {
                'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'
            }),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {
                'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'
            }),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {
                'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)",
                'object_name': 'ContentType', 'db_table': "'django_content_type'"
            },
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'problem_builder.answer': {
            'Meta': {'unique_together': "(('student_id', 'course_id', 'name'),)", 'object_name': 'Answer'},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'student_id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'student_input': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        'problem_builder.share': {
            'Meta': {'unique_together': "(('shared_by', 'shared_with', 'block_id'),)", 'object_name': 'Share'},
            'block_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notified': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'shared_by': ('django.db.models.fields.related.ForeignKey', [], {
                'related_name': "'problem_builder_shared_by'", 'to': "orm['auth.User']"
            }),
            'shared_with': ('django.db.models.fields.related.ForeignKey', [], {
                'related_name': "'problem_builder_shared_with'", 'to': "orm['auth.User']"
            }),
            'submission_uid': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        }
    }

    complete_apps = ['problem_builder']
