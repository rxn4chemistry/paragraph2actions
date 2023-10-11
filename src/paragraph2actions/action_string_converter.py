import re
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from .actions import (
    PH,
    Action,
    Add,
    Chemical,
    CollectLayer,
    Concentrate,
    Degas,
    DrySolid,
    DrySolution,
    Extract,
    Filter,
    FollowOtherProcedure,
    InvalidAction,
    MakeSolution,
    Microwave,
    NoAction,
    OtherLanguage,
    Partition,
    PhaseSeparation,
    Purify,
    Quench,
    Recrystallize,
    Reflux,
    SetTemperature,
    Sonicate,
    Stir,
    Triturate,
    Wait,
    Wash,
    Yield,
)
from .utils import get_all_action_types


class ActionStringConversionError(ValueError):
    def __init__(self, action_string: str):
        super().__init__(
            f'Conversion from string to actions failed for "{action_string}".'
        )


class ActionStringConverter(ABC):
    """
    Base class for the conversion of our custom action classes to and from strings.
    """

    def __init__(self):
        for action_name in get_all_action_types():
            assert self.action_type_supported(
                action_name
            ), f'Action "{action_name}" is not supported by the converter'

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
    def string_to_actions(self, action_string: str) -> List[Action]:
        """
        Converts a string representation to the corresponding list of actions.
        """


class ReprConverter(ActionStringConverter):
    """
    Action-String converter based on the `repr` form of the action instances.
    """

    def action_type_supported(self, action_type: str) -> bool:
        return action_type in get_all_action_types()

    def actions_to_string(self, actions: List[Action]) -> str:
        return repr(actions)

    def string_to_actions(self, action_string: str) -> List[Action]:
        try:
            return eval(action_string)
        except Exception as e:
            raise ActionStringConversionError(action_string) from e


