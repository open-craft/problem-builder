# -*- coding: utf-8 -*-


# Imports ###########################################################

import logging
import os
import pkg_resources

from xblock.fragment import Fragment


# Globals ###########################################################

log = logging.getLogger(__name__)


# Functions #########################################################

def load_resource(resource_path):
    """
    Gets the content of a resource
    """
    resource_path = os.path.join('..', resource_path)
    resource_content = pkg_resources.resource_string(__name__, resource_path)
    return unicode(resource_content)

def eval_template(template_path, context={}):
    """
    Evaluate a template by resource path, applying the provided context
    """
    template = load_resource(template_path)
    return template.format(**context)

def create_fragment(template_path, context={}):
    """
    Returns a new fragment, with its HTML content initialized to the evaluated template,
    with the provided context
    """
    html = eval_template(template_path, context=context)
    return Fragment(html)


