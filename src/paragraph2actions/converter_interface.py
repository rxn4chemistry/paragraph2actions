from abc import ABC, abstractmethod
from typing import List

from .actions import Action


class ActionStringConverter(ABC):
    """
    Base class for the conversion of our custom action classes to and from strings.
    """

    @abstractmethod
    def action_type_supported(self, action_type: str) -> bool:
        """
        Whether the conversion to and from a given action type is supported by the converter.
        """

    @abstractmethod
    def actions_to_string(self, actions: List[Action]) -> str:
        """
        Converts a list of actions to a string representation.
        """

    @abstractmethod
    def string_to_actions(
        self, action_string: str, wrap_errors_into_invalidaction: bool = False
    ) -> List[Action]:
        """
        Converts a string representation to the corresponding list of actions.

        Args:
            action_string: string to convert to a list of actions
            wrap_errors_into_invalidaction: if True, exceptions raised during the
                conversion will be converted into an InvalidAction, without propagating
                the exception. Useful for instance to show feedback to a user if a
                single action failed out of many (in the UI).

        Raises:
            ActionStringConversionError.
        """