class ReadableConverter(ActionStringConverter):
    """
    Action-String converter based on the format used initially for the translation task:

    For instance:
    > FILTERFILTRATE; EXTRACT with chloroform (quantity unspecified).
    """

    def __init__(self, separator: str = "; ", end_mark: str = "."):
        """
        Args:
            separator: string that will be inserted between the action strings.
            end_mark: string that will be added at the end of the action string.
        """
        super().__init__()

        self.separator = separator
        self.end_mark = end_mark

        assert len(self.separator) > 1
        # If a compound name / duration contains the separator, the string
        # will be modified by adding a no-break space between the first and
        # second character.
        self.separator_substitute = self.separator[:1] + "\u200C" + self.separator[1:]

    def action_type_supported(self, action_type: str) -> bool:
        from_method_exists = self._get_from_method(action_type) is not None
        to_method_exists = self._get_to_method(action_type) is not None
        return from_method_exists and to_method_exists

    def actions_to_string(self, actions: List[Action]) -> str:
        action_strings = (self.action_to_string(a) for a in actions)
        return self.separator.join(action_strings) + self.end_mark

    def string_to_actions(self, action_string: str) -> List[Action]:
        try:
            if self.end_mark:
                # remove last dot (or other end mark)
                action_string = action_string[: -len(self.end_mark)]
            if not action_string:
                return []
            action_strings = action_string.split(self.separator)
            return [
                self.string_to_action(action_string) for action_string in action_strings
            ]
        except Exception as e:
            raise ActionStringConversionError(action_string) from e

    def action_to_string(self, action: Action) -> str:
        action_string = self._get_from_method(action.action_name)(action)

        # replace normal space by no-break space if there is '; ' in the string,
        # as it would lead to an error in the back-conversion
        action_string = action_string.replace(self.separator, self.separator_substitute)

        return action_string

    def string_to_action(self, action_string: str) -> Action:
        # replace no-break space (probably introduced in action_to_string) by normal space
        action_string = action_string.replace(self.separator_substitute, self.separator)

        action_type = action_string.split(" ", 1)[0]
        return self._get_to_method(action_type)(action_string)

    def _uppercase_action_name(self, action: Action) -> str:
        return action.action_name.upper()

    def _chemical_to_string(self, c: Chemical) -> str:
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

    def _get_from_method(self, action_type: str):
        method_name = "_from_" + action_type.lower()
        method = getattr(self, method_name, None)
        if method is None:
            raise ValueError(
                f'Cannot find method to convert "{action_type}" action to string'
            )
        return method

    def _get_to_method(self, action_type: str):
        method_name = "_to_" + action_type.lower()
        method = getattr(self, method_name, None)
        if method is None:
            raise ValueError(
                f'Cannot find method to convert "{action_type}" action string to an actual action'
            )
        return method

    def _from_add(self, action: Add) -> str:
        s = f"{self._uppercase_action_name(action)} {self._chemical_to_string(action.material)}"
        if action.dropwise:
            s += " dropwise"
        if action.temperature:
            s += f" at {action.temperature}"
        if action.atmosphere:
            s += f" under {action.atmosphere}"
        if action.duration:
            s += f" over {action.duration}"
        return s

    def _to_add(self, action_text: str) -> Action:
        remaining, duration = self._get_property_from_split(action_text, "over")
        remaining, atmosphere = self._get_property_from_split(remaining, "under")
        remaining, temperature = self._get_property_from_split(remaining, "at")
        dropwise = " dropwise" in remaining
        remaining = remaining.replace(" dropwise", "")
        chemical = self._get_chemical(remaining, "ADD ")
        return Add(
            material=chemical,
            dropwise=dropwise,
            temperature=temperature,
            atmosphere=atmosphere,
            duration=duration,
        )

    def _from_invalidaction(self, action: InvalidAction) -> str:
        s = f"{self._uppercase_action_name(action)}"
        if action.error:
            s += f" {action.error}"
        return s

    def _to_invalidaction(self, action_text: str) -> Action:
        m = re.match("INVALIDACTION (.*)", action_text)
        if m is None:
            # if there is no match, it means that there was no error message
            return InvalidAction()
        return InvalidAction(error=m.group(1))

    def _from_collectlayer(self, action: CollectLayer) -> str:
        return f"{self._uppercase_action_name(action)} {action.layer}"

    def _to_collectlayer(self, action_text: str) -> Action:
        layer = self._re_match(r"COLLECTLAYER (.*)", action_text)
        return CollectLayer(layer=layer)

    def _from_concentrate(self, action: Concentrate) -> str:
        return self._uppercase_action_name(action)

    def _to_concentrate(self, action_text: str) -> Action:
        return Concentrate()

    def _from_degas(self, action: Degas) -> str:
        return f"{self._uppercase_action_name(action)} with {action.gas} for {action.duration}"

    def _to_degas(self, action_text: str) -> Action:
        remaining, duration = self._get_property_from_split(action_text, "for")
        material = self._re_match(r"DEGAS with (.*)", remaining)
        return Degas(gas=material, duration=duration)

    def _from_drysolid(self, action: DrySolid) -> str:
        s = f"{self._uppercase_action_name(action)}"
        if action.duration:
            s += f" for {action.duration}"
        if action.temperature:
            s += f" at {action.temperature}"
        if action.atmosphere:
            s += f" under {action.atmosphere}"
        return s

    def _to_drysolid(self, action_text: str) -> Action:
        remaining, atmosphere = self._get_property_from_split(action_text, "under")
        remaining, temperature = self._get_property_from_split(remaining, "at")
        remaining, duration = self._get_property_from_split(remaining, "for")
        return DrySolid(
            duration=duration, temperature=temperature, atmosphere=atmosphere
        )

    def _from_drysolution(self, action: DrySolution) -> str:
        s = self._uppercase_action_name(action)
        if action.material:
            s += f" over {action.material}"
        return s

    def _to_drysolution(self, action_text: str) -> Action:
        remaining, material = self._get_property_from_split(action_text, "over")
        return DrySolution(material=material)

    def _from_extract(self, action: Extract) -> str:
        s = f"{self._uppercase_action_name(action)} with {self._chemical_to_string(action.solvent)}"
        if action.repetitions != 1:
            s += f" {action.repetitions} x"
        return s

    def _to_extract(self, action_text: str) -> Action:
        repetitions = 1
        match = re.findall(r"( (\d+) x)$", action_text)
        if match:
            assert len(match) == 1
            assert len(match[0]) == 2
            repetitions = int(match[0][1])
            action_text = action_text.replace(match[0][0], "")
        material = self._get_chemical(action_text, "EXTRACT with ")
        return Extract(solvent=material, repetitions=repetitions)

    def _from_filter(self, action: Filter) -> str:
        s = self._uppercase_action_name(action)
        if action.phase_to_keep is not None:
            s += f" keep {action.phase_to_keep}"
        return s

    def _to_filter(self, action_text: str) -> Action:
        _, phase = self._get_property_from_split(action_text, "keep")
        return Filter(phase)

    def _from_followotherprocedure(self, action: Concentrate) -> str:
        return self._uppercase_action_name(action)

    def _to_followotherprocedure(self, action_text: str) -> Action:
        return FollowOtherProcedure()

    def _from_makesolution(self, action: MakeSolution) -> str:
        materials_strings = [self._chemical_to_string(c) for c in action.materials]
        combined_materials = " and ".join(materials_strings)
        return f"{self._uppercase_action_name(action)} with {combined_materials}"

    def _to_makesolution(self, action_text: str) -> Action:
        action_text = action_text.replace("MAKESOLUTION with ", "")
        compounds_strings = action_text.split(" and ")
        compounds = [
            self._get_chemical(compound_string) for compound_string in compounds_strings
        ]
        return MakeSolution(materials=compounds)

    def _from_microwave(self, action: Sonicate) -> str:
        s = f"{self._uppercase_action_name(action)}"
        if action.duration:
            s += f" for {action.duration}"
        if action.temperature:
            s += f" at {action.temperature}"
        return s

    def _to_microwave(self, action_text: str) -> Action:
        remaining, temperature = self._get_property_from_split(action_text, "at")
        remaining, duration = self._get_property_from_split(remaining, "for")
        return Microwave(duration=duration, temperature=temperature)

    def _from_otherlanguage(self, action: OtherLanguage) -> str:
        return self._uppercase_action_name(action)

    def _to_otherlanguage(self, action_text: str) -> Action:
        return OtherLanguage()

    def _from_partition(self, action: Partition) -> str:
        return (
            f"{self._uppercase_action_name(action)} "
            f"with {self._chemical_to_string(action.material_1)} "
            f"and {self._chemical_to_string(action.material_2)}"
        )

    def _to_partition(self, action_text: str) -> Action:
        action_text = action_text.replace("PARTITION with ", "")
        splits = action_text.split(" and ")
        m1 = self._get_chemical(splits[0])
        m2 = self._get_chemical(splits[1])
        return Partition(material_1=m1, material_2=m2)

    def _from_ph(self, action: PH) -> str:
        s = (
            f"{self._uppercase_action_name(action)} "
            f"with {self._chemical_to_string(action.material)}"
        )
        if action.ph:
            s += f" to pH {action.ph}"
        if action.dropwise:
            s += " dropwise"
        if action.temperature:
            s += f" at {action.temperature}"
        return s

    def _to_ph(self, action_text: str) -> Action:
        remaining, temperature = self._get_property_from_split(action_text, "at")
        dropwise = " dropwise" in remaining
        remaining = remaining.replace(" dropwise", "")
        splits = remaining.split(" to pH ")
        ph = splits[1] if len(splits) > 1 else None
        material = self._get_chemical(splits[0], "PH with ")
        return PH(material=material, ph=ph, dropwise=dropwise, temperature=temperature)

    def _from_phaseseparation(self, action: PhaseSeparation) -> str:
        return self._uppercase_action_name(action)

    def _to_phaseseparation(self, action_text: str) -> Action:
        return PhaseSeparation()

    def _from_purify(self, action: Purify) -> str:
        return self._uppercase_action_name(action)

    def _to_purify(self, action_text: str) -> Action:
        return Purify()

    def _from_quench(self, action: Quench) -> str:
        s = (
            f"{self._uppercase_action_name(action)} "
            f"with {self._chemical_to_string(action.material)}"
        )
        if action.dropwise:
            s += " dropwise"
        if action.temperature:
            s += f" at {action.temperature}"
        return s

    def _to_quench(self, action_text: str) -> Action:
        remaining, temperature = self._get_property_from_split(action_text, "at")
        dropwise = " dropwise" in remaining
        remaining = remaining.replace(" dropwise", "")
        material = self._get_chemical(remaining, "QUENCH with ")
        return Quench(material=material, dropwise=dropwise, temperature=temperature)

    def _from_recrystallize(self, action: Recrystallize) -> str:
        return (
            f"{self._uppercase_action_name(action)} "
            f"from {self._chemical_to_string(action.solvent)}"
        )

    def _to_recrystallize(self, action_text: str) -> Action:
        chemical = self._get_chemical(action_text, "RECRYSTALLIZE from ")
        return Recrystallize(solvent=chemical)

    def _from_reflux(self, action: Reflux) -> str:
        s = self._uppercase_action_name(action)
        if action.duration is not None:
            s += f" for {action.duration}"
        if action.atmosphere is not None:
            s += f" under {action.atmosphere}"
        if action.dean_stark:
            s += f" with Dean-Stark apparatus"
        return s

    def _to_reflux(self, action_text: str) -> Action:
        dean_stark = " with Dean-Stark apparatus" in action_text
        remaining = action_text.replace(" with Dean-Stark apparatus", "")
        remaining, atmosphere = self._get_property_from_split(remaining, "under")
        remaining, duration = self._get_property_from_split(remaining, "for")
        return Reflux(duration=duration, dean_stark=dean_stark, atmosphere=atmosphere)

    def _from_settemperature(self, action: SetTemperature) -> str:
        return f"{self._uppercase_action_name(action)} {action.temperature}"

    def _to_settemperature(self, action_text: str) -> Action:
        temperature = self._re_match(r"SETTEMPERATURE (.*)", action_text)
        return SetTemperature(temperature=temperature)

    def _from_sonicate(self, action: Sonicate) -> str:
        s = f"{self._uppercase_action_name(action)}"
        if action.duration:
            s += f" for {action.duration}"
        if action.temperature:
            s += f" at {action.temperature}"
        return s

    def _to_sonicate(self, action_text: str) -> Action:
        remaining, temperature = self._get_property_from_split(action_text, "at")
        remaining, duration = self._get_property_from_split(remaining, "for")
        return Sonicate(duration=duration, temperature=temperature)

    def _from_stir(self, action: Stir) -> str:
        s = self._uppercase_action_name(action)
        if action.duration:
            s += f" for {action.duration}"
        if action.temperature:
            s += f" at {action.temperature}"
        if action.atmosphere:
            s += f" under {action.atmosphere}"
        return s

    def _to_stir(self, action_text: str) -> Action:
        remaining, atmosphere = self._get_property_from_split(action_text, "under")
        remaining, temperature = self._get_property_from_split(remaining, "at")
        remaining, duration = self._get_property_from_split(remaining, "for")
        return Stir(duration=duration, temperature=temperature, atmosphere=atmosphere)

    def _from_triturate(self, action: Triturate) -> str:
        s = f"{self._uppercase_action_name(action)} with {self._chemical_to_string(action.solvent)}"
        return s

    def _to_triturate(self, action_text: str) -> Action:
        material = self._get_chemical(action_text, "TRITURATE with ")
        return Triturate(solvent=material)

    def _from_wait(self, action: Wait) -> str:
        s = f"{self._uppercase_action_name(action)} for {action.duration}"
        if action.temperature:
            s += f" at {action.temperature}"
        return s

    def _to_wait(self, action_text: str) -> Action:
        remaining, temperature = self._get_property_from_split(action_text, "at")
        remaining, duration = self._get_property_from_split(remaining, "for")
        if duration is None:
            raise ValueError("The duration must be set for Wait actions")
        return Wait(duration=duration, temperature=temperature)

    def _from_wash(self, action: Wash) -> str:
        s = (
            f"{self._uppercase_action_name(action)} "
            f"with {self._chemical_to_string(action.material)}"
        )
        if action.repetitions != 1:
            s += f" {action.repetitions} x"
        return s

    def _to_wash(self, action_text: str) -> Action:
        repetitions = 1
        match = re.findall(r"( (\d+) x)$", action_text)
        if match:
            assert len(match) == 1
            assert len(match[0]) == 2
            repetitions = int(match[0][1])
            action_text = action_text.replace(match[0][0], "")
        material = self._get_chemical(action_text, "WASH with ")
        return Wash(material=material, repetitions=repetitions)

    def _from_yield(self, action: Yield) -> str:
        return f"{self._uppercase_action_name(action)} {self._chemical_to_string(action.material)}"

    def _to_yield(self, action_text: str) -> Action:
        material = self._get_chemical(action_text, "YIELD ")
        return Yield(material=material)

    def _from_noaction(self, action: NoAction) -> str:
        return self._uppercase_action_name(action)

    def _to_noaction(self, action_text: str) -> Action:
        return NoAction()

    def _get_property_from_split(
        self, sentence: str, splitting_word: str
    ) -> Tuple[str, Optional[str]]:
        """
        Gets an optional property following a given splitting word.
        Returns:
            Tuple: (sentence before splitting word, optional property)
        """
        splits = sentence.split(f" {splitting_word} ")
        prop = splits[1] if len(splits) > 1 else None
        return splits[0], prop

    def _get_quantities(self, sentence: str) -> Tuple[str, List[str]]:
        match = re.match(r"^.*( \(.*\))$", sentence)
        if not match:
            return sentence, []
        full_match_string = match.group(1)
        # remove parentheses
        match_string = full_match_string[2:-1]
        quantities = match_string.split(", ")
        remaining = sentence.replace(full_match_string, "")
        return remaining, quantities

    def _get_chemical(self, sentence: str, prefix: str = "") -> Chemical:
        """
        Convert a string to a chemical.

        Input examples:
            4-butyloctane (5 ml)
            DMF

        If prefix is given, it will remove it from the original sentence
        (useful for the action names in the beginning of the string).
        """
        if prefix:
            sentence = sentence.replace(prefix, "")
        remaining, quantities = self._get_quantities(sentence)

        # replace the insecable space before the parenthesis back to a normal space
        compound_name = remaining.replace(" \u200C(", " (")

        return Chemical(name=compound_name, quantity=quantities)

    def _re_match(self, regex: str, text: str) -> str:
        p = re.compile(regex)
        m = p.match(text)
        if m is None:
            raise RuntimeError(f'No match for regex "{regex}" in "{text}"')
        return m.group(1)
