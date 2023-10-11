import logging
from collections import defaultdict
from typing import DefaultDict, Dict, Iterable, List, Optional, Type

from rxn.utilities.strings import remove_postfix

from .actions import Action, InvalidAction
from .conversion_utils import (
    ActionToStringError,
    SingleActionConverter,
    StringToActionError,
    UnsupportedType,
)
from .converter_interface import ActionStringConverter
from .default_converters import default_action_converters

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class ReadableConverter(ActionStringConverter):
    """
    Converter for synthesis actions to and from readable text.

    This class relies on registering converters. For the string-to-action conversion,
    there may be several converters for the same name. In this case, the priority
    follows which was registered first.
    """

    def __init__(
        self,
        separator: str = "; ",
        end_mark: str = ".",
        single_action_converters: Optional[Iterable[SingleActionConverter]] = None,  # type: ignore[type-arg]
    ):
        """
        Args:
            separator: string that will be inserted between the action strings.
            end_mark: string that will be added at the end of the action string.
            single_action_converters: converters to register. Defaults to the
                defaults ones from the default_converters.py module.
        """
        super().__init__()

        self.separator = separator
        self.end_mark = end_mark

        # If a compound name / duration contains the separator, the string
        # will be modified by adding a no-break space between the first and
        # second character.
        self.separator_substitute = self.separator[:1] + "\u200C" + self.separator[1:]

        self.mapping_action: Dict[Type[Action], SingleActionConverter] = {}  # type: ignore[type-arg]
        # Note: defaultdict, as there may be several action classes with the same name.
        self.mapping_uppercase_name: DefaultDict[str, List[SingleActionConverter]] = defaultdict(list)  # type: ignore[type-arg]

        if single_action_converters is None:
            single_action_converters = default_action_converters()

        self.register_many(single_action_converters)

    def register_many(self, action_converters: Iterable[SingleActionConverter]) -> None:  # type: ignore[type-arg]
        """Register several single-action converters."""
        for action_converter in action_converters:
            self.register(action_converter)

    def register(self, action_converter: SingleActionConverter) -> None:  # type: ignore[type-arg]
        """Register a single-action converter."""
        self.mapping_action[action_converter.action_type] = action_converter
        self.mapping_uppercase_name[action_converter.first_word()].append(
            action_converter
        )

    def action_type_supported(self, action_type: str) -> bool:
        all_action_names = (
            action_class.__name__ for action_class in self.mapping_action.keys()
        )
        return any(action_type == name for name in all_action_names)

    def actions_to_string(self, actions: List[Action]) -> str:
        action_strings = (self.action_to_string(a) for a in actions)
        return self.separator.join(action_strings) + self.end_mark

    def string_to_actions(
        self,
        action_string: str,
        wrap_errors_into_invalidaction: bool = False,
    ) -> List[Action]:
        # remove last dot (or other end mark)
        if self.end_mark:
            try:
                action_string = remove_postfix(
                    action_string, self.end_mark, raise_if_missing=True
                )
            except ValueError as e:
                logger.warning(str(e))

        if not action_string:
            return []

        action_strings = action_string.split(self.separator)

        actions: List[Action] = []
        for action_string in action_strings:
            try:
                action = self.string_to_action(action_string)
            except StringToActionError as e:
                if not wrap_errors_into_invalidaction:
                    raise
                action = InvalidAction(str(e))
            actions.append(action)
        return actions

    def action_to_string(self, action: Action) -> str:
        try:
            action_converter = self.mapping_action[action.__class__]
        except KeyError as e:
            raise UnsupportedType(action.__class__) from e

        try:
            action_string = action_converter.action_to_text(action)
        except Exception as e:
            raise ActionToStringError(
                f"Conversion to string failed for {action}"
            ) from e

        # replace normal space by no-break space if there is '; ' in the string,
        # as it would lead to an error in the back-conversion
        action_string = action_string.replace(self.separator, self.separator_substitute)

        return action_string

    def string_to_action(self, action_string: str) -> Action:
        """
        Convert a string for a single action into an action.

        Raises:
            StringToActionError: in case of error.
        """
        # replace no-break space (probably introduced in action_to_string) by normal space
        action_string = action_string.replace(self.separator_substitute, self.separator)

        action_type = action_string.split(" ", 1)[0]
        single_action_converters = self.mapping_uppercase_name[action_type]
        if len(single_action_converters) == 0:
            # i.e. could not find converter for action
            raise StringToActionError(
                action_string, f'Can not find converter for "{action_string}".'
            )

        exceptions = []
        for converter in single_action_converters:
            try:
                action: Action = converter.text_to_action(action_string)
                return action
            except Exception as e:
                exceptions.append(e)

        # If hasn't returned by now: all the converters failed
        raise StringToActionError(
            action_string,
            f"Conversion failed for {action_string}: {'; '.join(str(e) for e in exceptions)}",
        )
