Mentoring XBlock
----------------

This XBlock allows to automate the workflow of real-life mentoring, within an edX course.

It supports:

* **Free-form answers** (textarea) which can be shared accross different XBlock instances (for example, to remind a student of an answer he gave before). Editable or read-only.
* **Self-assessment quizzes** (multiple choice), to display predetermined feedback to a student based on his choices in the self-assessment. Supports rating scales and arbitrary answers.
* **Progression tracking**, allowing to check that the student has completed the previous steps before allowing to complete a given XBlock instance. Provides a link to the next step to the student.
* **Tables**, which allow to present answers from the student to free-form answers in a concise way. Supports custom headers.
* **Data export**, to allow course authors to download a CSV file containing the free-form answers entered by the students

Examples
--------

### Free-form answers

First XBlock instance:

```xml
<mentoring url_name="goal_definition" followed_by="getting_feedback">
    <html>
        <p>What is your goal?</p>
    </html>

    <answer name="goal" />
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
    <answer name="goal_feedback" />
</mentoring>
```

### Self-assessment quizzes

```xml
<mentoring url_name="quizz_1" enforce_dependency="false">
    <quizz name="quizz_1_1" type="choices">
        <question>Do you like this quizz?</question>
        <choice value="yes">Yes</choice>
        <choice value="maybenot">Maybe not</choice>
        <choice value="understand">I don't understand</choice>

        <tip display="yes">Great!</tip>
        <tip reject="maybenot">Ah, damn.</tip>
        <tip reject="understand"><html><div id="test-custom-html">Really?</div></html></tip>
    </quizz>

    <quizz name="quizz_1_2" type="rating" low="Not good at all" high="Extremely good">
        <question>How much do you rate this quizz?</question>
        <choice value="notwant">I don't want to rate it</choice>

        <tip display="4,5">I love good grades.</tip>
        <tip reject="1,2,3">Will do better next time...</tip>
        <tip reject="notwant">Your loss!</tip>
    </quizz>

    <message type="completed">
        All is good now...
        <html><p>Congratulations!</p></html>
    </message>
</mentoring>
```

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

Installing dependencies
-----------------------

Within the Python virtual environment you used to setup the XBlock workbench or the LMS, install the
requirements:

```bash
$ pip install -r requirements.txt
```

You also need to install the mentoring XBlock in the same virtual environment. From the `xblock-mentoring`
directory, enter:

```bash
$ pip install -e .
```

Custom workbench settings
-------------------------

In the main XBlock repository, create the following configuration file in `workbench/settings_mentoring.py`:

```python
from settings import *

INSTALLED_APPS += ('mentoring',)
DATABASES['default']['NAME'] = 'workbench.sqlite'
```

Adding custom scenarios in the workbench
----------------------------------------

Create the `templates/xml` and add XML scenarios to it - all files with the `*.xml` extension will be
automatically loaded by the workbench:

```bash
$ mkdir templates/xml
$ cat > templates/xml/my_mentoring_scenario.xml
```

Starting the workbench
----------------------

Because this XBlock uses a Django model, you need to sync the database before starting the workbench:

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

Run with the following command:

```bash
$ DJANGO_SETTINGS_MODULE="workbench.settings_mentoring" PYTHONPATH=".:/path/to/xblock" nosetests --with-django
```

`/path/to/xblock` is the path to the XBlock main repository (the one containing the workbench)
 
