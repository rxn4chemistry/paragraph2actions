import inspect
import itertools
from typing import List, Iterable, Any, Iterator, Tuple, Sequence

import attr

from .actions import Action, Chemical
from .actions import __dict__ as actions_module_dict  # type: ignore

temperature_attribute_names = ['temperature']
duration_attribute_names = ['duration']


def get_all_action_types() -> List[str]:
    """Returns a list of the available action names"""

    actions: List[str] = []
    for name, val in actions_module_dict.items():  # iterate through every module's attributes
        if inspect.isclass(val) and issubclass(val, Action) and val != Action:
            actions.append(name)

    return actions


def extract_chemicals(actions: Iterable[Action]) -> List[Chemical]:
    """
    Returns a list of all the chemicals present in a sequence of actions.
    """
    chemicals = []

    for a in actions:
        for value in a.__dict__.values():
            if isinstance(value, Chemical):
                chemicals.append(value)
            if isinstance(value, list):
                for v in value:
                    if isinstance(v, Chemical):
                        chemicals.append(v)

    return chemicals


def pairwise(s: List[Any]) -> Iterator[Tuple[Any, Any]]:
    """
    Iterates over neighbors in a list.

    s -> (s0,s1), (s1,s2), (s2, s3), ...

    From https://stackoverflow.com/a/5434936
    """

    a, b = itertools.tee(s)
    next(b, None)
    return zip(a, b)


def all_identical(sequence: Sequence[Any]) -> bool:
    return all(s == sequence[0] for s in sequence)


@attr.s(auto_attribs=True)
class Sentence:
    """
    Sentence from a synthesis recipe with the corresponding actions.
    """
    text: str
    actions: List[Action]
