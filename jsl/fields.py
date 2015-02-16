# coding: utf-8
from __future__ import unicode_literals

import re
import sre_constants
import itertools

from . import registry


RECURSIVE_REFERENCE_CONSTANT = 'self'


def _validate_regex(regex):
    """
    :type regex: str
    :raises: ValueError
    :return:
    """
    try:
        re.compile(regex)
    except sre_constants.error as e:
        raise ValueError('Invalid regular expression: {0}'.format(e))


class BaseField(object):
    """A base class for fields in a JSL :class:`.document.Document`.
    Instances of this class may be added to a document to define its properties.

    :param required:
        If the field is required, defaults to False.
    """
    def __init__(self, required=False):
        self.required = required

    def get_definitions_and_schema(self, ref_documents=None):  # pragma: no cover
        """Returns a tuple of two elements.

        The second element is a JSON schema of the data described by this field,
        and the first is a dictionary containing definitions that are referenced
        from the field schema.

        :arg definitions:
            Overrides some of the nested :class:`DocumentField`s schemas.

            If :class:`DocumentField`'s document definition id (see :meth:`get_definition_id`)
            is in this dictionary, its value will be used instead of the document's schema.

        :type definitions: dict
        :rtype: (dict, dict)
        """
        raise NotImplementedError()

    def get_schema(self):
        """Returns a JSON schema (draft v4) of the data described by this field."""
        definitions, schema = self.get_definitions_and_schema()
        if definitions:
            schema['definitions'] = definitions
        return schema

    def walk(self, through_document_fields=False, visited_documents=frozenset()):
        """Yields nested fields in a DFS order."""
        yield self


class BaseSchemaField(BaseField):
    """A base class for fields that directly map to JSON Schema validator.

    :param required:
        If the field is required, defaults to False.
    :param default:
        The default value for this field. May be a callable.
    :param enum:
        A list of valid choices. May be a callable.
    :param title:
        A short explanation about the purpose of the data described by this field.
    :param description:
        A detailed explanation about the purpose of the data described by this field.
    """
    def __init__(self, default=None, enum=None, title=None, description=None, **kwargs):
        self.title = title
        self.description = description
        self._enum = enum
        self._default = default
        super(BaseSchemaField, self).__init__(**kwargs)

    @property
    def enum(self):
        enum = self._enum
        if callable(self._enum):
            enum = self._enum()
        return enum

    @property
    def default(self):
        default = self._default
        if callable(self._default):
            default = self._default()
        return default

    def _get_common_schema_fields(self):
        rv = {}
        if self.title is not None:
            rv['title'] = self.title
        if self.description is not None:
            rv['description'] = self.description
        if self.enum:
            rv['enum'] = list(self.enum)
        if self._default is not None:
            rv['default'] = self.default
        return rv


class BooleanField(BaseSchemaField):
    """A boolean field."""
    def get_definitions_and_schema(self, ref_documents=None):
        schema = {'type': 'boolean'}
        schema.update(self._get_common_schema_fields())
        return {}, schema


class StringField(BaseSchemaField):
    """A string field.

    :param pattern:
        A regular expression (ECMA 262) that a string value must match.
    :type pattern: string
    :param format:
        A semantic format of the string (for example, "date-time", "email", or "uri").
    :type format: string
    :param min_length:
        A minimum length.
    :type min_length: int
    :param max_length:
        A maximum length.
    :type max_length: int
    """
    _FORMAT = None

    def __init__(self, pattern=None, format=None, min_length=None, max_length=None, **kwargs):
        self.pattern = pattern
        if self.pattern is not None:
            _validate_regex(self.pattern)
        self.format = format or self._FORMAT
        self.max_length = max_length
        self.min_length = min_length
        super(StringField, self).__init__(**kwargs)

    def get_definitions_and_schema(self, ref_documents=None):
        schema = {'type': 'string'}
        schema.update(self._get_common_schema_fields())
        if self.pattern:
            schema['pattern'] = self.pattern
        if self.min_length is not None:
            schema['minLength'] = self.min_length
        if self.max_length is not None:
            schema['maxLength'] = self.max_length
        if self.format is not None:
            schema['format'] = self.format
        return {}, schema


