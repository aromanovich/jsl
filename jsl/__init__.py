# coding: utf-8
"""
JSL
===
A Python DSL for describing JSON schemas.
See http://jsl.rtfd.org/ for documentation.
:copyright: (c) 2015 Anton Romanovich
:license: BSD
"""

__title__ = 'JSL'
__author__ = 'Anton Romanovich'
__license__ = 'BSD'
__copyright__ = 'Copyright 2015 Anton Romanovich'
__version__ = '0.0.2'
__version_info__ = tuple(int(i) for i in __version__.split('.'))


from .document import Document
from .fields import *
