"""
Generates Mako templates
"""

import os

import mako.lookup

from .. import serverconfig

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             'templates')

def render(template, **kwargs):
    """
    Function to generate mako template

    :param str template: Name of the mako template to generate
    :param kwargs: The keywords to pass to the rendered template
    :returns: Rendered webpage from the selected template
    :rtype: str
    """

    return mako.lookup.TemplateLookup(
        directories=[TEMPLATES_DIR],
        module_directory=os.path.join(
            serverconfig.config_dict()['workspace'], 'mako_modules')
        ).get_template(template).render(**kwargs)
