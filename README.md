Mentoring XBlock
----------------

This XBlock allows to automate the workflow of real-life mentoring, within an edX course.

It supports:

* **Free-form answers** (textarea) which can be shared accross different XBlock instances (for example, to remind a student of an answer he gave before). Editable or read-only.
* **Self-assessment MCQs** (multiple choice), to display predetermined feedback to a student based on his choices in the self-assessment. Supports rating scales and arbitrary answers.
* **Progression tracking**, allowing to check that the student has completed the previous steps before allowing to complete a given XBlock instance. Provides a link to the next step to the student.
* **Tables**, which allow to present answers from the student to free-form answers in a concise way. Supports custom headers.
* **Data export**, to allow course authors to download a CSV file containing the free-form answers entered by the students

Examples
--------

### Free-form answers

First XBlock instance:

```xml
<mentoring url_name="goal_definition" followed_by="getting_feedback" weight="20">
    <html>
        <p>What is your goal?</p>
    </html>

    <answer name="goal" weight="10"/>
</mentoring>
```

Second XBlock instance:

```xml
<mentoring url_name="getting_feedback">
    <html>
        <p>The goal you entered was:</p>
    </html>
    <answer name="goal" read_only="true" />

    <html>
        <p>Ask feedback from friends about this goal - what did they think?</p>
    </html>
    <answer name="goal_feedback" weight="5"/>
</mentoring>
```

You can specify the weight of a free form answer. It will be considered during the
grade/score computation.

### Self-assessment MCQs

```xml
<mentoring url_name="mcq_1" enforce_dependency="false">
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
    </MCQ>

    <message type="completed">
        All is good now...
        <html><p>Congratulations!</p></html>
    </message>
    <message type="incomplete">
        <html><p>Still some work to do...</p></html>
    </message>
</mentoring>
```

You can specify the weight of a self-assessment MCQ. It will be considered during the
grade/score computation.

### Self-assessment MRQs
```xml
<mentoring url_name="mrq_1" enforce_dependency="false">
    <mrq name="mrq_1_1" type="choices" hide_results="true" weight="10">
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
    <message type="completed">
        All is good now...
        <html><p>Congratulations!</p></html>
    </message>
    <message type="incomplete">
        <html><p>Still some work to do...</p></html>
    </message>
</mentoring>
```

You can specify the weight of a self-assessment MRQ. It will be considered during the
grade/score computation.

### Tables

```xml
<mentoring-table type="goal" url_name="goal_table">
    <column>
        <header>Your goal</header>
        <answer name="goal" />
    </column>

    <column>
        <header>Header Test 2</header>
        <answer name="goal_feedback" />
    </column>
</mentoring-table>
```

### Data export

```xml
<vertical>
    <mentoring-dataexport url_name="mentoring_dataexport"></mentoring-dataexport>
</vertical>
```

### Modes

There are 2 mentoring modes available:

 * standard: Traditional mentoring. All questions are displayed in the page and submitted at the
   same time. The student get some tips and feedback about their answers. (default mode)

 * assessment: Questions are displayed and submitted one after one. The student dont get tips or
   feedback but only know if their answer was correct. Assessment mode comes with a default
   max_attempts of 2.

To set the *assessment* mode, set the mode attribute in the settings:
```xml
<mentoring url_name="mentoring_1" mode="assessment">
...
</mentoring>
```

### Maximum Attempts

You can set the number of maximum attempts for the unit completion, as well as
a feedback message when the maximum number of attempts is reached:
```xml
<mentoring url_name="mcq_1" enforce_dependency="false" max_attempts="3">
    <mrq name="mrq_1_1" type="choices" hide_results="true">
        <question>What do you like in this MRQ?</question>
        <choice value="elegance">Its elegance</choice>
        ...
    </mrq>
    <message type="completed">
        All is good now...
        <html><p>Congratulations!</p></html>
    </message>
    <message type="max_attempts_reached">
        <html><p>Maximum number of attempts reached</p></html>
    </message>
</mentoring>
```

### Custom tip popup window size

You can specify `width` and `height` attributes to the `tip` child to customize the popup window
size. The value of those attribute should be valid CSS.

```xml
<mentoring url_name="mcq_1" enforce_dependency="false">
    <mrq name="mrq_1_1" type="choices">
        <question>What do you like in this MRQ?</question>
        <choice value="elegance">Its elegance</choice>
        ...
        <tip require="elegance" width="50px" height="20px">This is something everyone has to like about this MRQ</tip>
    </mrq>
</mentoring>
```

### Custom Nav title

The Nav title (the black tooltip showed on hover on the Units Nav bar) is a list of the `display_name` attributes of all the blocks present in that Unit.

So two Mentoring blocks like the following will result in a tooltip like the one below:

```xml
<mentoring url_name="mentoring-0a06b184" weight="20" display_name="First Mentoring block">
<mentoring url_name="mentoring-1a04badd" weight="20" display_name="Second Mentoring block">
```

![image](https://cloud.githubusercontent.com/assets/1225294/2820216/b0228fd8-cef7-11e3-98e1-5fdbf49b706a.png)

The default title is "Mentoring Block".

Installing dependencies
-----------------------

From the xblock-mentoring repository, and within the Python virtual environment you used to setup the XBlock
workbench or the LMS, install the requirements:

```bash
$ pip install -r requirements.txt
```

You also need to install the mentoring XBlock in the same virtual environment. From the `xblock-mentoring`
directory, enter:

```bash
$ pip install -e .
```

Since `XBlock` and `xblock-mentoring` are both in development, it is recommended
to use the `XBlock` revision specified in the workbench/LMS requirements.txt
file. The main `XBlock` repository is not always ready to use in edx-platform
and you might experience some issues.

Custom workbench settings
-------------------------

In the main XBlock repository, create the following configuration file in `workbench/settings_mentoring.py`
in the XBlock repository:

```python
from settings import *

INSTALLED_APPS += ('mentoring',)
DATABASES['default']['NAME'] = 'workbench.sqlite'
```

Starting the workbench
----------------------

Because this XBlock uses a Django model, you need to sync the database before starting the workbench. Run this
from the XBlock repository root:

```bash
$ ./manage.py syncdb --settings=workbench.settings_mentoring
```

Then start the workbench:

```bash
$ ./manage.py runserver 8000 --settings=workbench.settings_mentoring
```

Access it at http://localhost:8000/

Running tests
-------------

From the xblock-mentoring repository root, run the tests with the following command:

```bash
$ DJANGO_SETTINGS_MODULE="workbench.settings_mentoring" PYTHONPATH=".:/path/to/xblock" nosetests --with-django
```

`/path/to/xblock` is the path to the XBlock main repository (the one containing the workbench)

Adding custom scenarios to the workbench
----------------------------------------

Within the xblock-mentoring repository, create the `templates/xml` and add XML scenarios to it - all files with
the `*.xml` extension will be automatically loaded by the workbench:

```bash
$ mkdir templates/xml
$ cat > templates/xml/my_mentoring_scenario.xml
```

Restart the workbench to take the new scenarios into account.
