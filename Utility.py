import difflib
from functools import reduce
from typing import List


def genDiff(before: str, after: str) -> str:
    """
    Generate a string showing the difference between the two input strings using difflib

    :param before: the string before change
    :param after: the string after change
    :return: string showing the difference between 2 strings in detail
    """

    before = before.splitlines(1)
    after = after.splitlines(1)

    diff = difflib.unified_diff(before, after)

    return ''.join(diff)


def genSubHuntingMap(huntingRange: List[List[str]]):
    return "{{HuntingRange/Alternative\n |" + reduce(lambda x, y: x + "|\n |" + y,
                                                     map(lambda row: reduce(lambda x, y: x + "|" + y, row),
                                                         huntingRange)) + "|\n}}"
