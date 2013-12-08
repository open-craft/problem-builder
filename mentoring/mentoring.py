# -*- coding: utf-8 -*-

# Imports ###########################################################

import logging

from xblock.core import XBlock
from xblock.fields import Boolean, Scope, String
from xblock.fragment import Fragment

from .utils import load_resource, render_template, XBlockWithChildrenFragmentsMixin


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class MentoringBlock(XBlock, XBlockWithChildrenFragmentsMixin):
    """
    An XBlock providing mentoring capabilities

    Composed of text, answers input fields, and a set of multiple choice quizzes with advices. 
    A set of conditions on the provided answers and quizzes choices will determine if the
    student is a) provided mentoring advices and asked to alter his answer, or b) is given the
    ok to continue.
    """
    attempted = Boolean(help="Has the student attempted this mentoring step?", default=False, scope=Scope.user_state)
    completed = Boolean(help="Has the student completed this mentoring step?", default=False, scope=Scope.user_state)
    completed_message = String(help="Message to display upon completion", scope=Scope.content, default="")
    has_children = True

    @classmethod
    def parse_xml(cls, node, runtime, keys):
        block = runtime.construct_xblock_from_class(cls, keys)

        for child in node:
            if child.tag == 'message':
                if child.get('type') == 'completed':
                    block.completed_message = child.text
                else:
                    raise ValueError, u'Invalid value for message type: `{}`'.format(child.get('type'))
            else:
                block.runtime.add_node_as_child(block, child)

        for name, value in node.items():
            if name in block.fields:
                setattr(block, name, value)

        return block

    def student_view(self, context):
        fragment, named_children = self.get_children_fragment(context, view_name='mentoring_view')

        fragment.add_content(render_template('templates/html/mentoring.html', {
            'self': self,
            'named_children': named_children,
        }))
        fragment.add_css(load_resource('static/css/mentoring.css'))
        fragment.add_javascript(load_resource('static/js/vendor/underscore-min.js'))
        fragment.add_javascript(load_resource('static/js/mentoring.js'))

        fragment.add_resource(load_resource('templates/html/mentoring_progress.html').format(
                completed=self.runtime.resources_url('images/correct-icon.png')),
            "text/html")

        fragment.initialize_js('MentoringBlock')

        return fragment

    @XBlock.json_handler
    def submit(self, submissions, suffix=''):
        log.info(u'Received submissions: {}'.format(submissions))
        self.attempted = True

        submit_results = []
        completed = True
        for child_id in self.children:  # pylint: disable=E1101
            child = self.runtime.get_block(child_id)
            if child.name and child.name in submissions:
                submission = submissions[child.name]
                child_result = child.submit(submission)
                submit_results.append([child.name, child_result])
                child.save()
                completed = completed and child_result['completed']

        self.completed = bool(completed)
        if self.completed:
            message = self.completed_message
        else:
            message = ''

        return {
            'submitResults': submit_results,
            'completed': self.completed,
            'message': message,
        }

    def studio_view(self, context):
        return Fragment(u'Studio view body')

    @staticmethod
    def workbench_scenarios():
        """
        Sample scenarios which will be displayed in the workbench
        """
        return [
            ("001) Pre-goal brainstom",
                                  load_resource('templates/xml/001_pre_goal_brainstorm.xml')),
            ("002) Getting feedback",
                                  load_resource('templates/xml/002_getting_feedback.xml')),
            ("003) Reflecting on your feedback",
                                  load_resource('templates/xml/003_reflecting_on_feedback.xml')),
            ("004) Deciding on your improvement goal",
                                  load_resource('templates/xml/004_deciding_on_your_improvement_goal.xml')),
            ("005) Checking your improvement goal",
                                  load_resource('templates/xml/005_checking_your_improvement_goal.xml')),
            ("006) Past attempts at change",
                                  load_resource('templates/xml/006_past_attempts_at_change.xml')),
            ("007) Doing / not doing instead",
                                  load_resource('templates/xml/007_doing_not_doing_instead.xml')),
            ("008) Checking your doing / not doing instead",
                                  load_resource('templates/xml/008_checking_your_doing_not_doing_instead.xml')),
            ("009) Worry box",
                                  load_resource('templates/xml/009_worry_box.xml')),
            ("010) Hidden commitments",
                                  load_resource('templates/xml/010_hidden_commitments.xml')),
            ("011) Checking your hidden commitments",
                                  load_resource('templates/xml/011_checking_your_hidden_commitments.xml')),
            ("012) Your immune system",
                                  load_resource('templates/xml/012_your_immune_system.xml')),
            ("013) Checking the map",
                                  load_resource('templates/xml/013_checking_the_map.xml')),
            ("014) Big assumptions",
                                  load_resource('templates/xml/014_big_assumptions.xml')),
            ("015) Checking your big assumptions",
                                  load_resource('templates/xml/015_checking_your_big_assumptions.xml')),
            ("016) Revising your entire map",
                                  load_resource('templates/xml/016_revising_your_entire_map.xml')),
            ("017) Checking the entire map",
                                  load_resource('templates/xml/017_checking_the_entire_map.xml')),
            ("700) Change diary - Map",
                                  load_resource('templates/xml/700_change_diary_map.xml')),
            ("701) Change diary - Other fields",
                                  load_resource('templates/xml/701_change_diary_other_fields.xml')),
            ("800) Help on revising immunity to change maps",
                                  load_resource('templates/xml/800_help_on_revising_immunity_to_change_maps.xml')),
        ]
