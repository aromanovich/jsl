# coding: utf-8
import sys
import os

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
if not on_rtd:
    import sphinx_rtd_theme

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
autoclass_content = 'both'

# Options for HTML output

if not on_rtd:
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = ['_static']
htmlhelp_basename = 'JSLdoc'
html_sidebars = {
    '**': [
        'about.html', 'navigation.html', 'searchbox.html', 'donate.html',
    ]
}

# Options for manual page output

man_pages = [
    ('index', 'jsl', u'JSL Documentation', [u'Anton Romanovich'], 1),
]