class EmailField(StringField):
    """An email field."""
    _FORMAT = 'email'


class IPv4Type(StringField):
    """An IPv4 field."""
    _FORMAT = 'ipv4'


class DateTimeField(StringField):
    """An ISO 8601 formatted date-time field."""
    _FORMAT = 'date-time'


class UriField(StringField):
    """A URI field."""
    _FORMAT = 'uri'


class NumberField(BaseSchemaField):
    """A number field.

    :param multiple_of:
        A value must be a multiple of this factor.
    :param minimum:
        A minimum allowed value.
    :param exclusive_minimum:
        Whether a value is allowed to exactly equal the minimum.
    :param maximum:
        A maximum allowed value.
    :param exclusive_maximum:
        Whether a value is allowed to exactly equal the maximum.
    """
    _NUMBER_TYPE = 'number'

    def __init__(self, multiple_of=None, minimum=None, maximum=None,
                 exclusive_minimum=False, exclusive_maximum=False, **kwargs):
        self.multiple_of = multiple_of
        self.minimum = minimum
        self.exclusive_minimum = exclusive_minimum
        self.maximum = maximum
        self.exclusive_maximum = exclusive_maximum
        super(NumberField, self).__init__(**kwargs)

    def get_definitions_and_schema(self, ref_documents=None):
        schema = {'type': self._NUMBER_TYPE}
        schema.update(self._get_common_schema_fields())
        if self.multiple_of is not None:
            schema['multipleOf'] = self.multiple_of
        if self.minimum is not None:
            schema['minimum'] = self.minimum
        if self.exclusive_minimum:
            schema['exclusiveMinumum'] = True
        if self.maximum is not None:
            schema['maximum'] = self.maximum
        if self.exclusive_maximum:
            schema['exclusiveMaximum'] = True
        return {}, schema


class IntField(NumberField):
    """An integer field."""
    _NUMBER_TYPE = 'integer'


class ArrayField(BaseSchemaField):
    """An array field.

    :param items:
        Either of the following:

        * :class:`BaseField` -- all items of the array must match the field schema;
        * a list or a tuple of :class:`BaseField` s -- all items of the array must be
          valid according to the field schema at the corresponding index (tuple typing).

    :param min_items:
        A minimum length of an array.
    :type min_items: int
    :param max_items:
        A maximum length of an array.
    :type max_items: int
    :param unique_items:
        Whether all the values in the array must be distinct.
    :type unique_items: bool
    :param additional_items:
        If the value of ``items`` is a list or a tuple, and the array length is larger than
        the number of fields in ``items``, then the additional items are described
        by the schema in this property.
    :type unique_items: bool or :class:`BaseField`
    """
    def __init__(self, items, min_items=None, max_items=None, unique_items=False,
                 additional_items=None, **kwargs):
        self.items = items
        self.min_items = min_items
        self.max_items = max_items
        self.unique_items = unique_items
        self.additional_items = additional_items
        super(ArrayField, self).__init__(**kwargs)

    def get_definitions_and_schema(self, ref_documents=None):
        if isinstance(self.items, (list, tuple)):
            nested_definitions = {}
            nested_schema = []
            for item in self.items:
                item_definitions, item_schema = item.get_definitions_and_schema(
                    ref_documents=ref_documents)
                nested_definitions.update(item_definitions)
                nested_schema.append(item_schema)
        else:
            nested_definitions, nested_schema = self.items.get_definitions_and_schema(
                ref_documents=ref_documents)
        schema = {
            'type': 'array',
            'items': nested_schema,
        }
        schema.update(self._get_common_schema_fields())
        if self.min_items is not None:
            schema['minItems'] = self.min_items
        if self.max_items is not None:
            schema['maxItems'] = self.max_items
        if self.unique_items:
            schema['uniqueItems'] = True

        if self.additional_items is not None:
            if isinstance(self.additional_items, bool):
                schema['additionalItems'] = self.additional_items
            else:
                items_definitions, items_schema = self.additional_items.get_definitions_and_schema(
                    ref_documents=ref_documents)
                schema['additionalItems'] = items_schema
                nested_definitions.update(items_definitions)

        return nested_definitions, schema

    def walk(self, through_document_fields=False, visited_documents=frozenset()):
        yield self
        if isinstance(self.items, (list, tuple)):
            for field in self.items:
                for field_ in field.walk(through_document_fields=through_document_fields,
                                         visited_documents=visited_documents):
                    yield field_
        else:
            for field in self.items.walk(through_document_fields=through_document_fields,
                                         visited_documents=visited_documents):
                yield field


