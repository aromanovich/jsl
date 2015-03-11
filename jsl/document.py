# coding: utf-8
from __future__ import unicode_literals

import inspect

from . import registry
from ._compat import iteritems, itervalues, with_metaclass
from .fields import BaseField, DocumentField, DictField


def set_owner_to_document_fields(cls):
    for field in itervalues(cls._fields):
        for field_ in field.walk(through_document_fields=False, visited_documents=set([cls])):
            if isinstance(field_, DocumentField):
                field_.set_owner(cls)


class Options(object):
    """
    A container for options. Its primary purpose is to create
    an instance of options for every instance of a :class:`Document`.

    All the arguments are the same and work exactly as for :class:`.fields.DictField`
    except these:

    :param definition_id:
        A unique string to be used as a key for this document in the "definitions"
        schema section. If not specified, will be generated using module and class names.
    :type definition_id: str
    :param schema_uri:
        An URI of the JSON Schema meta-schema.
    :type schema_uri: str
    """
    def __init__(self, additional_properties=False, pattern_properties=None,
                 min_properties=None, max_properties=None,
                 title=None, description=None,
                 default=None, enum=None,
                 definition_id=None, schema_uri='http://json-schema.org/draft-04/schema#'):
        self.pattern_properties = pattern_properties
        self.additional_properties = additional_properties
        self.min_properties = min_properties
        self.max_properties = max_properties
        self.title = title
        self.description = description
        self.enum = enum
        self.default = default
        self.definition_id = definition_id
        self.schema_uri = schema_uri


class DocumentMeta(type):
    """
    A metaclass for :class:`~.Document`. It's responsible for collecting fields and options,
    registering the document in the registry, making it the owner of nested
    :class:`~.DocumentField` s and so on.
    """
    options_container = Options
    """
    A class to be used by :meth:`~.DocumentMeta.create_options`.
    Must be a subclass of :class:`~.Options`.
    """

    def __new__(mcs, name, bases, attrs):
        fields = mcs.collect_fields(bases, attrs)
        options_data = mcs.collect_options(bases, attrs)
        options = mcs.create_options(options_data)

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
    def collect_fields(mcs, bases, attrs):
        """
        Collects fields from the current class and its parent classes.

        :rtype: a dictionary mapping field names to :class:`~jsl.document.BaseField` s
        """
        fields = {}
        # fields from parent classes:
        for base in reversed(bases):
            if hasattr(base, '_fields'):
                fields.update(base._fields)
        # and from the current class:
        for key, value in iteritems(attrs):
            if isinstance(value, BaseField):
                fields[key] = value
        return fields

    @classmethod
    def collect_options(mcs, bases, attrs):
        """
        Collects options from the current class and its parent classes.

        :rtype: a dictionary of options
        """
        options = {}
        # options from parent classes:
        for base in reversed(bases):
            if hasattr(base, '_options'):
                for key, value in inspect.getmembers(base._options):
                    if not key.startswith('_') and value is not None:
                        options[key] = value
        # options from the current class:
        if 'Options' in attrs:
            for key, value in inspect.getmembers(attrs['Options']):
                if not key.startswith('_') and value is not None:
                    options[key] = value
        return options

    @classmethod
    def create_options(cls, options):
        """
        Wraps ``options`` into a container class (see :attr:`~.DocumentMeta.options_container`).

        :param options: a dictionary of options
        :return: an instance of :attr:`~.DocumentMeta.options_container`
        """
        return cls.options_container(**options)


class Document(with_metaclass(DocumentMeta)):
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
        return cls._options.definition_id or '{0}.{1}'.format(cls.__module__, cls.__name__)

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


# Remove Document itself from registry
registry.remove_document(Document.__name__, module=Document.__module__)