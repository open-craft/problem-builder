from django.db import models

class Answer(models.Model):
    class Meta:
        app_label = 'mentoring'
        unique_together = (('student_id', 'name'),)

    name = models.CharField(max_length=20, db_index=True)
    student_id = models.CharField(max_length=20, db_index=True)
    student_input = models.CharField(max_length=10000, blank=True, default='')
    created_on = models.DateTimeField('created on', auto_now_add=True)
    modified_on = models.DateTimeField('modified on', auto_now=True)
