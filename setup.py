from setuptools import setup

setup(
    name='xblock-mentoring',
    version='0.1',
    description='XBlock - Mentoring',
    packages=['mentoring'],
    entry_points={
        'xblock.v1': [
            'mentoring = mentoring:MentoringBlock',
        ],
        'xmodule.v1': [
            'mentoring = mentoring:MentoringBlock',
        ]
    }
)
