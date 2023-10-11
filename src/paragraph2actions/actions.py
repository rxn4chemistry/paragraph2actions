from abc import ABC
from typing import List, Optional

import attr


@attr.s(auto_attribs=True)
class Chemical:
    """
    Substance with attached quantities.

    Quantities are optional, and several may be given simultaneously (f.i. ['1 mmol', '2.0 g', '2.0 mL']'), therefore
    they are saved as a list.
    """

    name: str
    quantity: List[str] = attr.Factory(list)


@attr.s(auto_attribs=True)
class Action(ABC):
    """
    Base class for an action.

    See https://github.ibm.com/rxn/action_sequences/wiki/Data-format-for-synthesis-actions for
    basic details about available actions.
    """

    @property
    def action_name(self) -> str:
        return self.__class__.__name__


@attr.s(auto_attribs=True)
class InvalidAction(Action):
    error: str = ""


@attr.s(auto_attribs=True)
class Add(Action):
    material: Chemical
    dropwise: bool = False
    temperature: Optional[str] = None
    atmosphere: Optional[str] = None
    duration: Optional[str] = None


@attr.s(auto_attribs=True)
class CollectLayer(Action):
    """
    Attributes:
        layer: which layer to keep ("aqueous" or "organic")
    """

    layer: str

    def __attrs_post_init__(self) -> None:
        if self.layer not in ["aqueous", "organic"]:
            raise ValueError('layer must be equal to "aqueous" or "organic"')


@attr.s(auto_attribs=True)
class Concentrate(Action):
    pass


@attr.s(auto_attribs=True)
class Degas(Action):
    gas: Optional[str]
    duration: Optional[str] = None


@attr.s(auto_attribs=True)
class DrySolid(Action):
    """Dry a solid under air or vacuum.

    For drying under vacuum, the atmosphere variable should contain the string 'vacuum'.
    For drying on air, the atmosphere variable should contain the string 'air'.
    For other atmospheres, the corresponding gas name should be given ('N2', 'argon', etc.).
    """

    duration: Optional[str] = None
    temperature: Optional[str] = None
    atmosphere: Optional[str] = None


@attr.s(auto_attribs=True)
class DrySolution(Action):
    """Dry an organic solution with a desiccant"""

    material: Optional[str]


@attr.s(auto_attribs=True)
class Extract(Action):
    solvent: Chemical
    repetitions: int = 1


@attr.s(auto_attribs=True)
class Filter(Action):
    """
    Filtration action, possibly with information about what phase to keep ('filtrate' or 'precipitate')
    """

    phase_to_keep: Optional[str] = None

    def __attrs_post_init__(self) -> None:
        if self.phase_to_keep is not None and self.phase_to_keep not in [
            "filtrate",
            "precipitate",
        ]:
            raise ValueError(
                'phase_to_keep must be equal to "filtrate" or "precipitate"'
            )


@attr.s(auto_attribs=True)
class FollowOtherProcedure(Action):
    """
    Fake action for sentences that refer to another experimental procedure.
    """


@attr.s(auto_attribs=True)
class MakeSolution(Action):
    """
    Action to make a solution out of a list of compounds.
    This action is usually followed by another action using it (Add, Quench, etc.).
    """

    materials: List[Chemical]

    def __attrs_post_init__(self) -> None:
        if len(self.materials) < 2:
            raise ValueError(
                f"MakeSolution requires at least two components (actual: {len(self.materials)}"
            )


@attr.s(auto_attribs=True)
class Microwave(Action):
    duration: Optional[str] = None
    temperature: Optional[str] = None


@attr.s(auto_attribs=True)
class OtherLanguage(Action):
    """
    Fake action for sentences that are not in English.
    """


@attr.s(auto_attribs=True)
class Partition(Action):
    material_1: Chemical
    material_2: Chemical


@attr.s(auto_attribs=True)
class PH(Action):
    material: Chemical
    ph: Optional[str] = None
    dropwise: bool = False
    temperature: Optional[str] = None


@attr.s(auto_attribs=True)
class PhaseSeparation(Action):
    pass


@attr.s(auto_attribs=True)
class Purify(Action):
    pass


@attr.s(auto_attribs=True)
class Quench(Action):
    material: Chemical
    dropwise: bool = False
    temperature: Optional[str] = None


@attr.s(auto_attribs=True)
class Recrystallize(Action):
    solvent: Chemical


@attr.s(auto_attribs=True)
class Reflux(Action):
    duration: Optional[str] = None
    dean_stark: bool = False
    atmosphere: Optional[str] = None


@attr.s(auto_attribs=True)
class SetTemperature(Action):
    """
    If there is a duration given with cooling/heating, use "Stir" instead
    """

    temperature: str


@attr.s(auto_attribs=True)
class Sonicate(Action):
    duration: Optional[str] = None
    temperature: Optional[str] = None


@attr.s(auto_attribs=True)
class Stir(Action):
    duration: Optional[str] = None
    temperature: Optional[str] = None
    atmosphere: Optional[str] = None


@attr.s(auto_attribs=True)
class Triturate(Action):
    solvent: Chemical


@attr.s(auto_attribs=True)
class Wait(Action):
    """
    NB: "Wait" as an action can be ambiguous depending on the context.
    It seldom means "waiting without doing anything", but is often "continue what was before", at least in Pistachio.
    """

    duration: str
    temperature: Optional[str] = None


@attr.s(auto_attribs=True)
class Wash(Action):
    material: Chemical
    repetitions: int = 1


@attr.s(auto_attribs=True)
class Yield(Action):
    material: Chemical


@attr.s(auto_attribs=True)
class NoAction(Action):
    """
    Fake action for sentences that actually have no action.
    """
