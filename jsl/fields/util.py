import re
import sre_constants

from ..roles import Var


def validate_regex(regex):
    """
    :type regex: str
    :raises: ValueError
    :return:
    """
    try:
        re.compile(regex)
    except sre_constants.error as e:
        raise ValueError('Invalid regular expression: {0}'.format(e))


def validate(value_or_var, validator):
    if isinstance(value_or_var, Var):
        for _, value in value_or_var.values:
            validator(value)
    else:
        validator(value_or_var)