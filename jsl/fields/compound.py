# coding: utf-8
import itertools

from .. import registry
from ..roles import DEFAULT_ROLE, Resolvable, Var
from ..resolutionscope import EMPTY_SCOPE
from .._compat import iteritems, iterkeys, itervalues, string_types, OrderedDict
from .base import BaseSchemaField, BaseField
from .util import validate_regex


__all__ = [
    'ArrayField', 'DictField', 'OneOfField', 'AnyOfField', 'AllOfField',
    'NotField', 'DocumentField', 'RECURSIVE_REFERENCE_CONSTANT'
]

RECURSIVE_REFERENCE_CONSTANT = 'self'


class ArrayField(BaseSchemaField):
    """An array field.

    :param items:
        Either of the following:

        * :class:`BaseField` -- all items of the array must match the field schema;
        * a list or a tuple of :class:`BaseField` s -- all items of the array must be
          valid according to the field schema at the corresponding index (tuple typing).

    :param min_items:
        A minimum length of an array.
    :type min_items: int or :class:`Var`
    :param max_items:
        A maximum length of an array.
    :type max_items: int or :class:`Var`
    :param unique_items:
        Whether all the values in the array must be distinct.
    :type unique_items: bool or :class:`Var`
    :param additional_items:
        If the value of ``items`` is a list or a tuple, and the array length is larger than
        the number of fields in ``items``, then the additional items are described
        by the :class:`BaseField` passed using this argument.
    :type additional_items: bool or :class:`BaseField` or :class:`Var`
    """

    def __init__(self, items=None, additional_items=None,
                 min_items=None, max_items=None, unique_items=None, **kwargs):
        self.items = items
        self.min_items = min_items
        self.max_items = max_items
        self.unique_items = unique_items
        self.additional_items = additional_items
        super(ArrayField, self).__init__(**kwargs)

    def get_definitions_and_schema(self, role=DEFAULT_ROLE, res_scope=EMPTY_SCOPE,
                                   ordered=False, ref_documents=None):
        id, res_scope = res_scope.alter(self.id)
        schema = (OrderedDict if ordered else dict)(type='array')
        schema = self._update_schema_with_common_fields(schema, id=id, role=role)
        nested_definitions = {}

        items, items_role = self.resolve_attr('items', role)
        if items is not None:
            if isinstance(items, (list, tuple)):
                items_schema = []
                for item in items:
                    item, item_role = item.resolve(items_role)
                    item_definitions, item_schema = item.get_definitions_and_schema(
                        role=item_role,
                        res_scope=res_scope, ordered=ordered, ref_documents=ref_documents)
                    nested_definitions.update(item_definitions)
                    items_schema.append(item_schema)
            else:
                items_definitions, items_schema = items.get_definitions_and_schema(
                    role=items_role, res_scope=res_scope, ordered=ordered,
                    ref_documents=ref_documents)
                nested_definitions.update(items_definitions)
            schema['items'] = items_schema

        additional_items, additional_items_role = self.resolve_attr('additional_items', role)
        if additional_items is not None:
            if isinstance(additional_items, bool):
                schema['additionalItems'] = additional_items
            else:
                items_definitions, items_schema = additional_items.get_definitions_and_schema(
                    role=additional_items_role,
                    res_scope=res_scope, ordered=ordered, ref_documents=ref_documents)
                schema['additionalItems'] = items_schema
                nested_definitions.update(items_definitions)

        min_items = self.resolve_attr('min_items', role).value
        if min_items is not None:
            schema['minItems'] = min_items
        max_items = self.resolve_attr('max_items', role).value
        if max_items is not None:
            schema['maxItems'] = max_items
        unique_items = self.resolve_attr('unique_items', role).value
        if unique_items is not None:
            schema['uniqueItems'] = unique_items
        return nested_definitions, schema

    def iter_all_fields(self):
        rv = []
        if isinstance(self.items, (list, tuple)):
            for item in self.items:
                rv.append(item.iter_values())
        elif isinstance(self.items, Resolvable):
            for items_value in self.items.iter_values():
                if isinstance(items_value, (list, tuple)):
                    for item in items_value:
                        rv.append(item.iter_values())
                else:
                    rv.append(items_value.iter_values())
        if isinstance(self.additional_items, Resolvable):
            rv.append(self.additional_items.iter_values())
        return itertools.chain.from_iterable(rv)

    def iter_fields(self, role=DEFAULT_ROLE):
        items, items_role = self.resolve_attr('items', role)
        if isinstance(items, (list, tuple)):
            for item in items:
                if isinstance(item, Resolvable):
                    item_value = item.resolve(items_role).value
                    if isinstance(item_value, BaseField):
                        yield item_value
        elif isinstance(items, Resolvable):
            yield items
        additional_items = self.resolve_attr('additional_items', role).value
        if isinstance(additional_items, BaseField):
            yield additional_items


