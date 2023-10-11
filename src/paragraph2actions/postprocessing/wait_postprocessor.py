import copy
from typing import List, Optional

from ..actions import Action, Add, SetTemperature, Stir, Wait
from .action_postprocessor import ActionPostprocessor


class WaitPostprocessor(ActionPostprocessor):
    def __init__(self) -> None:
        self.ineligible_actions = {Add}

    def postprocess(self, actions: List[Action]) -> List[Action]:
        updated_actions: List[Optional[Action]] = list(copy.deepcopy(actions))

        # go through the actions, "consumed" Wait actions are converted to None in order to remove them afterwards
        for i in range(len(updated_actions) - 1):
            a = updated_actions[i]
            b = updated_actions[i + 1]

            # NB: we don't merge if b has a temperature
            if not isinstance(b, Wait) or b.temperature is not None:
                continue

            # convert SetTemperature to Stir
            if isinstance(a, SetTemperature):
                a = Stir(temperature=a.temperature)

            if not self.eligible_first_action(a):
                continue

            setattr(a, "duration", b.duration)
            updated_actions[i] = a
            updated_actions[i + 1] = None

        return [a for a in updated_actions if a is not None]

    def eligible_first_action(self, a: Optional[Action]) -> bool:
        if any(isinstance(a, cls) for cls in self.ineligible_actions):
            return False

        return hasattr(a, "duration") and getattr(a, "duration") is None
