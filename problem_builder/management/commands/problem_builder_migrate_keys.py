"""
Command to copy content of Answer.course_id to Answer.course_key.
"""

import time

from django.core.management.base import BaseCommand
from django.db.models import F, Q

from problem_builder.models import Answer


class Command(BaseCommand):
    """
    Copy content of the deprecated Answer.course_id column into
    Answer.course_key in batches.  The batch size and sleep time between
    batches are configurable.
    """
    help = 'Copy content of the deprecated Answer.course_id column to Answer.course_key in batches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            help='The size of each batch of records to copy (default: 5000).',
            type=int,
            default=5000,
        )
        parser.add_argument(
            '--offset',
            help='The lowest primary key to copy (default: 0)',
            type=int,
            default=0,
        )
        parser.add_argument(
            '--sleep',
            help='Number of seconds to sleep before processing the next batch (default: 1).',
            type=int,
            default=1,
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        sleep_time = options['sleep']
        offset = options['offset']
        max_pk = Answer.objects.order_by('-pk')[0].pk
        batch_start = offset
        batch_stop = batch_start + batch_size
        self.stdout.write(
            "Copying Answer.course_id field into Answer.course_key in batches of at most {}".format(
                batch_size
            )
        )
        while batch_start <= max_pk:

            queryset = Answer.objects.filter(
                pk__gte=batch_start,
                pk__lt=batch_stop,
            ).filter(
                Q(course_key__isnull=True) | Q(course_key='')
            )
            queryset.update(course_key=F('course_id'))
            self.stdout.write(
                "Processed Answers through pk: {}, max pk: {}".format(batch_stop, max_pk)
            )
            if batch_stop < max_pk:
                time.sleep(sleep_time)
            batch_start = batch_stop
            batch_stop += batch_size

        self.stdout.write("Successfully copied Answer.course_id into Answer.course_key")
