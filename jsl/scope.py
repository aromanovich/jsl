from ._compat import urljoin, urldefrag


class ResolutionScope(object):
    """An utility class to help with translating :class:`.fields.BaseSchemaField` s into
    schema identifiers.

    :param base:
        A resolution scope of the outermost schema.
    :type base: URI, string
    :param current:
        A resolution scope of the current schema.
    :type current: URI, string
    :param output:
        An output part (expressed by parent schema id properties) scope of
        the current schema.
    :type output: URI, string
    """
    def __init__(self, base='', current='', output=''):
        self._base, _ = urldefrag(base)
        self._current, _ = urldefrag(current)
        self._output, _ = urldefrag(output)

    def __repr__(self):
        return 'ResolutionScope(\n  base={0},\n  current={1},\n  output={2}\n)'.format(
            self._base, self._current, self._output)

    def replace(self, current=None, output=None):
        """Returns a new :class:`~.ResolutionScope` with specified current and
        output scopes.
        """
        return ResolutionScope(
            base=self._base,
            current=self._current if current is None else current,
            output=self._output if output is None else output
        )

    def alter(self, field_id):
        """Returns a pair, where the first element is an identifier to be used
        in "id" schema field and the second is a new :class:`~.ResolutionScope`
        altered by the ``field_id``.
        """
        new_current = urljoin(self._current or self._base, field_id)
        if new_current.startswith(self._output):
            schema_id = new_current[len(self._output):]
        else:
            schema_id = new_current
        return schema_id, self.replace(current=new_current, output=new_current)

    def create_ref(self, definition_id):
        """Returns a reference (``{"$ref": ...}`` dictionary) related to the base scope."""
        ref = '{0}#/definitions/{1}'.format(
            self._base if self._current and self._base != self._current else '',
            definition_id
        )
        return {'$ref': ref}