"""
Celery task for CSV student answer export.
"""
import time

from celery.task import task
from celery.utils.log import get_task_logger
from instructor_task.models import ReportStore
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey, CourseKey
from student.models import user_by_anonymous_id
from submissions.models import StudentItem
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from .mcq import MCQBlock, RatingBlock
from problem_builder import AnswerBlock
from .sub_api import sub_api

logger = get_task_logger(__name__)


@task()
def export_data(course_id, source_block_id_str, block_types, user_id, match_string, get_root=True):
    """
    Exports student answers to all MCQ questions to a CSV file.
    """
    start_timestamp = time.time()

    logger.debug("Beginning data export")
    try:
        course_key = CourseKey.from_string(course_id)
        src_block = modulestore().get_items(course_key, qualifiers={'name': source_block_id_str}, depth=0)[0]
        if src_block is None:
            raise InvalidKeyError
    except InvalidKeyError:
        raise ValueError("Could not find the specified Block ID.")
    course_key_str = unicode(course_key)

    root = src_block
    if get_root:
        # Get the root block for the course.
        while root.parent:
            root = root.get_parent()

    type_map = {cls.__name__: cls for cls in [MCQBlock, RatingBlock, AnswerBlock]}

    if not block_types:
        block_types = tuple(type_map.values())
    else:
        block_types = tuple(type_map[class_name] for class_name in block_types)

    # Build an ordered list of blocks to include in the export
    blocks_to_include = []

    def scan_for_blocks(block):
        """ Recursively scan the course tree for blocks of interest """
        if isinstance(block, block_types):
            blocks_to_include.append(block)
        elif block.has_children:
            for child_id in block.children:
                try:
                    scan_for_blocks(block.runtime.get_block(child_id))
                except ItemNotFoundError:
                    # Blocks may refer to missing children. Don't break in this case.
                    pass

    scan_for_blocks(root)

    # Define the header rows of our CSV:
    rows = []
    rows.append(["Section", "Subsection", "Unit", "Type", "Question", "Answer", "Username"])

    # Load the actual student submissions for each block in blocks_to_include.
    # Note this requires one giant query per block (all student submissions for each block, one block at a time)
    for block in blocks_to_include:
        # Get all of the most recent student submissions for this block:
        block_id = unicode(block.scope_ids.usage_id.replace(branch=None, version_guid=None))
        block_type = block.scope_ids.block_type
        if not user_id:
            submissions = sub_api.get_all_submissions(course_key_str, block_id, block_type)
        else:
            student_dict = {
                'student_id': user_id,
                'item_id': block_id,
                'course_id': course_key_str,
                'item_type': block_type,
            }
            submissions = sub_api.get_submissions(student_dict, limit=1)

        for submission in submissions:
            # If the student ID key doesn't exist, we're dealing with a single student and know the ID already.
            student_id = submission.get('student_id', user_id)

            # Extract data for display
            # "row" will be None if answer does not match "match_string"
            row = _extract_data_for_display(submission, student_id, block_type, match_string)
            if row:
                rows.append(row)

    # Generate the CSV:
    filename = u"pb-data-export-{}.csv".format(time.strftime("%Y-%m-%d-%H%M%S", time.gmtime(start_timestamp)))
    report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
    report_store.store_rows(course_key, filename, rows)

    generation_time_s = time.time() - start_timestamp
    logger.debug("Done data export - took {} seconds".format(generation_time_s))

    return {
        "error": None,
        "report_filename": filename,
        "start_timestamp": start_timestamp,
        "generation_time_s": generation_time_s,
        "display_data": [] if len(rows) == 1 else rows[1:]
    }


def _extract_data_for_display(submission, student_id, block_type, match_string):
    """
    Extract data that will be displayed on Student Answers Dashboard
    from `submission`.
    """

    # Username
    user = user_by_anonymous_id(student_id)
    username = user.username

    # Question
    student_item = StudentItem.objects.get(pk=submission['student_item'])

    block_key = UsageKey.from_string(student_item.item_id)
    block = modulestore().get_item(block_key)

    # Answer
    answer = submission['answer']

    try:
        choices = block.children
    except AttributeError:
        pass
    else:
        for choice in choices:
            choice_block = modulestore().get_item(choice)
            if choice_block.value == answer:
                answer = choice_block.content
                break

    # Short-circuit if answer does not match search criteria
    if not match_string.lower() in answer.lower():
        return

    # Unit
    mentoring_block = modulestore().get_item(block.parent)
    unit = modulestore().get_item(mentoring_block.parent)

    # Subsection
    subsection = modulestore().get_item(unit.parent)

    # Section
    section = modulestore().get_item(subsection.parent)

    return [
        section.display_name,
        subsection.display_name,
        unit.display_name,
        block_type,
        block.question,
        answer,
        username
    ]
