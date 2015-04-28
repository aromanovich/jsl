# coding: utf-8
from ..resolutionscope import ResolutionScope
from ..roles import Resolvable, Resolution, DEFAULT_ROLE, Var


__all__ = ['BaseField', 'BaseSchemaField']


class BaseField(Resolvable):
    """A base class for fields in a JSL :class:`.document.Document`.
    Instances of this class may be added to a document to define its properties.

    :param required:
        If the field is required, defaults to False.
    """

    def __init__(self, required=False):
        self.required = required

    # Resolvable methods

    def resolve(self, role):
        return Resolution(self, role)

    def iter_values(self):
        yield self

    # / Resolvable methods

    def get_definitions_and_schema(self, role=DEFAULT_ROLE, res_scope=ResolutionScope(),
                                   ordered=False, ref_documents=None):  # pragma: no cover
        """Returns a tuple of two elements.

        The second element is a JSON schema of the data described by this field,
        and the first is a dictionary containing definitions that are referenced
        from the field schema.

        :arg role:
            A role. TODO
        :type role: string
        :arg ordered:
            If True, the resulting schema is an OrderedDict and its properties are ordered
            in a sensible way, which makes it more readable.
        :type ordered: bool
        :arg res_scope:
            Current resolution scope.
        :type res_scope: :class:`.scope.ResolutionScope`
        :arg ref_documents:
            If subclass of :class:`Document` is in this set, all :class:`DocumentField` s
            pointing to it will be resolved to a reference: ``{"$ref": "#/definitions/..."}``.
            Note: resulting definitions will not contain schema for this document.
        :type ref_documents: set
        :rtype: (dict, dict)
        """
        raise NotImplementedError()

    def get_schema(self, ordered=False, role=DEFAULT_ROLE):
        """Returns a JSON schema (draft v4) of the data described by this field.

        :arg role:
            A role. TODO
        :type role: string
        :arg ordered:
            If True, the resulting schema is an OrderedDict and its properties are ordered
            in a sensible way, which makes it more readable.
        :type ordered: bool
        """
        definitions, schema = self.get_definitions_and_schema(ordered=ordered, role=role)
        if definitions:
            schema['definitions'] = definitions
        return schema

    def resolve_attr(self, attr, role=DEFAULT_ROLE):
        value = getattr(self, attr)
        if isinstance(value, Var):
            return value.resolve(role)
        return Resolution(value, role)


class BaseSchemaField(BaseField):
    """A base class for fields that directly map to JSON Schema validator.

    :param required:
        If the field is required, defaults to False.
    :type required: bool or :class:`Var`
    :param default:
        The default value for this field. May be a callable.
    :type default: any JSON-representable object, a callable or a :class:`Var`
    :param enum:
        A list of valid choices. May be a callable.
    :type enum: list, tuple, set or :class:`Var`
    :param title:
        A short explanation about the purpose of the data described by this field.
    :type title: string or :class:`Var`
    :param description:
        A detailed explanation about the purpose of the data described by this field.
    :type description: string or :class:`Var`
    """

    def __init__(self, id='', default=None, enum=None, title=None, description=None, **kwargs):
        self.id = id
        self.title = title
        self.description = description
        self._enum = enum
        self._default = default
        super(BaseSchemaField, self).__init__(**kwargs)

    def get_enum(self, role=DEFAULT_ROLE):
        enum = self.resolve_attr('_enum', role).value
        if callable(enum):
            enum = enum()
        return enum

    def get_default(self, role=DEFAULT_ROLE):
        default = self.resolve_attr('_default', role).value
        if callable(default):
            default = default()
        return default

    def get_definitions_and_schema(self, role=DEFAULT_ROLE, res_scope=ResolutionScope(),
                                   ordered=False, ref_documents=None):  # pragma: no cover
        raise NotImplementedError()

    def _update_schema_with_common_fields(self, schema, id='', role=DEFAULT_ROLE):
        if id:
            schema['id'] = id
        title = self.resolve_attr('title', role).value
        if title is not None:
            schema['title'] = title
        description = self.resolve_attr('description', role).value
        if description is not None:
            schema['description'] = description
        enum = self.get_enum(role=role)
        if enum:
            schema['enum'] = list(enum)
        default = self.get_default(role=role)
        if default is not None:
            schema['default'] = default
        return schema

    def iter_all_fields(self):
        return iter([])

    def walk_all(self, through_document_fields=False, visited_documents=frozenset()):
        """Yields nested fields in a DFS order."""
        yield self
        for field in self.iter_all_fields():
            for field_ in field.walk_all(through_document_fields=through_document_fields,
                                         visited_documents=visited_documents):
                yield field_

    def iter_fields(self, role=DEFAULT_ROLE):
        return iter([])

    def walk(self, role=DEFAULT_ROLE,
             through_document_fields=False, visited_documents=frozenset()):
        """Yields nested fields in a DFS order."""
        yield self
        for field in self.iter_fields(role=role):
            field, field_role = field.resolve(role)
            for field_ in field.walk(role=field_role,
                                     through_document_fields=through_document_fields,
                                     visited_documents=visited_documents):
                yield field_
