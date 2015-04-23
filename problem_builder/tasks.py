"""
This file contains celery tasks for contentstore views
"""
import datetime
from celery.task import task
from celery.utils.log import get_task_logger

from opaque_keys.edx.keys import UsageKey
from xmodule.modulestore.django import modulestore

logger = get_task_logger(__name__)


@task()
def export_data(source_block_id_str, user_id):
    """
    Reruns a course in a new celery task.
    """
    report_date = datetime.datetime.now()

    logger.debug("Beginning data export")

    block_key = UsageKey.from_string(source_block_id_str)
    block = modulestore().get_item(block_key)

    root = block
    while root.parent:
        root = root.get_parent()

    course_name = root.display_name

    import time
    time.sleep(5)

    generation_time_s = (datetime.datetime.now() - report_date).total_seconds()
    logger.debug("Done data export - took {} seconds".format(generation_time_s))

    return {
        "error": None,
        "example": course_name,
        "report_date": report_date.isoformat(),
        "generation_time_s": generation_time_s,
    }
