# coding: utf-8
import sys
import os

sys.path.insert(0, os.path.abspath('../..'))

import jsl

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

project = u'JSL'
copyright = u'2015, Anton Romanovich'
version = jsl.__version__
release = jsl.__version__

language = 'en'
pygments_style = 'sphinx'
autodoc_member_order = 'bysource'

# Options for HTML output

html_theme = 'nature'
html_theme_options = {}
html_static_path = ['_static']
htmlhelp_basename = 'JSLdoc'

# Options for manual page output

man_pages = [
    ('index', 'jsl', u'JSL Documentation', [u'Anton Romanovich'], 1),
]