class DictField(BaseSchemaField):
    """A dictionary field.

    :param properties:
        A dictionary containing fields.
    :type properties: dict from str to :class:`BaseField` or :class:`Var`
    :param pattern_properties:
        A dictionary whose keys are regular expressions (ECMA 262).
        Properties match against these regular expressions, and for any that match,
        the property is described by the corresponding field schema.
    :type pattern_properties: dict from str to :class:`BaseField` or :class:`Var`
    :param additional_properties:
        Describes properties that are not described by the ``properties`` or ``pattern_properties``.
    :type additional_properties: bool or :class:`BaseField` or :class:`Var`
    :param min_properties:
        A minimum number of properties.
    :type min_properties: int or :class:`Var`
    :param max_properties:
        A maximum number of properties
    :type max_properties: int or :class:`Var`
    """

    def __init__(self, properties=None, pattern_properties=None, additional_properties=None,
                 min_properties=None, max_properties=None, **kwargs):
        self.properties = properties
        self.pattern_properties = pattern_properties
        self.additional_properties = additional_properties
        self.min_properties = min_properties
        self.max_properties = max_properties
        super(DictField, self).__init__(**kwargs)

    def _process_properties(self, properties, res_scope, ordered=False,
                            ref_documents=None, role=DEFAULT_ROLE):
        nested_definitions = {}
        schema = OrderedDict() if ordered else {}
        required = []
        for prop, field in iteritems(properties):
            field, field_role = field.resolve(role)
            if field is None:
                continue
            field_definitions, field_schema = field.get_definitions_and_schema(
                role=field_role, res_scope=res_scope, ordered=ordered, ref_documents=ref_documents)
            if field.resolve_attr('required', field_role).value:
                required.append(prop)
            schema[prop] = field_schema
            nested_definitions.update(field_definitions)
        return nested_definitions, required, schema

    def get_definitions_and_schema(self, role=DEFAULT_ROLE, res_scope=EMPTY_SCOPE,
                                   ordered=False, ref_documents=None):
        id, res_scope = res_scope.alter(self.id)
        schema = (OrderedDict if ordered else dict)(type='object')
        schema = self._update_schema_with_common_fields(schema, id=id, role=role)
        nested_definitions = {}

        properties, properties_role = self.resolve_attr('properties', role)
        if properties is not None:
            properties_definitions, properties_required, properties_schema = \
                self._process_properties(properties, res_scope, ordered=ordered,
                                         ref_documents=ref_documents, role=properties_role)
            schema['properties'] = properties_schema
            if properties_required:
                schema['required'] = properties_required
            nested_definitions.update(properties_definitions)

        pattern_properties, pattern_properties_role = self.resolve_attr('pattern_properties', role)
        if pattern_properties is not None:
            for key in iterkeys(pattern_properties):
                validate_regex(key)
            properties_definitions, _, properties_schema = self._process_properties(
                pattern_properties, res_scope, ordered=ordered, ref_documents=ref_documents,
                role=pattern_properties_role)
            schema['patternProperties'] = properties_schema
            nested_definitions.update(properties_definitions)

        additional_properties, additional_properties_role = \
            self.resolve_attr('additional_properties', role)
        if additional_properties is not None:
            if isinstance(additional_properties, bool):
                schema['additionalProperties'] = additional_properties
            else:
                properties_definitions, properties_schema = \
                    additional_properties.get_definitions_and_schema(
                        role=additional_properties_role,
                        res_scope=res_scope, ordered=ordered, ref_documents=ref_documents)
                schema['additionalProperties'] = properties_schema
                nested_definitions.update(properties_definitions)

        min_properties = self.resolve_attr('min_properties', role).value
        if min_properties is not None:
            schema['minProperties'] = min_properties
        max_properties = self.resolve_attr('max_properties', role).value
        if max_properties is not None:
            schema['maxProperties'] = max_properties

        return nested_definitions, schema

    def iter_all_fields(self):
        def _extract_resolvables(dict_or_resolvable):
            rv = []
            possible_dicts = []
            if isinstance(dict_or_resolvable, Resolvable):
                possible_dicts = dict_or_resolvable.iter_values()
            elif isinstance(dict_or_resolvable, dict):
                possible_dicts = [dict_or_resolvable]
            for possible_dict in possible_dicts:
                rv.extend(v for v in itervalues(possible_dict) if v is not None)
            return rv

        resolvables = _extract_resolvables(self.properties)
        resolvables.extend(_extract_resolvables(self.pattern_properties))
        if isinstance(self.additional_properties, Resolvable):
            resolvables.append(self.additional_properties)
        return itertools.chain.from_iterable(r.iter_values() for r in resolvables)

    def iter_fields(self, role=DEFAULT_ROLE):
        properties, properties_role = self.resolve_attr('properties', role)
        if properties is not None:
            for field in itervalues(properties):
                field = field.resolve(properties_role).value
                if isinstance(field, BaseField):
                    yield field
        pattern_properties, pattern_properties_role = self.resolve_attr('pattern_properties', role)
        if pattern_properties is not None:
            for field in itervalues(pattern_properties):
                field = field.resolve(pattern_properties_role).value
                if isinstance(field, BaseField):
                    yield field
        additional_properties = self.resolve_attr('additional_properties', role).value
        if isinstance(additional_properties, BaseField):
            yield additional_properties


