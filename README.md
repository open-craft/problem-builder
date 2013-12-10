
Custom workbench settings
-------------------------

In the main XBlock repository, create the following configuration file in `workbench/settings_mentoring.py`:

```
from settings import *

INSTALLED_APPS += ('mentoring',)
DATABASES['default']['NAME'] = 'workbench.sqlite'
```

Running tests
-------------

Run with the following command:

```
$ DJANGO_SETTINGS_MODULE="workbench.settings_mentoring" PYTHONPATH=".:/path/to/xblock" nosetests --with-django
```

`/path/to/xblock` is the path to the XBlock main repository (the one containing the workbench)
 
