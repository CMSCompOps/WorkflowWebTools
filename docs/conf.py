import os
import sys
sys.path.insert(0, os.path.abspath('.'))
#sys.path.insert(0, os.path.abspath('../'))
#print sys.path
#sys.path.insert(0, os.path.abspath('../runserver'))


# -- Project information -----------------------------------------------------

project = 'WorkflowWebTools'
copyright = '2018, W.Si for CMS CompOps T&I'
author = 'W.Si for CMS CompOps T&I'

# The short X.Y version
version = ''
# The full version, including alpha/beta/rc tags
release = ''

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinx.ext.mathjax',
    'sphinxcontrib.programoutput',
    'sphinxcontrib.autoanysrc'
    ]

source_suffix = '.rst'

master_doc = 'index'

pygments_style = 'sphinx'

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
            "collapse_navigation" : False
            }
