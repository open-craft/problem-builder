from setuptools import setup

BLOCKS = [
    'mentoring = mentoring:MentoringBlock',
    'mentoring-dataexport = mentoring:MentoringDataExportBlock',
    'mentoring-table = mentoring:MentoringTableBlock',
    'column = mentoring:MentoringTableColumnBlock',
    'answer = mentoring:AnswerBlock',
    'quizz = mentoring:QuizzBlock',
    'tip = mentoring:QuizzTipBlock',
]

setup(
    name='xblock-mentoring',
    version='0.1',
    description='XBlock - Mentoring',
    packages=['mentoring'],
    entry_points={
        'xblock.v1': BLOCKS,
    }
)
