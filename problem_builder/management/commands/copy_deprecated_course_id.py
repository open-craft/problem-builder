import time

from django.core.management.base import BaseCommand

from problem_builder.models import Answer


class Command(BaseCommand):
    """
    Copy content of the deprecated Answer.course_id column into Answer.course_key in batches.
    The batch size and sleep time between batches are configurable.
    """
    help = 'Copy content of the deprecated Answer.course_id column into Answer.course_key in batches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            help='The size of each batch of records to copy (default: 5000).',
            type=int,
            default=5000,
        )
        parser.add_argument(
            '--sleep',
            help='Number of seconds to sleep before processing the next batch (default: 5).',
            type=int,
            default=5
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        sleep_time = options['sleep']
        queryset = Answer.objects.filter(course_key__isnull=True)

        self.stdout.write(
            "Copying Answer.course_id field into Answer.course_key in batches of {}".format(batch_size)
        )

        idx = 0
        while True:
            idx += 1
            batch = queryset[:batch_size]
            if not batch:
                break
            for answer in batch:
                answer.course_key = answer.course_id
                answer.save()
            self.stdout.write("Processed batch {}".format(idx))
            time.sleep(sleep_time)

        self.stdout.write("Successfully copied Answer.course_id into Answer.course_key")
