from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50, db_index=True)),
                ('student_id', models.CharField(max_length=32, db_index=True)),
                ('course_id', models.CharField(max_length=50, db_index=True)),
                ('student_input', models.TextField(default='', blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('modified_on', models.DateTimeField(auto_now=True, verbose_name='modified on')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='answer',
            unique_together={('student_id', 'course_id', 'name')},
        ),
    ]
