# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Harvard, edX & OpenCraft
#
# This software's license gives you freedom; you can copy, convey,
# propagate, redistribute and/or modify this program under the terms of
# the GNU Affero General Public License (AGPL) as published by the Free
# Software Foundation (FSF), either version 3 of the License, or (at your
# option) any later version of the AGPL published by the FSF.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program in a file in the toplevel directory called
# "AGPLv3".  If not, see <http://www.gnu.org/licenses/>.
#

# PURPOSE OF THIS MODULE:
# problem-builder has a couple dependencies on models in the edx-platform
# repository. This comes with two challenges:
#  1. We cannot import from edx-platform during unit tests, because
#     it is not installed into the testing environment.
#  2. Some edx-platform import paths differ between Open edX releases.
# In the interest of performing these imports in a consistent way,
# we centralize the imports here, to be re-imported by other modules.

# pylint: disable=unused-import

try:
    # Koa and earlier: use shortened import path.
    # This will raise a warning in Koa, but that's OK.
    from courseware.models import StudentModule
    from static_replace import replace_static_urls
    from student.models import AnonymousUserId
    from xblock_django.models import XBlockConfiguration
except Exception:  # pylint: disable=broad-except
    # (catch broadly, since the exception could manifest as either an ImportError
    #  or an EdxPlatformDeprecatedImportError, the latter of which is not a subclass
    #  of the former, and only exists on edx-platform master between Koa and Lilac).
    try:
        # Post-Koa: we must use the full import path.
        from lms.djangoapps.courseware.models import StudentModule
        from common.djangoapps.static_replace import replace_static_urls
        from common.djangoapps.student.models import AnonymousUserId
        from common.djangoapps.xblock_django.models import XBlockConfiguration
    except ImportError:
        # If we get here, we are not running within edx-platform
        # (e.g., we are running problem-builder unit tests).
        StudentModule = None
        replace_static_urls = None
        AnonymousUserId = None
        XBlockConfiguration = None
