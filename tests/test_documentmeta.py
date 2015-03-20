# coding: utf-8
import mock

from jsl import fields
from jsl._compat import iteritems, with_metaclass
from jsl.document import Document, DocumentMeta, Options


class OptionsStub(Options):
    """An options container that allows storing extra options."""
    def __init__(self, a=None, b=None, c=None, d=None, **kwargs):
        super(OptionsStub, self).__init__(**kwargs)
        self.a = a
        self.b = b
        self.c = c
        self.d = d


def test_collect_fields_and_options():
    with mock.patch.object(DocumentMeta, 'options_container', wraps=OptionsStub):
        class ParentOne(Document):
            a = fields.StringField()
            b = fields.IntField()
            c = fields.NumberField()

            class Options(object):
                a = 1
                b = 1
                c = 1

        class ParentTwo(Document):
            b = fields.DictField()

            class Options:
                b = 2
                d = 2

    bases = (ParentTwo, ParentOne)
    attrs = {
        'c': fields.BooleanField(),
        'd': fields.BooleanField(),
    }

    fields_dict = DocumentMeta.collect_fields(bases, attrs)
    assert fields_dict == {
        'a': ParentOne.a,
        'b': ParentTwo.b,
        'c': attrs['c'],
        'd': attrs['d'],
    }

    options_dict = DocumentMeta.collect_options(bases, attrs)
    for expected_key, expected_value in iteritems({
        'a': 1,
        'b': 2,
        'c': 1,
        'd': 2
    }):
        assert options_dict[expected_key] == expected_value


def test_overriding_options_container():
    class ParameterOptions(Options):
        def __init__(self, repeated=None, location=None, annotations=None, **kwargs):
            super(ParameterOptions, self).__init__(**kwargs)
            self.repeated = repeated
            self.location = location
            self.annotations = annotations

    class ParameterMeta(DocumentMeta):
        options_container = ParameterOptions

    class Parameter(with_metaclass(ParameterMeta, Document)):
        class Options(object):
            repeated = True
            location = 'query'
            title = 'Parameter'

    assert Parameter._options.repeated
    assert Parameter._options.location == 'query'
    assert Parameter._options.title == 'Parameter'