class BaseOfField(BaseSchemaField):
    _KEYWORD = None

    def __init__(self, fields, **kwargs):
        self.fields = fields
        super(BaseOfField, self).__init__(**kwargs)

    def get_definitions_and_schema(self, role=DEFAULT_ROLE, res_scope=EMPTY_SCOPE,
                                   ordered=False, ref_documents=None):
        id, res_scope = res_scope.alter(self.id)
        schema = OrderedDict() if ordered else {}
        schema = self._update_schema_with_common_fields(schema, id=id)
        nested_definitions = {}

        one_of = []
        fields, fields_role = self.resolve_attr('fields', role)
        if fields is not None:
            for field in fields:
                field, field_role = field.resolve(fields_role)
                if isinstance(field, BaseField):
                    field_definitions, field_schema = field.get_definitions_and_schema(
                        role=field_role, res_scope=res_scope,
                        ordered=ordered, ref_documents=ref_documents)
                    nested_definitions.update(field_definitions)
                    one_of.append(field_schema)
        schema[self._KEYWORD] = one_of
        return nested_definitions, schema

    def iter_all_fields(self):
        resolvables = []
        if isinstance(self.fields, (list, tuple)):
            resolvables.extend(self.fields)
        if isinstance(self.fields, Resolvable):
            for fields in self.fields.iter_values():
                if isinstance(fields, (list, tuple)):
                    resolvables.extend(fields)
                elif isinstance(fields, Resolvable):
                    resolvables.append(fields)
        return itertools.chain.from_iterable(r.iter_values() for r in resolvables)

    def iter_fields(self, role=DEFAULT_ROLE):
        fields, fields_role = self.resolve_attr('fields', role)
        for field in fields:
            field = field.resolve(fields_role).value
            if isinstance(field, BaseField):
                yield field


class OneOfField(BaseOfField):
    """
    :param fields: a list of fields, exactly one of which describes the data
    :type fields: list whose elements are :class:`BaseField` s or :class:`Var` s
    """
    _KEYWORD = 'oneOf'


class AnyOfField(BaseOfField):
    """
    :param fields: a list of fields, at least one of which describes the data
    :type fields: list whose elements are :class:`BaseField` s or :class:`Var` s
    """
    _KEYWORD = 'anyOf'


