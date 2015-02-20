from jsl import Document, StringField, ArrayField, DocumentField, OneOfField, popobuilder


def test_y():
    class Entry(Document):
        name = StringField(required=True)

    class File(Entry):
        content = StringField(required=True)

    class Directory(Entry):
        content = ArrayField(OneOfField([
            DocumentField(File, as_ref=True),
            DocumentField('self')
        ]), required=True)

    lines = popobuilder.PopoBuilder().generate_module([
        Entry, File, Directory
    ])
    assert '\n'.join(lines) == '''from jsl import popo


class Entry(popo.DotExpandedDict):
    """
    :type name: str
    """
    name = popo.Placeholder('name')


class File(popo.DotExpandedDict):
    """
    :type content: str
    :type name: str
    """
    content = popo.Placeholder('content')
    name = popo.Placeholder('name')


class Directory(popo.DotExpandedDict):
    """
    :type content: list[test_popobuilder.File | test_popobuilder.Directory]
    :type name: str
    """
    content = popo.Placeholder('content')
    name = popo.Placeholder('name')

'''