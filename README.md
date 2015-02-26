Mentoring XBlock
----------------

[![Build Status](https://travis-ci.org/open-craft/xblock-mentoring.svg?branch=master)](https://travis-ci.org/open-craft/xblock-mentoring)

This XBlock allows to automate the workflow of real-life mentoring,
within an edX course.

It supports:

* **Free-form answers** (textarea) which can be shared accross
  different XBlock instances (for example, to remind a student of an
  answer he gave before). Editable or read-only.
* **Self-assessment MCQs** (multiple choice), to display predetermined
  feedback to a student based on his choices in the
  self-assessment. Supports rating scales and arbitrary answers.
* **Progression tracking**, allowing to check that the student has
  completed the previous steps before allowing to complete a given
  XBlock instance. Provides a link to the next step to the student.
* **Tables**, which allow to present answers from the student to
  free-form answers in a concise way. Supports custom headers.
* **Data export**, to allow course authors to download a CSV file
  containing the free-form answers entered by the students.

The screenshot shows an example of a mentoring block containing a
free-form question, two MCQs and one MRQ.

![Mentoring Example](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/mentoring-example.png)

Installation
------------

Install the requirements into the python virtual environment of your
`edx-platform` installation by running the following command from the
root folder:

```bash
$ pip install -r requirements.txt
```

Enabling in Studio
------------------

You can enable the Mentoring XBlock in studio through the advanced
settings.

1. From the main page of a specific course, navigate to `Settings ->
   Advanced Settings` from the top menu.
2. Check for the `advanced_modules` policy key, and add `"mentoring"`
   to the policy value list.
3. Click the "Save changes" button.

Usage
-----

When you add the `Mentoring` component to a course in the studio, the
built-it editing tools guide you through the process of configuring the
block and adding individual questions.

### Mentoring modes

There are 2 mentoring modes available:

* *standard*: Traditional mentoring. All questions are displayed on the
  page and submitted at the same time. The students get some tips and
  feedback about their answers. This is the default mode.

* *assessment*: Questions are displayed and submitted one by one. The
  students don't get tips or feedback, but only know if their answer was
  correct. Assessment mode comes with a default `max_attempts` of `2`.

Below are some LMS screenshots of a mentoring block in assessment mode.

Question before submitting an answer:

![Assessment Step 1](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/assessment-1.png)

Question after submitting the correct answer:

![Assessment Step 2](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/assessment-2.png)

Question after submitting a wrong answer:

![Assessment Step 3](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/assessment-3.png)

Score review and the "Try Again" button:

![Assessment Step 4](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/assessment-4.png)

### Free-form questions

Free-form questions are represented by a "Long Answer" component. 

Example screenshot before answering the question:

![Answer Initial](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/answer-1.png)

Screenshot after answering the question:

![Answer Complete](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/answer-2.png)

You can add "Long Answer Recap" components to mentoring blocks later on
in the course to provide a read-only view of any answer that the student
entered earlier.

The read-only answer is rendered as a quote in the LMS:

![Answer Read-Only](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/answer-3.png)

### Self-assessment MCQs

Multiple choice questions are represented by the `<mcq>` element. The
`<mcq>` element supports the following attributes:

* `name` - Unique name that identifies the question withing a course.
* `weight` - The weight is used when computing total grade/score of
  the mentoring block. The larger the weight, the more influence this
  question will have on the grade. Value of zero means this question
  has no influence on the grade (float, defaults to `1`).
* `type` - Can be set to `choices` (default) or `rating`.
* `low` - Sets the label of the lowest value. Only makes sense for
  questions of the `rating` type (string; defaults to `"Less"`).
* `high` - Sets the label of the lowest value. Only makes sense for
  questions of the `rating` type (string; defaults to `"More"`).

The `<mcq>` element can contain the following child elements:

* `<question>` - The question text to display above the radio buttons.
* `<choice>` - Defines a choice corresponding to a single radio
  button.
* `<tip>` - Defines feedback tips displayed when student submits their
  answer.

The `<choice>` elements support a single (required) attribute
`value`. The should be a string which is unique among the choices of a
single MCQ.

The contents of the `<tip>` element specify the message to display
next to the question when the question is submitted. It supports two
mutually exclusive attributes `display` and `reject`. The value of
the attributes should be a comma-separated list of choice values for
which the tip should be shown. When using `display`, the listed
choices are considered "correct" and if one of the listed choices is
selected when submitting an answer, the question will be considered
complete. The values under `reject` on the other hand contain
questions which are not considered correct and the question will not
be considered completed until the student submits a choice from the
`display` list instead.

#### Rating MCQ

When constructing questions where the student rates some topic on the
scale from `1` to `5`, you can set the `type` attribute of `<mcq>` to
`rating`, which automatically generates choices with values from `"1""`
to `"5"`. The `low` and `high` attributes specify the text shown next
to the lowest and highest valued choice.

#### Example

The below example sets up two MCQs. The second one is of the `rating`
type.

```xml
<mentoring url_name="mcq_1">
    <mcq name="mcq_1_1" type="choices" weight="10">
        <question>Do you like this MCQ?</question>
        <choice value="yes">Yes</choice>
        <choice value="maybenot">Maybe not</choice>
        <choice value="understand">I don't understand</choice>

        <tip display="yes">Great!</tip>
        <tip reject="maybenot">Ah, damn.</tip>
        <tip reject="understand"><html><div id="test-custom-html">Really?</div></html></tip>
    </mcq>

    <mcq name="mcq_1_2" type="rating" low="Not good at all" high="Extremely good" weight="5">
        <question>How much do you rate this MCQ?</question>
        <choice value="notwant">I don't want to rate it</choice>

        <tip display="4,5">I love good grades.</tip>
        <tip reject="1,2,3">Will do better next time...</tip>
        <tip reject="notwant">Your loss!</tip>
    </mcq>
</mentoring>
```

Before attempting to answer the questions:

![MCQ Initial](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/mcq-1.png)

While attempting to complete the questions:

![MCQ Attempting](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/mcq-2.png)

After successfully completing the questions:

![MCQ Success](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/mcq-3.png)

### Self-assessment MRQs

Multiple response questions are set up similarly to MCQs. The answers
are rendered as checkboxes. Unlike MCQs where only a single answer can
be selected, MRQs allow multiple answers to be selected at the same
time.

The `<mrq>` element supports these attributes:

* `name` - Unique name that identifies the question withing a course.
* `weight` - The weight is used when computing total grade/score of
  the mentoring block. The larger the weight, the more influence this
  question will have on the grade. Value of zero means this question
  has no influence on the grade (float, defaults to `1`).
* `hide_results` - If set to `true`, the feedback icons next to each
  choice will not be displayed (boolean; defaults to `false`).

The `<question>` and `<choice>` elements work the same way as they
do when used with MCQs (see above).

The `<tip>` elements also work similarly, except that you should use
`require` instead of `display` attribute to mark all answers that
should be checked before the question is considered complete.
While the content of the `<tip>` element in a MCQ is automatically
displayed to the student when submitting an answer, it is only
displayed for MRQs when the student clicks on the feedback icon next
to the corresponding choice.

The `<mrq>` element supports an additional child element `<message>`
with a single required attribute `type`. The only supported type at
this time is `on-submit`. The contents of the `<message>` element are
displayed every time the student submits an answer to the question.

#### Example

The example shows two MRQs. The first one uses a `<message
type="on-submit">` to display a custom message. The second MRQ
demonstrates the effects of setting `hide_results` attribute to
`true`.

```xml
<mentoring url_name="mrq_1">
    <mrq name="mrq_1_1" weight="3">
        <question>What do you like in this MRQ?</question>
        <choice value="elegance">Its elegance</choice>
        <choice value="beauty">Its beauty</choice>
        <choice value="gracefulness">Its gracefulness</choice>
        <choice value="bugs">Its bugs</choice>

        <tip require="gracefulness">This MRQ is indeed very graceful</tip>
        <tip require="elegance,beauty">This is something everyone has to like about this MRQ</tip>
        <tip reject="bugs">Nah, there isn't any!</tip>

        <message type="on-submit">Thank you for answering!</message>
    </mrq>

    <mrq name="mrq_1_2" hide_results="true">
        <question>What do you like in this MRQ?</question>
        <choice value="elegance">Its elegance</choice>
        <choice value="beauty">Its beauty</choice>
        <choice value="gracefulness">Its gracefulness</choice>
        <choice value="bugs">Its bugs</choice>

        <tip require="gracefulness">This MRQ is indeed very graceful</tip>
        <tip require="elegance,beauty">This is something everyone has to like about this MRQ</tip>
        <tip reject="bugs">Nah, there isn't any!</tip>
    </mrq>
</mentoring>
```

Before attempting to answer the questions:

![MRQ Initial](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/mrq-1.png)

While attempting to answer the questions:

![MRQ Attempt](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/mrq-2.png)

After clicking on the feedback icon next to the "Its bugs" answer:

![MRQ Attempt](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/mrq-3.png)

After successfully completing the questions:

![MRQ Success](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/mrq-4.png)

### Tables

The mentoring table allows you to present answers to multiple
free-form questions in a concise way. The table consists of mulitple
columns defined with the `<column>` element. Each `<column>` element
should contain a `<header>` and an `<answer>` element. The `<header>`
elements sets the text of the header while the `<answer>` element
references a free-form question through its mandatory `name` attribute.

#### Example

These example shows a table containing to two previously answered
questions.

```xml
<mentoring url_name="goal_table">
  <mentoring-table url_name="goal_table">
      <column>
          <header>Your goal</header>
          <answer name="goal" />
      </column>

      <column>
          <header>Your Other Goal</header>
          <answer name="goal_other" />
      </column>
  </mentoring-table>
</mentoring>
```

![Mentoring Table](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/mentoring-table.png)

### Maximum Attempts

You can set the number of maximum attempts for the unit completion by
setting the `max_attempts` attribute of the `<mentoring>` element.

```xml
<mentoring url_name="mcq_1" max_attempts="2">
    <title>Max Attempts Demonstration</title>
    <mcq name="mcq_1_1x" type="choices">
        <question>Do you like this MCQ?</question>
        <choice value="yes">Yes</choice>
        <choice value="maybenot">Maybe not</choice>
        <choice value="understand">I don't understand</choice>

        <tip display="yes">Great!</tip>
        <tip reject="maybenot">Ah, damn.</tip>
        <tip reject="understand"><html><div id="test-custom-html">Really?</div></html></tip>
    </mcq>
</mentoring>
```

Before submitting an answer for the first time:

![Max Attempts Before](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/max-attempts-before.png)

After submitting a wrong answer two times:

![Max Attempts Reached](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/max-attempts-reached.png)

### Custom tip popup window size

You can specify `width` and `height` attributes of any Tip component to
customize the popup window size. The value of those attribute should
be valid CSS (e.g. `50px`).

Workbench installation and settings
-----------------------------------

Install to the workbench's virtualenv by running the following command form the mentoring repo root:

```bash
pip install -r requirements.txt
```

In the main XBlock repository, create the following configuration file
in `workbench/settings_mentoring.py` in the XBlock repository:

```python
from settings import *

INSTALLED_APPS += ('mentoring',)
DATABASES['default']['NAME'] = 'workbench.sqlite'
```

Because this XBlock uses a Django model, you need to sync the database
before starting the workbench. Run this from the XBlock repository
root:

```bash
$ ./manage.py syncdb --settings=workbench.settings_mentoring
```

Running the workbench
---------------------

```bash
$ ./manage.py runserver 8000 --settings=workbench.settings_mentoring
```

Access it at [http://localhost:8000/](http://localhost:8000).

Running tests
-------------

First, make sure the [XBlock SDK (Workbench)](https://github.com/edx/xblock-sdk)
is installed in the same virtual environment as xblock-mentoring.

From the xblock-mentoring repository root, run the tests with the
following command:

```bash
$ ./run_tests.py
```

If you want to run only the integration or the unit tests, append the directory to the command. You can also run separate modules in this manner.

```bash
$ ./run_tests.py mentoring/tests/unit
```

Adding custom scenarios to the workbench
----------------------------------------

Within the xblock-mentoring repository, create the `templates/xml` and
add XML scenarios to it - all files with the `*.xml` extension will be
automatically loaded by the workbench:

```bash
$ mkdir templates/xml
$ cat > templates/xml/my_mentoring_scenario.xml
```

Restart the workbench to take the new scenarios into account.

Upgrading from Version 1
------------------------

To upgrade a course from the earlier version of this XBlock, run the following
command on a system with edx-platform and xblock-mentoring installed:

```bash
$ SERVICE_VARIANT=cms DJANGO_SETTINGS_MODULE="cms.envs.devstack" python -m mentoring.v1.upgrade "Org/Course/Run"
```
Where "Org/Course/Run" is replaced with the ID of the course to upgrade.

License
-------

The Mentoring XBlock is available under the GNU Affero General
Public License (AGPLv3).
