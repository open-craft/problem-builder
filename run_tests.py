#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run tests for the Problem Builder XBlock

This script is required to run our selenium tests inside the xblock-sdk workbench
because the workbench SDK's settings file is not inside any python module.
"""

import os
import sys
import logging

logging_level_overrides = {
    'workbench.views': logging.ERROR,
    'django.request': logging.ERROR,
    'workbench.runtime': logging.ERROR,
}

def patch_broken_pipe_error():
    """Monkey Patch BaseServer.handle_error to not write a stacktrace to stderr on broken pipe.
    This message is automatically suppressed in Django 1.8, so this monkey patch can be
    removed once the workbench upgrades to Django >= 1.8.
    http://stackoverflow.com/a/22618740/51397"""

    import socket
    from SocketServer import BaseServer
    from wsgiref import handlers

    handle_error = BaseServer.handle_error
    log_exception = handlers.BaseHandler.log_exception

    def is_broken_pipe_error():
        exc_type, exc_value = sys.exc_info()[:2]
        if issubclass(exc_type, socket.error) and exc_value.args[0] == 32:
            return True
        return False

    def my_handle_error(self, request, client_address):
        if not is_broken_pipe_error():
            handle_error(self, request, client_address)

    def my_log_exception(self, exc_info):
        if not is_broken_pipe_error():
            log_exception(self, exc_info)

    BaseServer.handle_error = my_handle_error
    handlers.BaseHandler.log_exception = my_log_exception

if __name__ == "__main__":
    patch_broken_pipe_error()
    # Use the workbench settings file:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "workbench.settings")
    # Configure a range of ports in case the default port of 8081 is in use
    os.environ.setdefault("DJANGO_LIVE_TEST_SERVER_ADDRESS", "localhost:8081-8099")

    try:
        os.mkdir('var')
    except OSError:
        # May already exist.
        pass

    from django.conf import settings
    settings.INSTALLED_APPS += ("problem_builder", )

    for noisy_logger, log_level in logging_level_overrides.iteritems():
        logging.getLogger(noisy_logger).setLevel(log_level)

    from django.core.management import execute_from_command_line
    args = sys.argv[1:]
    paths = [arg for arg in args if arg[0] != '-']
    if not paths:
        paths = ["problem_builder/tests/", "problem_builder/v1/tests/"]
    options = [arg for arg in args if arg not in paths]
    execute_from_command_line([sys.argv[0], "test"] + paths + options)
