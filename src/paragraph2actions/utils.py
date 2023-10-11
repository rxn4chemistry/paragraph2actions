import inspect
import itertools
from typing import Any, Callable, Iterable, Iterator, List, Optional, Sequence, Tuple

import attr

from .actions import Action, Chemical
from .actions import __dict__ as actions_module_dict  # type: ignore

temperature_attribute_names = ["temperature"]
duration_attribute_names = ["duration"]
atmosphere_attribute_names = ["atmosphere"]
compound_attribute_names = [
    "gas",
    "material",
    "material_1",
    "material_2",
    "materials",
    "solvent",
]


def get_all_action_types() -> List[str]:
    """Returns a list of the available action names"""

    actions: List[str] = []
    for (
        name,
        val,
    ) in actions_module_dict.items():  # iterate through every module's attributes
        if inspect.isclass(val) and issubclass(val, Action) and val != Action:
            actions.append(name)

    return actions


def extract_chemicals(
    actions: Iterable[Action], ignore_sln: bool = False
) -> List[Chemical]:
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

    if ignore_sln:
        chemicals = [chemical for chemical in chemicals if chemical.name != "SLN"]

    return chemicals


def actions_with_compounds(actions: Iterable[Action]) -> List[Tuple[Action, str]]:
    """
    In a list of actions, looks for the ones having a compound (that may be
    set or not).

    Returns them as a list of actions paired with the name of the member
    variable corresponding to the compound. Includes both compounds specified
    as strings and as instances of Chemical.
    """

    return _actions_with_attribute_names(actions, compound_attribute_names)


def extract_compound_names(
    actions: Iterable[Action], ignore_sln: bool = True
) -> List[str]:
    """
    Returns a list of all the compounds (as strings) present in a sequence of
    actions.

    Will not only return the ones corresponding to the Chemical instances
    extracted by extract_chemicals, but also the ones that are present only
    as strings such as Degas.gas or DrySolution.material.
    """

    compounds = []

    for action, attribute_name in actions_with_compounds(actions):
        value = getattr(action, attribute_name)
        if value is None:
            continue
        elif isinstance(value, str):
            compounds.append(value)
        elif isinstance(value, Chemical):
            compounds.append(value.name)
        elif isinstance(value, list):
            for element in value:
                if isinstance(element, Chemical):
                    compounds.append(element.name)

    if ignore_sln:
        compounds = [compound for compound in compounds if compound != "SLN"]

    return compounds


def _actions_with_attribute_names(
    actions: Iterable[Action], attribute_names: Sequence[str]
) -> List[Tuple[Action, str]]:
    """
    In a list of actions, looks for the ones having a given attribute names
    (that may be set or not).

    Useful for actions_with_temperatures or actions_with_durations, for
    instance. Returns them as a list of actions paired with the name of the
    member variable.
    """
    tuples: List[Tuple[Action, str]] = []

    for a in actions:
        for attribute_name in attribute_names:
            if hasattr(a, attribute_name):
                tuples.append((a, attribute_name))

    return tuples


def _apply_to_actions_with_attribute_names(
    actions: Iterable[Action],
    attribute_names: Sequence[str],
    fn: Callable[[str], Optional[str]],
) -> None:
    """
    Applies a function of all the duration fields present in the given actions,
    to update their values.

    Args:
        actions: actions on which to apply fn
        attribute_names: attribute names to apply to
        fn: function to apply to the durations, basically doing
            `action.<attribute_name> = fn(action.<attribute_name>)`
    """
    actions_and_attributes = _actions_with_attribute_names(actions, attribute_names)

    for a, attribute_name in actions_and_attributes:
        value = getattr(a, attribute_name, None)

        # do nothing if there is no value (f.i. optional variables)
        if value is None:
            continue

        # set the new value
        new_value = fn(value)
        setattr(a, attribute_name, new_value)


def apply_to_temperatures(actions: Iterable[Action], fn: Callable[[str], str]) -> None:
    """
    Applies a function of all the temperature fields present in the given
    actions, to update their values.

    Args:
        actions: actions on which to apply fn
        fn: function to apply to the temperatures, basically doing
            `action.temperature = fn(action.temperature)`
    """
    _apply_to_actions_with_attribute_names(actions, temperature_attribute_names, fn)


def apply_to_durations(actions: Iterable[Action], fn: Callable[[str], str]) -> None:
    """
    Applies a function of all the duration fields present in the given actions,
    to update their values.

    Args:
        actions: actions on which to apply fn
        fn: function to apply to the durations, basically doing
            `action.duration = fn(action.duration)`
    """
    _apply_to_actions_with_attribute_names(actions, duration_attribute_names, fn)


def apply_to_atmospheres(
    actions: Iterable[Action], fn: Callable[[str], Optional[str]]
) -> None:
    """
    Applies a function of all the atmosphere fields present in the given actions,
    to update their values.

    Args:
        actions: actions on which to apply fn
        fn: function to apply to the atmospheres, basically doing
            `action.atmosphere = fn(action.atmosphere)`
    """
    _apply_to_actions_with_attribute_names(actions, atmosphere_attribute_names, fn)


def actions_with_temperatures(actions: Iterable[Action]) -> List[Tuple[Action, str]]:
    """
    In a list of actions, looks for the ones having a temperature (that may be
    set or not).

    Returns them as a list of actions paired with the name of the member
    variable corresponding to the temperature.
    """

    return _actions_with_attribute_names(actions, temperature_attribute_names)


def actions_with_durations(actions: Iterable[Action]) -> List[Tuple[Action, str]]:
    """
    In a list of actions, looks for the ones having a duration (that may be
    set or not).

    Returns them as a list of actions paired with the name of the member
    variable corresponding to the duration.
    """

    return _actions_with_attribute_names(actions, duration_attribute_names)


def extract_temperatures(actions: Iterable[Action]) -> List[str]:
    """
    Returns a list of all the temperatures present in a sequence of actions.
    """
    temperatures = []

    for action, attribute_name in actions_with_temperatures(actions):
        value = getattr(action, attribute_name)
        if value is not None:
            temperatures.append(value)

    return temperatures


def extract_durations(actions: Iterable[Action]) -> List[str]:
    """
    Returns a list of all the durations present in a sequence of actions.
    """
    durations = []

    for action, attribute_name in actions_with_durations(actions):
        value = getattr(action, attribute_name)
        if value is not None:
            durations.append(value)

    return durations


def remove_quantities(actions: Iterable[Action]) -> None:
    """Remove the quantities of a list of actions in-place."""
    chemicals = extract_chemicals(actions)
    for chemical in chemicals:
        chemical.quantity = []


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
