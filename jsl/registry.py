# coding: utf-8
from __future__ import unicode_literals
"""
A registry of all documents.
"""

_documents_registry = {}


def get_document(name, module=None):
    if module:
        name = '{0}.{1}'.format(module, name)
    return _documents_registry[name]


def put_document(name, document_cls, module=None):
    if module:
        name = '{0}.{1}'.format(module, name)
    _documents_registry[name] = document_cls
