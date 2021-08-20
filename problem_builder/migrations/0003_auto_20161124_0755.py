from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problem_builder', '0002_auto_20160121_1525'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='course_key',
            field=models.CharField(default=None, max_length=255, null=True, db_index=True),
        ),
        migrations.AlterUniqueTogether(
            name='answer',
            unique_together={('student_id', 'course_key', 'name'), ('student_id', 'course_id', 'name')},
        ),
    ]
