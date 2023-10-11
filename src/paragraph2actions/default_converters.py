import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

import attr
from rxn.utilities.strings import remove_postfix, remove_prefix

from .actions import (
    PH,
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
from .conversion_utils import (
    ActionType,
    SingleActionConverter,
    chemical_to_string,
    chemicals_to_text,
    get_chemical,
    get_property_from_split,
    text_to_chemicals,
    uppercase_action_name,
    uppercase_type_name,
)
from .introspection import get_variable_type


def action_without_parameters(
    action_type: Type[ActionType],
) -> SingleActionConverter[ActionType]:
    """Create an action converter for an action type that does not have any
    parameters.

    This will lead to a conversion relying on the uppercase action name.

    Args:
        action_type: action type to create the converter for.
    """

    def action_to_text(action: ActionType) -> str:
        return uppercase_action_name(action)

    def text_to_action(action_string: str) -> ActionType:
        uppercase_name = uppercase_type_name(action_type)
        if action_string != uppercase_name:
            raise ValueError(
                f'Expected "{uppercase_name}", but the action string is "{action_string}".'
            )
        return action_type()

    return SingleActionConverter(action_type, action_to_text, text_to_action)


@attr.s(auto_attribs=True)
class Parameters:
    """
    Utility class for the automatic generation of an action converter with
    parameters.

    Instances of this class specify the name of the action attribute together
    with a separator / prefix. For more complex transformations, functions
    to and from text can be given.

    Attributes:
        attribute: name of the attribute associated with the action class.
        separator: separator word used in the string conversion, such as "at", "with", etc.
        to_text: can be given if the conversion does not simply rely on a
            separator / prefix. Callback to convert the attribute value to
            the segment of string related to that attribute.
        from_text: can be given if the conversion does not simply rely on a
            separator / prefix. Callback to convert the remaining action string
            to what remains after the attribute extraction and the extracted value.
    """

    attribute: str
    separator: Optional[str]
    to_text: Optional[Callable[[Any], str]] = None
    from_text: Optional[Callable[[str], Tuple[str, Any]]] = None

    @property
    def prefix(self) -> str:
        """
        Helper function to give whatever needs to be added before the actual
        value in the string, independently of whether there is a separator or not.
        """
        if self.separator is None:
            return ""
        return f" {self.separator}"


def action_with_parameters(
    action_type: Type[ActionType],
    parameters_raw: List[Union[Parameters, Tuple[Any, ...]]],
    compound_parameter: Optional[Parameters] = None,
) -> SingleActionConverter[ActionType]:
    """Create an action converter for an action type by automating the generation
    of the text linked to its associated properties.

    This will lead to a conversion relying on the uppercase action name, followed
    by a few portions for each of the parameters.
    This is illustrated very well in the uses of this function for the default
    converters.

    Args:
        action_type: action type to create the converter for.
        parameters_raw: List of parameters to specifying how to convert the
            properties associated with an action to and from text. If provided
            as tuples (for ease of use), will be converted directly to
            Parameters instances.
        compound_parameter: Parameter for a Chemical instance. Will always be
            the first one given in the string after the action name. Given as a
            separate parameter because it is usually feasible to parse it only
            if one knows exactly what comes before in the string (i.e.: action
            name).
    """
    parameters = [
        p if isinstance(p, Parameters) else Parameters(*p) for p in parameters_raw
    ]
    uppercase_name = uppercase_type_name(action_type)

    def action_to_text(action: ActionType) -> str:
        s = uppercase_name

        if compound_parameter is not None:
            value = getattr(action, compound_parameter.attribute)
            if value is not None:
                s += f"{compound_parameter.prefix} {chemical_to_string(value)}"

        for parameter in parameters:
            value_type = get_variable_type(action_type, parameter.attribute)
            value = getattr(action, parameter.attribute)
            if parameter.to_text is not None:
                s += parameter.to_text(value)
            elif value_type is str:
                s += f"{parameter.prefix} {value}"
            elif value_type is Optional[str]:
                if value is not None:
                    s += f"{parameter.prefix} {value}"
            elif value_type is bool:
                if value is True:
                    s += f"{parameter.prefix}"
            elif value_type is Chemical or value_type is Optional[Chemical]:
                if value is not None:
                    s += f"{parameter.prefix} {chemical_to_string(value)}"
            else:
                raise ValueError(f"Cannot convert type {value_type.__name__}")
        return s

    def text_to_action(action_text: str) -> ActionType:
        remaining = action_text
        properties: Dict[str, Any] = {}
        for parameter in reversed(parameters):
            value_type = get_variable_type(action_type, parameter.attribute)
            if parameter.from_text is not None:
                remaining, value = parameter.from_text(remaining)
            elif value_type is bool:
                value = remaining.endswith(parameter.prefix)
                remaining = remove_postfix(remaining, parameter.prefix)
            elif value_type is str:
                remaining, value = get_property_from_split(remaining, parameter.prefix)
                if value is None:
                    raise ValueError("Expected a string, but received None instead.")
            elif value_type is Chemical or value_type is Optional[Chemical]:
                # Note: the prefix already has an empty space as a prefix
                splits = remaining.split(f"{parameter.prefix} ")
                if len(splits) == 1:
                    value = None
                elif len(splits) > 2:
                    raise ValueError(
                        f"Found more than one occurence of {parameter.prefix}"
                    )
                else:
                    remaining, compound_text = splits
                    value = get_chemical(compound_text)
            else:
                remaining, value = get_property_from_split(remaining, parameter.prefix)
            properties[parameter.attribute] = value

        if compound_parameter is not None:
            value_type = get_variable_type(action_type, compound_parameter.attribute)
            if value_type is Optional[Chemical] and remaining == uppercase_name:
                pass
            else:
                # Remove action name and prefix to get the compound text
                compound_text = remove_prefix(
                    remaining,
                    f"{uppercase_name}{compound_parameter.prefix} ",
                    raise_if_missing=True,
                )
                value = get_chemical(compound_text)
                properties[compound_parameter.attribute] = value
                # Remaining afterwards: only the uppercase action name
                remaining = uppercase_name

        if remaining != uppercase_name:
            raise ValueError(
                f'Only "{uppercase_name}" should remain. Actual: "{remaining}".'
            )

        return action_type(**properties)

    return SingleActionConverter(action_type, action_to_text, text_to_action)


def repetition_to_text(repetitions: int) -> str:
    """Convert a number of repetitions to its string representation, to be used
    as the to_text variable of the Parameters class."""
    if repetitions == 1:
        return ""
    return f" {repetitions} x"


def repetition_from_text(remaining_text: str) -> Tuple[str, int]:
    """Extract the number of repetitions from an action string, to be used
    as the from_text variable of the Parameters class."""
    match = re.findall(r"( (\d+) x)$", remaining_text)
    if not match:
        return remaining_text, 1

    # NB: there will be only one match, as the regex contains '$'
    all_matched, digit_matched = match[0]
    remaining = remove_postfix(remaining_text, all_matched, raise_if_missing=True)
    return remaining, int(digit_matched)


def makesolution_to_text(action: MakeSolution) -> str:
    """To be used in the creation of the ActionConverter for MakeSolution."""
    return (
        uppercase_action_name(action) + " with " + chemicals_to_text(action.materials)
    )


def makesolution_from_text(action_text: str) -> MakeSolution:
    """To be used in the creation of the ActionConverter for MakeSolution."""
    chemicals_text = action_text.replace("MAKESOLUTION with ", "")
    compounds = text_to_chemicals(chemicals_text)
    return MakeSolution(materials=compounds)


def partition_to_text(action: Partition) -> str:
    """To be used in the creation of the ActionConverter for Partition."""
    return (
        uppercase_action_name(action)
        + " with "
        + chemicals_to_text([action.material_1, action.material_2])
    )


def partition_from_text(action_text: str) -> Partition:
    """To be used in the creation of the ActionConverter for Partition."""
    chemicals_text = action_text.replace("PARTITION with ", "")
    compounds = text_to_chemicals(chemicals_text)
    if len(compounds) != 2:
        raise ValueError(
            f"Found {len(compounds)} compounds associated with Partition action. Must be 2."
        )
    return Partition(material_1=compounds[0], material_2=compounds[1])


add = action_with_parameters(
    Add,
    [
        ("dropwise", "dropwise"),
        ("temperature", "at"),
        ("atmosphere", "under"),
        ("duration", "over"),
    ],
    Parameters("material", None),
)
collect_layer = action_with_parameters(CollectLayer, [("layer", None)])
concentrate = action_without_parameters(Concentrate)
degas = action_with_parameters(
    Degas,
    [
        ("gas", "with"),
        ("duration", "for"),
    ],
)
dry_solid = action_with_parameters(
    DrySolid,
    [
        ("duration", "for"),
        ("temperature", "at"),
        ("atmosphere", "under"),
    ],
)
dry_solution = action_with_parameters(DrySolution, [("material", "over")])
extract = action_with_parameters(
    Extract,
    [("repetitions", None, repetition_to_text, repetition_from_text)],
    Parameters("solvent", "with"),
)
filter_ = action_with_parameters(Filter, [("phase_to_keep", "keep")])
follow_other_procedure = action_without_parameters(FollowOtherProcedure)
invalid_action = action_with_parameters(
    InvalidAction,
    [
        ("error", None),
    ],
)
makesolution = SingleActionConverter(
    MakeSolution, makesolution_to_text, makesolution_from_text
)
microwave = action_with_parameters(
    Microwave,
    [
        ("duration", "for"),
        ("temperature", "at"),
    ],
)
no_action = action_without_parameters(NoAction)
other_language = action_without_parameters(OtherLanguage)
partition = SingleActionConverter(Partition, partition_to_text, partition_from_text)
ph = action_with_parameters(
    PH,
    [("ph", "to pH"), ("dropwise", "dropwise"), ("temperature", "at")],
    Parameters("material", "with"),
)
phase_separation = action_without_parameters(PhaseSeparation)
purify = action_without_parameters(Purify)
quench = action_with_parameters(
    Quench,
    [("dropwise", "dropwise"), ("temperature", "at")],
    Parameters("material", "with"),
)
recrystallize = action_with_parameters(Recrystallize, [], Parameters("solvent", "from"))
reflux = action_with_parameters(
    Reflux,
    [
        ("duration", "for"),
        ("atmosphere", "under"),
        ("dean_stark", "with Dean-Stark apparatus"),
    ],
)
set_temperature = action_with_parameters(SetTemperature, [("temperature", None)])
sonicate = action_with_parameters(
    Sonicate,
    [
        ("duration", "for"),
        ("temperature", "at"),
    ],
)
stir = action_with_parameters(
    Stir,
    [
        ("duration", "for"),
        ("temperature", "at"),
        ("atmosphere", "under"),
    ],
)
triturate = action_with_parameters(Triturate, [], Parameters("solvent", "with"))
wait = action_with_parameters(
    Wait,
    [
        ("duration", "for"),
        ("temperature", "at"),
    ],
)
wash = action_with_parameters(
    Wash,
    [("repetitions", None, repetition_to_text, repetition_from_text)],
    Parameters("material", "with"),
)
yield_ = action_with_parameters(Yield, [], Parameters("material", None))


def default_action_converters() -> List[SingleActionConverter]:  # type: ignore[type-arg]
    """
    Get the default single-action converters for RXN.
    """
    action_converters: List[SingleActionConverter] = [  # type: ignore[type-arg]
        add,
        collect_layer,
        concentrate,
        degas,
        dry_solid,
        dry_solution,
        extract,
        filter_,
        follow_other_procedure,
        invalid_action,
        makesolution,
        microwave,
        no_action,
        other_language,
        partition,
        ph,
        phase_separation,
        purify,
        quench,
        recrystallize,
        reflux,
        set_temperature,
        sonicate,
        stir,
        triturate,
        wait,
        wash,
        yield_,
    ]
    return action_converters
