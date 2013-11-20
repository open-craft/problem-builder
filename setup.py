from setuptools import setup

BLOCKS = [
    'mentoring = mentoring:MentoringBlock',
    'answer = mentoring:AnswerBlock',
    'quizz = mentoring:QuizzBlock',
]

setup(
    name='xblock-mentoring',
    version='0.1',
    description='XBlock - Mentoring',
    packages=['mentoring'],
    entry_points={
        'xblock.v1': BLOCKS,
        'xmodule.v1': BLOCKS,
    }
)
