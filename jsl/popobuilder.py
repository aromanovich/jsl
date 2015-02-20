import inspect

from . import fields


def get_module_classes(module):
    """Returns a list of classes defined in ``module``."""
    def accept(member):
        return inspect.isclass(member) and module.__name__ == member.__module__
    return inspect.getmembers(module, accept)


class PopoBuilder(object):
    @classmethod
    def get_pycharm_type_hint(cls, field):
        if isinstance(field, fields.BooleanField):
            hint = 'bool'
        elif isinstance(field, fields.StringField):
            hint = 'str'
        elif isinstance(field, fields.NumberField):
            hint = 'numbers.Number'
        elif isinstance(field, fields.IntField):
            hint = 'int'
        elif isinstance(field, fields.ArrayField):
            nested_field_hint = cls.get_pycharm_type_hint(field.items)
            hint = 'list[{}]'.format(nested_field_hint)
        elif isinstance(field, fields.DictField):
            hint = 'dist'
        elif isinstance(field, fields.OneOfField):
            nested_field_hints = [cls.get_pycharm_type_hint(f) for f in field.fields]
            hint = ' | '.join(nested_field_hints)
        elif isinstance(field, fields.DocumentField):
            hint = field.document_cls.__module__ + '.' + field.document_cls.__name__
        else:
            hint = None
        return hint

    def generate_docstring(self, document):
        lines = ['"""']
        for name, field in document._fields.iteritems():
            hint = self.get_pycharm_type_hint(field)
            if hint:
                line = ':type {0}: {1}'.format(name, hint)
                lines.append(line)
        lines.append('"""')
        return lines

    def generate_class(self, name, document):
        lines = ['class {}(popo.DotExpandedDict):'.format(name)]
        for docstring_line in self.generate_docstring(document):
            lines.append(' ' * 4 + docstring_line)
        for name, field in document._fields.iteritems():
            lines.append(' ' * 4 + '{0} = popo.Placeholder(\'{0}\')'.format(name))
        return lines

    def generate_module(self, classes):
        lines = ['from jsl import popo', '', '']
        for cls in classes:
            lines.extend(self.generate_class(cls.__name__, cls))
            lines.extend(['', ''])
        return lines


