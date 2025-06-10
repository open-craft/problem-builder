#
# Copyright (c) 2014-2015 Harvard, edX & OpenCraft
#
# This software's license gives you freedom; you can copy, convey,
# propagate, redistribute and/or modify this program under the terms of
# the GNU Affero General Public License (AGPL) as published by the Free
# Software Foundation (FSF), either version 3 of the License, or (at your
# option) any later version of the AGPL published by the FSF.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program in a file in the toplevel directory called
# "AGPLv3".  If not, see <http://www.gnu.org/licenses/>.
#

# Imports ###########################################################

import os
import re
import sys

from setuptools import find_packages, setup


def get_version(*file_paths):
    """
    Extract the version string from the file.

    Input:
     - file_paths: relative path fragments to file with
                   version string
    """
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename, encoding="utf8").read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


def load_requirements(*requirements_paths):
    """
    Load all requirements from the specified requirements files.

    Requirements will include any constraints from files specified
    with -c in the requirements files.
    Returns a list of requirement strings.
    """
    requirements = {}
    constraint_files = set()

    # groups "pkg<=x.y.z,..." into ("pkg", "<=x.y.z,...")
    requirement_line_regex = re.compile(r"([a-zA-Z0-9-_.]+)([<>=][^#\s]+)?")

    def add_version_constraint_or_raise(current_line, current_requirements, add_if_not_present):
        regex_match = requirement_line_regex.match(current_line)
        if regex_match:
            package = regex_match.group(1)
            version_constraints = regex_match.group(2)
            existing_version_constraints = current_requirements.get(package, None)
            # fine to add constraints to an unconstrained package,
            # raise an error if there are already constraints in place
            if existing_version_constraints and existing_version_constraints != version_constraints:
                raise BaseException(
                    f'Multiple constraint definitions found for {package}:'
                    f' "{existing_version_constraints}" and "{version_constraints}".'
                    f'Combine constraints into one location with {package}'
                    f'{existing_version_constraints},{version_constraints}.'
                )
            if add_if_not_present or package in current_requirements:
                current_requirements[package] = version_constraints

    # read requirements from .in
    # store the path to any constraint files that are pulled in
    for path in requirements_paths:
        with open(path) as reqs:
            for line in reqs:
                if is_requirement(line):
                    add_version_constraint_or_raise(line, requirements, True)
                if line and line.startswith('-c') and not line.startswith('-c http'):
                    constraint_files.add(os.path.dirname(path) + '/' + line.split('#')[0].replace('-c', '').strip())

    # process constraint files: add constraints to existing requirements
    for constraint_file in constraint_files:
        with open(constraint_file) as reader:
            for line in reader:
                if is_requirement(line):
                    add_version_constraint_or_raise(line, requirements, False)

    # process back into list of pkg><=constraints strings
    constrained_requirements = [f'{pkg}{version or ""}' for (pkg, version) in sorted(requirements.items())]
    return constrained_requirements


def is_requirement(line):
    """
    Return True if the requirement line is a package requirement.

    Returns:
        bool: True if the line is not blank, a comment,
        a URL, or an included file
    """
    return line and line.strip() and not line.startswith(("-r", "#", "-e", "git+", "-c"))


def package_data(pkg, roots):
    """Generic function to find package_data.

    All of the files under each of the `roots` will be declared as package
    data for package `pkg`.

    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


VERSION = get_version('problem_builder', '__init__.py')

if sys.argv[-1] == 'tag':
    print("Tagging the version on github:")
    os.system("git tag -a %s -m 'version %s'" % (VERSION, VERSION))
    os.system("git push --tags")
    sys.exit()

README = open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding="utf8").read()

BLOCKS = [
    'problem-builder = problem_builder.mentoring:MentoringBlock',
    'step-builder = problem_builder.mentoring:MentoringWithExplicitStepsBlock',
    'sb-step = problem_builder.step:MentoringStepBlock',
    'sb-review-step = problem_builder.step_review:ReviewStepBlock',
    'sb-conditional-message = problem_builder.step_review:ConditionalMessageBlock',
    'sb-review-score = problem_builder.step_review:ScoreSummaryBlock',
    'sb-review-per-question-feedback = problem_builder.step_review:PerQuestionFeedbackBlock',

    'sb-plot = problem_builder.plot:PlotBlock',
    'sb-plot-overlay = problem_builder.plot:PlotOverlayBlock',

    'pb-table = problem_builder.table:MentoringTableBlock',
    'pb-column = problem_builder.table:MentoringTableColumn',
    'pb-answer = problem_builder.answer:AnswerBlock',
    'pb-answer-recap = problem_builder.answer:AnswerRecapBlock',
    'pb-mcq = problem_builder.mcq:MCQBlock',
    'pb-swipe = problem_builder.swipe:SwipeBlock',
    'pb-rating = problem_builder.mcq:RatingBlock',
    'pb-mrq = problem_builder.mrq:MRQBlock',
    'pb-slider = problem_builder.slider:SliderBlock',
    'pb-completion = problem_builder.completion:CompletionBlock',
    'pb-message = problem_builder.message:MentoringMessageBlock',
    'pb-tip = problem_builder.tip:TipBlock',
    'pb-choice = problem_builder.choice:ChoiceBlock',

    'pb-dashboard = problem_builder.dashboard:DashboardBlock',
    'pb-data-export = problem_builder.instructor_tool:InstructorToolBlock',  # Deprecated; use 'pb-instructor-tool' now
    'pb-instructor-tool = problem_builder.instructor_tool:InstructorToolBlock',
]

setup(
    name='xblock-problem-builder',
    version=VERSION,
    description='XBlock - Problem Builder',
    long_description=README,
    long_description_content_type='text/markdown',
    author='OpenCraft',
    url='https://github.com/open-craft/problem-builder',
    license='AGPL v3',
    packages=find_packages(
        include=['problem_builder', 'problem_builder.*'],
        exclude=["*tests"],
    ),
    package_data=package_data("problem_builder", ["templates", "public", "translations"]),
    install_requires=load_requirements('requirements/base.in'),
    python_requires=">=3.11",
    keywords='Python edx',
    entry_points={
        'xblock.v1': BLOCKS,
    },
)