class DictField(BaseSchemaField):
    """A dictionary field.

    :param properties:
        A dictionary containing fields.
    :type properties: dict from str to :class:`BaseField`
    :param pattern_properties:
        A dictionary whose keys are regular expressions (ECMA 262).
        Properties match against these regular expressions, and for any that match,
        the property is described by the corresponding field schema.
    :type pattern_properties: dict from str to :class:`BaseField`
    :param additional_properties:
        Describes properties that are not described by the ``properties`` or ``pattern_properties``.
    :type additional_properties: bool or :class:`BaseField`
    :param min_properties:
        A minimum number of properties.
    :param max_properties:
        A maximum number of properties
    """
    def __init__(self, properties=None, pattern_properties=None, additional_properties=None,
                 min_properties=None, max_properties=None, **kwargs):
        self.properties = properties
        self.pattern_properties = pattern_properties
        self.additional_properties = additional_properties
        self.min_properties = min_properties
        self.max_properties = max_properties
        super(DictField, self).__init__(**kwargs)

    @staticmethod
    def _process_properties(properties, ref_documents=None):
        nested_definitions = {}
        schema = {}
        required = []
        for prop, field in properties.iteritems():
            field_definitions, field_schema = field.get_definitions_and_schema(ref_documents=ref_documents)
            if field.required:
                required.append(prop)
            schema[prop] = field_schema
            nested_definitions.update(field_definitions)
        return nested_definitions, required, schema

    def get_definitions_and_schema(self, ref_documents=None):
        nested_definitions = {}
        schema = {'type': 'object'}
        schema.update(self._get_common_schema_fields())

        if self.properties is not None:
            properties_definitions, properties_required, properties_schema = self._process_properties(
                self.properties, ref_documents=ref_documents)
            schema['properties'] = properties_schema
            if properties_required:
                schema['required'] = properties_required
            nested_definitions.update(properties_definitions)

        if self.pattern_properties is not None:
            for key in self.pattern_properties.iterkeys():
                _validate_regex(key)
            properties_definitions, _, properties_schema = self._process_properties(
                self.pattern_properties, ref_documents=ref_documents)
            schema['patternProperties'] = properties_schema
            nested_definitions.update(properties_definitions)

        if self.additional_properties is not None:
            if isinstance(self.additional_properties, bool):
                schema['additionalProperties'] = self.additional_properties
            else:
                properties_definitions, properties_schema = self.additional_properties.get_definitions_and_schema(
                    ref_documents=ref_documents)
                schema['additionalProperties'] = properties_schema
                nested_definitions.update(properties_definitions)

        if self.min_properties is not None:
            schema['minProperties'] = self.min_properties
        if self.max_properties is not None:
            schema['maxProperties'] = self.max_properties

        return nested_definitions, schema

    def walk(self, through_document_fields=False, visited_documents=frozenset()):
        fields_to_visit = []
        if self.properties is not None:
            fields_to_visit.append(self.properties.itervalues())
        if self.pattern_properties is not None:
            fields_to_visit.append(self.pattern_properties.itervalues())
        if self.additional_properties is not None and not isinstance(self.additional_properties, bool):
            fields_to_visit.append([self.additional_properties])

        yield self
        for field in itertools.chain(*fields_to_visit):
            for field_ in field.walk(through_document_fields=through_document_fields,
                                     visited_documents=visited_documents):
                yield field_


