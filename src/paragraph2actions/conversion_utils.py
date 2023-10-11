import re
from typing import Callable, Generic, Iterable, List, Optional, Tuple, Type, TypeVar

import attr

from .actions import Action, Chemical

ActionType = TypeVar("ActionType", bound=Action)


class ActionStringConversionError(ValueError):
    """Exception raised for errors during conversion of actions to or from strings."""


class StringToActionError(ActionStringConversionError):
    """Exception raised when the error occurs in the string-to-action conversion."""

    def __init__(self, action_string: str, message: Optional[str] = None):
        self.action_string = action_string
        if message is None:
            message = f'Conversion from string to actions failed for "{action_string}".'
        super().__init__(message)


class ActionToStringError(ActionStringConversionError):
    """Exception raised when the error occurs in the action-to-string conversion."""


class UnsupportedType(ActionToStringError):
    def __init__(self, action_type: Type[Action]):
        self.unsupported_type = action_type.__name__
        super().__init__()


def uppercase_action_name(action: Action) -> str:
    return action.action_name.upper()


def uppercase_type_name(action_type: Type[Action]) -> str:
    return action_type.__name__.upper()


def get_property_from_split(sentence: str, prefix: str) -> Tuple[str, Optional[str]]:
    """
    Gets an optional property following a given prefix.

    Returns:
        Tuple: (sentence before splitting word, optional property)
    """
    separator = f"{prefix} "
    splits = sentence.split(separator)
    prop = separator.join(splits[1:]) if len(splits) > 1 else None
    return splits[0], prop


def chemicals_to_text(chemicals: Iterable[Chemical]) -> str:
    """Get a string representation for Chemical instances."""
    return " and ".join(chemical_to_string(c) for c in chemicals)


def text_to_chemicals(chemicals_text: str) -> List[Chemical]:
    """Get Chemical instances from their string representation."""
    chemicals_strings = chemicals_text.split(" and ")
    return [get_chemical(chemical_string) for chemical_string in chemicals_strings]


def get_chemical(text: str) -> Chemical:
    """
    Convert a string to a chemical.

    Input examples:
        4-butyloctane (5 ml)
        DMF
    """
    remaining, quantities = get_quantities(text)

    # replace the insecable space before the parenthesis back to a normal space
    compound_name = remaining.replace(" \u200C(", " (")

    return Chemical(name=compound_name, quantity=quantities)


def get_quantities(sentence: str) -> Tuple[str, List[str]]:
    match = re.match(r"^.*( \(.*\))$", sentence)
    if not match:
        return sentence, []
    full_match_string = match.group(1)
    # remove parentheses
    match_string = full_match_string[2:-1]
    quantities = match_string.split(", ")
    remaining = sentence.replace(full_match_string, "")
    return remaining, quantities


def chemical_to_string(c: Chemical) -> str:
    """
    Convert a chemical to a string
    """
    # if there is a parenthesis after a space, it may mess up for the
    # back-conversion of the quantities
    compound_name = c.name.replace(" (", " \u200C(")

    if not c.quantity:
        return compound_name
    else:
        quantity_str = ", ".join(c.quantity)
        return f"{compound_name} ({quantity_str})"


@attr.s(auto_attribs=True)
class SingleActionConverter(Generic[ActionType]):
    """
    Object to define the action-to-string and string-to-action conversion for
    a given action type.

    It is used in the ReadableConverter and relies on the principle that an action
    string will consist of the uppercase action type, followed by different
    segments for the associated properties.
    """

    action_type: Type[ActionType]
    action_to_text: Callable[[ActionType], str]
    text_to_action: Callable[[str], ActionType]

    def first_word(self) -> str:
        return uppercase_type_name(self.action_type)
