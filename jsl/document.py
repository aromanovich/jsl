# coding: utf-8
from __future__ import unicode_literals

import inspect

from . import registry
from .fields import BaseField, DocumentField, DictField


def set_owner_to_document_fields(cls):
    for field in cls._fields.itervalues():
        for field_ in field.walk(through_document_fields=False, visited_documents=set([cls])):
            if isinstance(field_, DocumentField):
                field_.set_owner(cls)


class Options(object):
    """
    A container for options. Its primary purpose is to create
    an instance of options for every instance of a :class:`Document`.
    """
    def __init__(self, additional_properties=False, pattern_properties=None,
                 min_properties=None, max_properties=None,
                 title=None, description=None,
                 default=None, enum=None, schema_uri='http://json-schema.org/draft-04/schema#'):
        self.pattern_properties = pattern_properties
        self.additional_properties = additional_properties
        self.min_properties = min_properties
        self.max_properties = max_properties
        self.title = title
        self.description = description
        self.enum = enum
        self.default = default
        self.schema_uri = schema_uri


class DocumentMeta(type):
    def __new__(mcs, name, bases, attrs):
        fields = {}

        # accumulate fields from parent classes
        for base in reversed(bases):
            if hasattr(base, '_fields'):
                fields.update(base._fields)

        for key, value in attrs.iteritems():
            if isinstance(value, BaseField):
                fields[key] = value

        options = mcs._read_options(name, bases, attrs)
        attrs['_fields'] = fields
        attrs['_options'] = options
        attrs['_field'] = DictField(
            properties=fields,
            pattern_properties=options.pattern_properties,
            additional_properties=options.additional_properties,
            min_properties=options.min_properties,
            max_properties=options.max_properties,
            title=options.title,
            description=options.description,
            enum=options.enum,
            default=options.default
        )

        klass = type.__new__(mcs, name, bases, attrs)
        registry.put_document(klass.__name__, klass, module=klass.__module__)
        set_owner_to_document_fields(klass)
        return klass

    @classmethod
    def _read_options(mcs, name, bases, attrs):
        """
        Parses `DocumentOptions` instance into the options value attached to
        `Document` instances.
        """
        options_members = {}

        for base in reversed(bases):
            if hasattr(base, '_options'):
                for key, value in inspect.getmembers(base._options):
                    if not key.startswith('_') and key != 'get_schema':
                        options_members[key] = value

        if 'Options' in attrs:
            for key, value in inspect.getmembers(attrs['Options']):
                if not key.startswith('_') and key != 'get_schema':
                    options_members[key] = value

        return Options(**options_members)


class Document(object):
    """A document. Can be thought as a kind of :class:`.fields.DictField`, which
    properties are defined by the fields added to the document class.

    It can be tuned using special ``Options`` attribute (see :class:`.Options` for available settings).

    Example::

        class User(Document):
            class Options(object):
                title = 'User'
                description = 'A person who uses a computer or network service.'
            login = StringField(required=True)
    """
    __metaclass__ = DocumentMeta

    @classmethod
    def walk(cls, through_document_fields=False, visited_documents=frozenset()):
        """Yields nested fields in DFS order.

        :param through_document_fields:
            If true, visits fields of the nested documents.
        :type through_document_fields: bool
        :param visited_documents:
            Keeps track of already visited document classes.
        :type visited_documents: set
        """
        for field_ in cls._field.walk(through_document_fields=through_document_fields,
                                      visited_documents=visited_documents | set([cls])):
            yield field_

    @classmethod
    def _is_recursive(cls):
        """Returns if the document is recursive, i.e. has a DocumentField pointing to itself."""
        for field in cls.walk(through_document_fields=True, visited_documents=set([cls])):
            if isinstance(field, DocumentField):
                if field.document_cls == cls:
                    return True
        return False

    @classmethod
    def _get_definition_id(cls):
        """Returns a unique string to be used as a key for this document
        in the "definitions" schema section.
        """
        return '{0}.{1}'.format(cls.__module__, cls.__name__)

    @classmethod
    def get_schema(cls):
        """Returns a JSON schema (draft v4) of the document."""
        definitions, schema = cls.get_definitions_and_schema()
        if definitions:
            schema['definitions'] = definitions
        if cls._options.schema_uri is not None:
            schema['$schema'] = cls._options.schema_uri
        return schema

    @classmethod
    def get_definitions_and_schema(cls, ref_documents=None):
        """Returns a tuple of two elements.

        The second element is a JSON schema of the document, and the first is a dictionary
        containing definitions that are referenced from the schema.

        :arg ref_documents:
            If subclass of :class:`Document` is in this set, all :class:`DocumentField` s
            pointing to it will be resolved to a reference: ``{"$ref": "#/definitions/..."}``.
            Note: resulting definitions will not contain schema for this document.
        :type ref_documents: set
        :rtype: (dict, dict)
        """
        is_recursive = cls._is_recursive()

        if is_recursive:
            ref_documents = set(ref_documents) if ref_documents else set()
            ref_documents.add(cls)

        definitions, schema = cls._field.get_definitions_and_schema(ref_documents=ref_documents)

        if is_recursive:
            definition_id = cls._get_definition_id()
            definitions[definition_id] = schema
            return definitions, {'$ref': '#/definitions/{0}'.format(definition_id)}
        else:
            return definitions, schema