class AllOfField(BaseOfField):
    """
    :param fields: a list of fields, all of which describe the data
    :type fields: list whose elements are :class:`BaseField` s or :class:`Var` s
    """
    _KEYWORD = 'allOf'


class NotField(BaseSchemaField):
    """
    :param field: a field to negate
    :type field: :class:`BaseField` or :class:`Var`
    """

    def __init__(self, field, **kwargs):
        self.field = field
        super(NotField, self).__init__(**kwargs)

    def iter_all_fields(self):
        return self.field.iter_values()

    def iter_fields(self, role=DEFAULT_ROLE):
        field, field_role = self.resolve_attr('field', role)
        if isinstance(field, BaseField):
            yield field

    def get_definitions_and_schema(self, role=DEFAULT_ROLE, res_scope=EMPTY_SCOPE,
                                   ordered=False, ref_documents=None):
        id, res_scope = res_scope.alter(self.id)
        schema = OrderedDict() if ordered else {}
        schema = self._update_schema_with_common_fields(schema, id=id, role=role)
        field, field_role = self.resolve_attr('field', role)
        if isinstance(field, BaseField):
            field_definitions, field_schema = field.get_definitions_and_schema(
                role=field_role, res_scope=res_scope,
                ordered=ordered, ref_documents=ref_documents)
        else:
            field_definitions = {}
            field_schema = {}
        schema['not'] = field_schema
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
        """
        :type document_cls: basestring or BaseField
        """
        self._document_cls = document_cls
        self.owner_cls = None
        self.as_ref = as_ref
        super(DocumentField, self).__init__(**kwargs)

    def iter_all_fields(self):
        return self.document_cls.iter_all_fields()

    def walk_all(self, through_document_fields=False, visited_documents=frozenset()):
        yield self
        if through_document_fields:
            document_cls = self.document_cls
            if document_cls not in visited_documents:
                visited_documents = visited_documents | set([document_cls])
                for field in document_cls.walk_all(
                        through_document_fields=through_document_fields,
                        visited_documents=visited_documents):
                    yield field

    def walk(self, role=DEFAULT_ROLE,
             through_document_fields=False, visited_documents=frozenset()):
        yield self
        if through_document_fields:
            document_cls = self.document_cls
            new_role = DEFAULT_ROLE
            if self.owner_cls:
                if self.owner_cls._options.roles_to_propagate(role):
                    new_role = role
            else:
                new_role = role
            if document_cls not in visited_documents:
                visited_documents = visited_documents | set([document_cls])
                for field in document_cls.walk(
                        role=new_role,
                        through_document_fields=through_document_fields,
                        visited_documents=visited_documents):
                    yield field

    def get_definitions_and_schema(self, role=DEFAULT_ROLE, res_scope=EMPTY_SCOPE,
                                   ordered=False, ref_documents=None):
        document_cls = self.document_cls
        definition_id = document_cls.get_definition_id()
        if ref_documents and document_cls in ref_documents:
            return {}, res_scope.create_ref(definition_id)
        else:
            new_role = DEFAULT_ROLE
            if self.owner_cls:
                if self.owner_cls._options.roles_to_propagate(role):
                    new_role = role
            else:
                new_role = role
            document_definitions, document_schema = document_cls.get_definitions_and_schema(
                role=new_role,
                res_scope=res_scope, ordered=ordered, ref_documents=ref_documents)
            if self.as_ref:
                document_definitions[definition_id] = document_schema
                return document_definitions, res_scope.create_ref(definition_id)
            else:
                return document_definitions, document_schema

    def set_owner(self, owner_cls):
        self.owner_cls = owner_cls

    @property
    def document_cls(self):
        document_cls = self._document_cls
        if isinstance(document_cls, string_types):
            if document_cls == RECURSIVE_REFERENCE_CONSTANT:
                if self.owner_cls is None:
                    raise ValueError('owner_cls is not set')
                document_cls = self.owner_cls
            else:
                try:
                    document_cls = registry.get_document(document_cls)
                except KeyError:
                    if self.owner_cls is None:
                        raise ValueError('owner_cls is not set')
                    document_cls = registry.get_document(document_cls,
                                                         module=self.owner_cls.__module__)
        return document_cls
