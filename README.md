Problem Builder and Step Builder
--------------------------------

[![Circle CI](https://circleci.com/gh/open-craft/problem-builder.svg?style=svg)](https://circleci.com/gh/open-craft/problem-builder)

This repository provides two XBlocks: Problem Builder and Step Builder.

Both blocks allow to create questions of various types. They can be
used to simulate the workflow of real-life mentoring, within an edX
course.

Supported features include:

* **Free-form answers** (textarea) which can be shared accross
  different XBlock instances (for example, to allow a student to
  review and edit an answer they gave before).
* **Self-assessment MCQs** (multiple choice questions), to display
  predetermined feedback to a student based on his choices in the
  self-assessment. Supports rating scales and arbitrary answers.
* **MRQs (Multiple Response Questions)**, a type of multiple choice
  question that allows the student to select more than one choice.
* **Answer recaps** that display a read-only summary of a user's
  answer to a free-form question asked earlier in the course.
* **Progression tracking**, to require that the student has
  completed a particular step before allowing them to complete the
  next step. Provides a link to the next step to the student.
* **Tables**, which allow to present answers from the student to
  free-form answers in a concise way. Supports custom headers.
* **Dashboards**, for displaying a summary of the student's answers
  to multiple choice questions. [Details](doc/Dashboard.md)

The following screenshot shows an example of a Problem Builder block
containing a free-form question, two MCQs and one MRQ:

![Problem Builder Example](doc/img/mentoring-example.png)

Installation
------------

Install the requirements into the Python virtual environment of your
`edx-platform` installation by running the following command from the
root folder:

```bash
$ pip install -r requirements.txt
```

Usage
-----

See [Usage Instructions](doc/Usage.md)

Workbench installation and settings
-----------------------------------

Install to the workbench's virtualenv by running the following command from the
problem builder repo root:

```bash
pip install -r requirements.txt
```

In the main XBlock repository, create the following configuration file
in `workbench/settings_pb.py` in the XBlock repository:

```python
from settings import *

INSTALLED_APPS += ('problem_builder',)
DATABASES['default']['NAME'] = 'workbench.sqlite'
```

Because this XBlock uses a Django model, you need to sync the database
before starting the workbench. Run this from the XBlock repository
root:

```bash
$ ./manage.py syncdb --settings=workbench.settings_pb
```

Running the workbench
---------------------

```bash
$ ./manage.py runserver 8000 --settings=workbench.settings_pb
```

Access it at [http://localhost:8000/](http://localhost:8000).

Running tests
-------------

First, make sure the [XBlock SDK (Workbench)](https://github.com/edx/xblock-sdk)
is installed in the same virtual environment as xblock-problem-builder.

From the xblock-problem-builder repository root, run the tests with the
following command:

```bash
$ ./run_tests.py
```

If you want to run only the integration or the unit tests, append the directory to the command. You can also run separate modules in this manner.

```bash
$ ./run_tests.py problem_builder/tests/unit
```

Extracting Translatable Strings
-------------------------------

To extract/update strings for translation, you will need i18n_tools:

```bash
pip install git+https://github.com/edx/i18n-tools.git#egg=i18n_tools
```

To extract strings, use `i18n_tool extract`. To build a dummy translation for
testing, use:

```bash
i18n_tool dummy && i18n_tool generate
```


Adding custom scenarios to the workbench
----------------------------------------

Within the xblock-problem-builder repository, create the `templates/xml` and
add XML scenarios to it - all files with the `*.xml` extension will be
automatically loaded by the workbench:

```bash
$ mkdir templates/xml
$ cat > templates/xml/my_pb_scenario.xml
```

Restart the workbench to take the new scenarios into account.

Upgrading from Version 1
------------------------

To upgrade a course from xblock-mentoring ("v1") to xblock-problem-builder
("v2"), run the following command on a system with edx-platform,
xblock-mentoring, and xblock-problem-builder installed:

```bash
$ SERVICE_VARIANT=cms DJANGO_SETTINGS_MODULE="cms.envs.devstack" python -m problem_builder.v1.upgrade "Org/Course/Run"
```
Where "Org/Course/Run" is replaced with the ID of the course to upgrade.


Open edX Installation
---------------------

Problem Builder releases are tagged with a version number, e.g.
[`v2.6.0`](https://github.com/open-craft/problem-builder/tree/v2.6.0),
[`v2.6.5`](https://github.com/open-craft/problem-builder/tree/v2.6.5).  We recommend installing the most recently tagged
version, with the exception of the following compatibility issues:

* `edx-platform` version `open-release/eucalyptus.2` and earlier must use
  ≤[v2.6.0](https://github.com/open-craft/problem-builder/tree/v2.6.0).  See
  [PR 128](https://github.com/open-craft/problem-builder/pull/128) for details.
* `edx-platform` version `named-release/dogwood.3` must use
  [v2.0.0](https://github.com/open-craft/problem-builder/tree/v2.0.0).
* Otherwise, consult the `edx-platform/requirements/edx/edx-private.txt` file to see which revision was
  used by [edx.org](https://edx.org) for your branch.

The `edx-platform` `master` branch will generally always be compatible with the most recent Problem Builder tag.  See
[edx-private.txt](https://github.com/edx/edx-platform/blob/master/requirements/edx/edx-private.txt) for the version
currently installed on [edx.org](https://edx.org).

To install Problem Builder on an Open edX installation, choose the tag you wish to install, and run:

```bash
$ sudo -u edxapp -Hs
edxapp $ cd ~
edxapp $ source edxapp_env
edxapp $ TAG='v2.6.5'  # example revision
edxapp $ pip install "git+https://github.com/open-craft/problem-builder.git@$TAG#egg=xblock-problem-builder==$TAG"
edxapp $ cd edx-platform
edxapp $ ./manage.py lms migrate --settings=aws  # or openstack, as appropriate
```

Then, restart the edxapp services:
```bash
$ sudo /edx/bin/supervisorctl restart edxapp:
$ sudo /edx/bin/supervisorctl restart edxapp_workers:
```

See [Usage Instructions](doc/Usage.md) for how to enable in Studio.

License
-------

This XBlock is available under the GNU Affero General Public License (AGPLv3).
