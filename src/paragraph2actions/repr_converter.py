from typing import List

from .actions import (  # noqa
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
from .conversion_utils import StringToActionError
from .converter_interface import ActionStringConverter
from .utils import get_all_action_types


class ReprConverter(ActionStringConverter):
    """
    Action-String converter based on the `repr` form of the action instances.

    Not really used anywhere.
    """

    def action_type_supported(self, action_type: str) -> bool:
        return action_type in get_all_action_types()

    def actions_to_string(self, actions: List[Action]) -> str:
        return repr(actions)

    def string_to_actions(
        self,
        action_string: str,
        wrap_errors_into_invalidaction: bool = False,
    ) -> List[Action]:
        try:
            return eval(action_string)  # type: ignore[no-any-return]
        except Exception as e:
            if wrap_errors_into_invalidaction:
                return [InvalidAction(str(e))]
            raise StringToActionError(action_string) from e