class BaseOfField(BaseSchemaField):
    _KEYWORD = None

    def __init__(self, fields, **kwargs):
        self.fields = list(fields)
        super(BaseOfField, self).__init__(**kwargs)

    def get_definitions_and_schema(self, ref_documents=None):
        nested_definitions = {}
        one_of = []
        for field in self.fields:
            field_definitions, field_schema = field.get_definitions_and_schema(ref_documents=ref_documents)
            nested_definitions.update(field_definitions)
            one_of.append(field_schema)
        schema = {self._KEYWORD: one_of}
        schema.update(self._get_common_schema_fields())
        return nested_definitions, schema

    def walk(self, through_document_fields=False, visited_documents=frozenset()):
        yield self
        for field in self.fields:
            for field_ in field.walk(through_document_fields=through_document_fields,
                                     visited_documents=visited_documents):
                yield field_


class OneOfField(BaseOfField):
    """
    :param fields: a list of fields, exactly one of which describes the data
    :type fields: list of :class:`BaseField`
    """
    _KEYWORD = 'oneOf'


class AnyOfField(BaseOfField):
    """
    :param fields: a list of fields, at least one of which describes the data
    :type fields: list of :class:`BaseField`
    """
    _KEYWORD = 'anyOf'


class AllOfField(BaseOfField):
    """
    :param fields: a list of fields, all of which describe the data
    :type fields: list of :class:`BaseField`
    """
    _KEYWORD = 'allOf'


class NotField(BaseSchemaField):
    """
    :param field: a field to negate
    :type field: :class:`BaseField`
    """
    def __init__(self, field, **kwargs):
        self.field = field
        super(NotField, self).__init__(**kwargs)

    def get_definitions_and_schema(self, ref_documents=None):
        field_definitions, field_schema = self.field.get_definitions_and_schema(
            ref_documents=ref_documents)
        schema = {'not': field_schema}
        schema.update(self._get_common_schema_fields())
        return field_definitions, schema


class DocumentField(BaseField):
    """A reference to a nested document.

    :param document_cls:
        A string (dot-separated path to document class, i.e. 'app.resources.User'),
        :data:`RECURSIVE_REFERENCE_CONSTANT` or a :class:`Document`
    :param as_ref:
        If true, ``document_cls``'s schema is placed into the definitions section, and
        the field schema is just a reference to it: ``{"$ref": "#/definitions/..."}``.
        Makes a resulting schema more readable.
    """
    def __init__(self, document_cls, as_ref=False, **kwargs):
        self._document_cls = document_cls
        self.owner_cls = None
        self.as_ref = as_ref
        super(DocumentField, self).__init__(**kwargs)

    def walk(self, through_document_fields=False, visited_documents=frozenset()):
        yield self
        if through_document_fields and self.document_cls not in visited_documents:
            for field in self.document_cls.walk(through_document_fields=through_document_fields,
                                                visited_documents=visited_documents | set([self.document_cls])):
                yield field

    def get_definitions_and_schema(self, ref_documents=None):
        definition_id = self.document_cls._get_definition_id()
        if ref_documents and self.document_cls in ref_documents:
            return {}, {'$ref': '#/definitions/{0}'.format(definition_id)}
        else:
            document_definitions, document_schema = self.document_cls.get_definitions_and_schema(
                ref_documents=ref_documents)
            if self.as_ref:
                document_definitions[definition_id] = document_schema
                return document_definitions, {'$ref': '#/definitions/{0}'.format(definition_id)}
            else:
                return document_definitions, document_schema

    def set_owner(self, owner_cls):
        self.owner_cls = owner_cls

    @property
    def document_cls(self):
        if isinstance(self._document_cls, basestring):
            if self._document_cls == RECURSIVE_REFERENCE_CONSTANT:
                if self.owner_cls is None:
                    raise ValueError('owner_cls is not set')
                return self.owner_cls
            else:
                try:
                    return registry.get_document(self._document_cls)
                except KeyError:
                    if self.owner_cls is None:
                        raise ValueError('owner_cls is not set')
                    return registry.get_document(self._document_cls, module=self.owner_cls.__module__)
        else:
            return self._document_cls
