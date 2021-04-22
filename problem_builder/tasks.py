"""
Celery task for CSV student answer export.
"""
import time

import six
from django.contrib.auth.models import User
from django.db.models import F

from celery.task import task
from celery.utils.log import get_task_logger
from lms.djangoapps.instructor_task.models import ReportStore
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from problem_builder.answer import AnswerBlock
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from .mcq import MCQBlock, RatingBlock
from .mrq import MRQBlock
from .questionnaire import QuestionnaireAbstractBlock
from .sub_api import sub_api

logger = get_task_logger(__name__)


@task()
def export_data(course_id, source_block_id_str, block_types, user_ids, match_string):
    """
    Exports student answers to all supported questions to a CSV file.
    """
    start_timestamp = time.time()

    logger.debug("Beginning data export")
    try:
        course_key = CourseKey.from_string(course_id)
        usage_key = UsageKey.from_string(source_block_id_str)
    except InvalidKeyError:
        raise ValueError("Could not find the specified Block ID.")

    src_block = modulestore().get_item(usage_key)
    course_key_str = six.text_type(course_key)
    type_map = {cls.__name__: cls for cls in [MCQBlock, MRQBlock, RatingBlock, AnswerBlock]}

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

    scan_for_blocks(src_block)

    # Define the header row of our CSV:
    rows = []
    rows.append(
        ["Section", "Subsection", "Unit", "Type", "Question", "Answer", "Username", "User ID", "User E-mail"]
    )

    # Collect results for each block in blocks_to_include
    for block in blocks_to_include:
        if not user_ids:
            results = _extract_data(course_key_str, block, None, match_string)
            rows += results
        else:
            for user_id in user_ids:
                results = _extract_data(course_key_str, block, user_id, match_string)
                rows += results

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
        "display_data": [] if len(rows) == 1 else rows[1:1001]  # Limit to preview of 1000 items
    }


def _extract_data(course_key_str, block, user_id, match_string):
    """
    Extract results for `block`.
    """
    rows = []

    # Extract info for "Section", "Subsection", and "Unit" columns
    section_name, subsection_name, unit_name = _get_context(block)

    # Extract info for "Type" column
    block_type = _get_type(block)

    # Extract info for "Question" column
    block_question = _get_question(block)

    # Extract info for "Answer" and "Username" columns
    # - Get all of the most recent student submissions for this block:
    submissions = tuple(_get_submissions(course_key_str, block, user_id))

    # If the student ID key doesn't exist, we're dealing with a single student and know the ID already.
    student_ids = [submission.get('student_id', user_id) for submission in submissions]
    users = get_users_by_anonymous_ids(student_ids)

    # - For each submission, look up student's username, email and answer:
    answer_cache = {}
    for submission in submissions:
        student_id = submission.get('student_id', user_id)
        username, _user_id, user_email = users.get(
            student_id,
            (student_id, 'N/A', 'N/A')
        )
        answer = _get_answer(block, submission, answer_cache)

        # Short-circuit if answer does not match search criteria
        if not match_string.lower() in answer.lower():
            continue

        rows.append([
            section_name,
            subsection_name,
            unit_name,
            block_type,
            block_question,
            answer,
            username,
            _user_id,
            user_email
        ])

    return rows


def _get_context(block):
    """
    Return section, subsection, and unit names for `block`.
    """
    block_names_by_type = {}
    block_iter = block
    while block_iter:
        block_iter_type = block_iter.scope_ids.block_type
        block_names_by_type[block_iter_type] = block_iter.display_name_with_default
        block_iter = block_iter.get_parent() if block_iter.parent else None
    section_name = block_names_by_type.get('chapter', '')
    subsection_name = block_names_by_type.get('sequential', '')
    unit_name = block_names_by_type.get('vertical', '')
    return section_name, subsection_name, unit_name


def _get_type(block):
    """
    Return type of `block`.
    """
    return block.scope_ids.block_type


def _get_question(block):
    """
    Return question for `block`; default to question ID if `question` is not set.
    """
    return block.question or block.name


def _get_submissions(course_key_str, block, user_id):
    """
    Return submissions for `block`.
    """
    # Load the actual student submissions for `block`.
    # Note this requires one giant query that retrieves all student submissions for `block` at once.
    block_id = six.text_type(block.scope_ids.usage_id.replace(branch=None, version_guid=None))
    block_type = _get_type(block)
    if block_type == 'pb-answer':
        block_id = block.name  # item_id of Long Answer submission matches question ID and not block ID
    if not user_id:
        return sub_api.get_all_submissions(course_key_str, block_id, block_type)
    else:
        student_dict = {
            'student_id': user_id,
            'item_id': block_id,
            'course_id': course_key_str,
            'item_type': block_type,
        }
        return sub_api.get_submissions(student_dict, limit=1)


def get_users_by_anonymous_ids(anonymous_ids):
    """
    Return users by anonymous_ids using AnonymousUserId lookup table.
    """
    if not anonymous_ids:
        return None

    users = User.objects.filter(
        anonymoususerid__anonymous_user_id__in=anonymous_ids
    ).annotate(
        anonymous_user_id=F('anonymoususerid__anonymous_user_id')
    ).values(
        'anonymous_user_id', 'username', 'id', 'email'
    ).iterator()

    return {
        user['anonymous_user_id']: (user['username'], user['id'], user['email']) for user in users
    }


def _get_answer(block, submission, answer_cache):
    """
    Return answer associated with `submission` to `block`.

    `answer_cache` is a dict that is reset for each block.
    """
    answer = submission['answer']
    if isinstance(block, QuestionnaireAbstractBlock):
        # Convert from answer ID to answer label
        if answer not in answer_cache:
            answer_cache[answer] = block.get_submission_display(answer)
        return answer_cache[answer]
    return answer
