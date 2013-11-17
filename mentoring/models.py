from django.db import models

class Answer(models.Model):
    class Meta:
        app_label = 'mentoring'

    text = models.CharField(max_length=2000)
    pub_date = models.DateTimeField('date published', auto_now_add=True)
