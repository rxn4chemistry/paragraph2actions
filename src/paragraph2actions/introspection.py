from typing import Dict, List, Tuple, Type

import rxn.utilities.attrs

from .actions import Action


def get_variables(cls: Type[Action]) -> List[str]:
    """
    For a given action class, returns the names of the variables.
    """
    return rxn.utilities.attrs.get_variables(cls)


def get_variables_and_types(cls: Type[Action]) -> List[Tuple[str, Type]]:  # type: ignore[type-arg]
    """
    For a given action class, returns the names of the variables and their types.
    """
    return rxn.utilities.attrs.get_variables_and_types(cls)


def get_variables_and_type_names(cls: Type[Action]) -> List[Tuple[str, str]]:
    """
    For a given action class, returns the names of the variables and their type names.
    """
    return rxn.utilities.attrs.get_variables_and_type_names(cls)


def get_variable_type(cls: Type[Action], variable_name: str) -> Type:  # type: ignore[type-arg]
    """
    For a given action class and variable name, returns the type of that variable.
    """
    for name, variable_type in get_variables_and_types(cls):
        if name == variable_name:
            return variable_type
    raise ValueError(f'No variable "{variable_name}" for class {cls.__name__}')


def inspect_all_variables() -> Dict[str, List[str]]:
    """
    Returns a dictionary of all the action classes names with the corresponding variables.
    """
    return {
        action_cls.__name__: get_variables(action_cls)
        for action_cls in Action.__subclasses__()
    }


def inspect_all_variables_and_types() -> Dict[str, List[Tuple[str, str]]]:
    """
    Returns a dictionary of all the action classes names with the corresponding variables, and types.
    """
    return {
        action_cls.__name__: get_variables_and_type_names(action_cls)
        for action_cls in Action.__subclasses__()
    }
