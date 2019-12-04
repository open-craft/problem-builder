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

You can install Problem Builder from [PyPI](https://pypi.org/project/xblock-problem-builder/)
using this command:

```
pip install xblock-problem-builder
```

For full details, see "Open edX Installation", below.

Usage
-----

See [Usage Instructions](doc/Usage.md)

Workbench installation and settings
-----------------------------------

For developers, you can install this XBlock into an XBlock SDK workbench's
virtualenv.

Firstly, create a virtualenv:

```bash
~/xblock_development $ virtualenv venv
~/xblock_development $ . venv/bin/activate
```

Now run the following commands from the problem builder repo
root to install the problem builder dependencies:

```bash
(venv) ~/xblock_development/problem-builder $ pip install -r requirements.txt
(venv) ~/xblock_development/problem-builder $ pip install -r requirements-dev.txt
```

Switch to the created XBlock SDK repository, install its dependencies, and
create its migrations:

```bash
(venv) ~/xblock_development/problem-builder $ cd ../venv/src/xblock-sdk
(venv) ~/xblock_development/venv/src/xblock-sdk $ make pip
(venv) ~/xblock_development/venv/src/xblock-sdk $ python manage.py makemigrations workbench
```

Create the following configuration file in `workbench/settings_pb.py`:

```python
from settings import *

INSTALLED_APPS += ('problem_builder',)
DATABASES['default']['NAME'] = 'var/workbench.db'
```

Because this XBlock uses a Django model, you need to sync the database
before starting the workbench. Run this from the XBlock repository
root:

```bash
$ ./manage.py migrate --settings=workbench.settings_pb
```

Running the workbench
---------------------

```bash
$ ./manage.py runserver 8000 --settings=workbench.settings_pb
```

Access it at [http://localhost:8000/](http://localhost:8000).

Running tests
-------------

The integration tests require a recent Firefox and geckodriver (CI
uses Firefox 70 and geckodriver 0.26). These can be installed locally for
testing if required. For example on Linux:

```
mkdir external
cd external
wget https://archive.mozilla.org/pub/firefox/releases/70.0.1/linux-x86_64/en-US/firefox-70.0.1.tar.bz2
tar jxf firefox-70.0.1.tar.bz2
wget https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-linux64.tar.gz
tar xzf geckodriver-v0.26.0-linux64.tar.gz
export PATH="$(pwd):$(pwd)/firefox/:$PATH"

# now can run integration tests using this firefox version
cd ..
make test.integration
```

From the problem-builder repository root, run the tests with the
following command:

```bash
$ make test
```

See also the following for more scoped tests:

```bash
$ make quality
$ make test.unit
$ make test.integration
```

Working with Translations
-------------------------

For information about working with translations, see the
[Internationalization Support](http://edx.readthedocs.io/projects/xblock-tutorial/en/latest/edx_platform/edx_lms.html#internationalization-support)
section of the [Open edX XBlock Tutorial](https://xblock-tutorial.readthedocs.io/en/latest/).

[Prepare your virtualenv](#workbench-installation-and-settings) and ensure that the
[Transifex authentication file](https://openedx.atlassian.net/wiki/display/OpenOPS/Running+Fullstack)
(``~/.transifexrc``) is properly set up.

Push new strings to Transifex:

```bash
$ make extract_translations
$ make push_translations
```

To get the latest translations from Transifex:

```bash
$ make pull_translations
$ make compile_translations
```

For testing purposes it's faster to avoid Transifex and work on dummy Esperanto translations:

```bash
$ make build_dummy_translations
```

The Transifex configuration is stored in `.tx`. For more information read
[transifex's documentation](https://docs.transifex.com/client/client-configuration)

If you want to add a new language:
  1. Add language to `problem_builder/translations/config.yaml`
  2. Make sure all tagged strings have been extracted and push to Transifex as described above.
  3. Go to Transifex and translate both of the
     [Problem Builder](https://www.transifex.com/open-edx/xblocks/problem-builder/) 
     and the [Problem Builder JS](https://www.transifex.com/open-edx/xblocks/problem-builder-js/) resources.
  4. When you're done with the translations pull from Transifex as described above.


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
* `edx-platform` version `named-release/dogwood.3` and earlier must use
  [v2.0.0](https://github.com/open-craft/problem-builder/tree/v2.0.0).

The `edx-platform` `master` branch will generally always be compatible with the most recent Problem Builder tag.  See
[the EDXAPP_PRIVATE_REQUIREMENTS setting](https://github.com/edx/configuration/blob/master/playbooks/roles/edxapp/defaults/main.yml) for the version
currently installed on [edx.org](https://edx.org).

To install new versions of Problem Builder (v3.1.3+), use `pip install xblock-problem-builder` or specify a version using e.g. `pip install xblock-problem-builder==3.1.3`. To do this on Open edX could look like:

```bash
$ sudo -Hu edxapp bash
edxapp $ cd && . edxapp_env  && . ./venvs/edxapp/bin/activate && cd edx-platform/
edxapp $ pip install xblock-problem-builder
edxapp $ ./manage.py lms migrate --settings=aws  # or openstack, as appropriate
```

Then, restart the edxapp services:
```bash
$ sudo /edx/bin/supervisorctl restart edxapp:
$ sudo /edx/bin/supervisorctl restart edxapp_workers:
```

To install old verions of Problem Builder (< v3.1.3) on an Open edX installation, choose the tag you wish to install, follow the above instructions but instead of the `pip install xblock-problem-builder` command, use:

```
TAG='v2.6.5' pip install "git+https://github.com/open-craft/problem-builder.git@$TAG#egg=xblock-problem-builder==$TAG"
```

Note that Problem Builder requires [xblock-utils](https://github.com/edx/xblock-utils).
If you are installing it into a virtualenv used by edx-platform, xblock-utils should
already be installed. But if you are installing it into another virtualenv, you may
need to first install xblock-utils manually (recent versions of it are not available
on PyPI so will not be automatically installed).

See [Usage Instructions](doc/Usage.md) for how to enable in Studio.

Publishing to PyPI
------------------

Whenever we tag a new version, e.g. `v3.1.3` and push it to GitHub, CircleCI will
build it and deploy it to PyPI automatically. For details on how this works, see
[this pull request](https://github.com/open-craft/problem-builder/pull/199).

License
-------

This XBlock is available under the GNU Affero General Public License (AGPLv3).
