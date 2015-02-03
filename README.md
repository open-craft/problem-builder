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
block is field with default XML content, shown in the screenshot below.

![Edit View](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/edit-view.png)

The wrapping `<mentoring>` supports the following attributes:

* `weight` - The number of points for this block (float; defaults to `1`).
* `max_attempts` - The maximum number of of times the student can
  submit an answer for this block. Set to zero for no limit. (integer;
  defaults to `0`)
* `url_name` - A unique identifier for this block. Used to refer to
  this block from other blocks and to be able to declare dependencies
  (string; a default unique value is generated when block is created).
* `followed_by` - The `url_name` of the next block the student should
  go to after completing this block. (string; defaults to `None`).
* `enforce_dependency` - Whether to enforce dependencies on this block
  as specified with `followed_by`. When set to `true`, the student
  will only be allowed to attempt this block after finishing the
  block that specifies the current block in its `followed_by`
  attribute (boolean; defaults to `false`).
* `mode` - The mentoring mode to use for this block. Two mentoring
  modes are currently supported: `standard` and `assessement`. For
  more information on the modes see the sectino below (string;
  defaults to `standard`)

The wrapping `<mentoring>` element can contain the following child
elements:

* `<title>` - Renders the title of the block.
* `<html>` - May contain arbitrary HTML to be displayed in the block.
* `<shared-header>` - A specialized HTML block, displayed together with the title as a shared header for every step in assessment mode.
* `<answer>` - Represents a free-form answer, rendered as a textarea
  element.
* `<mcq>` - Multiple choice question, rendered as radio buttons.
* `<mrq>` - Multiple response question, rendered as checkboxes.
* `<mentoring-table>` - Displays answers to free-form questions in a
  HTML table.
* `<message>` - Declares feedback text that is displayed when the
  student submits an answer (ignored in `assessment` mode).

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

Free-form questions are represented by an `<answer>` element. The
answer element supports the following attributes:

* `name` - Sets the name of the question. The name can be used to
  refer to the question when displaying the answer in another block.
  The name is not visible to the student. Should be unique within a
  course.
* `weight` - The weight is used when computing total grade/score of
  the mentoring block. The larger the weight, the more influence this
  question will have on the grade. Value of zero means this question
  has no influence on the grade (float, defaults to `1`).
* `min_characters` - The minimum length of the answer. If the answer
  contains less than the specified number of characters, the answer is
  considered invalid and the student will not be allowed to submit the
  answer (integer; defaults to `0`).
* `read_only` - Whether the answer should be rendered read-only. This
  only makes sense when displaying an answer to a previously answered
  question. The answer is rendered as a HTML quote instead of a
  textarea element (boolean; defaults to `false`).

It can also have a `<question>` element containing a paragraph of non-formatted plain text.

#### Example

Here is a simple example of a free-form question:

```xml
<mentoring url_name="goal_definition" followed_by="getting_feedback" weight="20">
    <answer name="goal" weight="10">
        <question>What is your goal?</question>
    </answer>
</mentoring>
```

Screenshot before answering the question:

![Answer Initial](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/answer-1.png)

Screenshot after answering the question:

![Answer Complete](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/answer-2.png)

The second example shows how to display the answer that the student
submitted in the previous step. The only difference is that the
`read_only` attribute is set to `true`.

```xml
<mentoring url_name="getting_feedback">
    <html>
        <p>The goal you entered was:</p>
    </html>
    <answer name="goal" read_only="true" />
</mentoring>
```

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

### Data export

The Data export XBlock allows the instructor team to export all the
student answers to questions from the entire course as a CSV file. To
use the Data Export XBlock, you must make sure that
`"mentoring-dataexport"` is present  in the `advanced_modules` list
under `Settings -> Advanced` in the Studio.

The Data export XBlock renders a button that will download a CSV file
when clicked.

![Data Export XBlock](https://raw.githubusercontent.com/edx-solutions/xblock-mentoring/1fb5e3ece6f34b6cf33c956a4fba1d7cbb7349a2/doc/img/dataexport.png)

The Data export XBlock is intented to be used as a tool by admins in
the Studio, and is not meant to be published on a live course.

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

You can specify `width` and `height` attributes to the `tip` child to
customize the popup window size. The value of those attribute should
be valid CSS.

```xml
<mentoring url_name="mcq_1" enforce_dependency="false">
    <mrq name="mrq_1_1" type="choices">
        <question>What do you like in this MRQ?</question>
        <choice value="elegance">Its elegance</choice>
        ...
        <tip require="elegance" width="50px" height="20px">
          This is something everyone has to like about this MRQ.
        </tip>
    </mrq>
</mentoring>
```

### Custom Nav title

The Nav title (the black tooltip showed on hover on the Units Nav bar)
is a list of the `display_name` attributes of all the blocks present
in that Unit.

So two Mentoring blocks like the following will result in a tooltip
like the one below:

```xml
<mentoring url_name="mentoring-0a06b184" weight="20" display_name="First Mentoring block">
<mentoring url_name="mentoring-1a04badd" weight="20" display_name="Second Mentoring block">
```

![Nav Title](https://cloud.githubusercontent.com/assets/1225294/2820216/b0228fd8-cef7-11e3-98e1-5fdbf49b706a.png)

The default title is "Mentoring Block".

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

License
-------

The Mentoring XBlock is available under the GNU Affero General
Public License (AGPLv3).
