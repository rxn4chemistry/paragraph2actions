import copy
from typing import Callable, List, Optional

from ..actions import Action
from ..utils import apply_to_temperatures, extract_temperatures
from .action_postprocessor import ActionPostprocessor


class SameTemperaturePostprocessor(ActionPostprocessor):
    """
    Postprocessor that converts "same temperature" to an actual temperature by
    looking backwards in the text.
    """

    def __init__(self) -> None:
        self.same_temperature_names = {"same temperature"}

    def postprocess(self, actions: List[Action]) -> List[Action]:
        actions = copy.deepcopy(actions)

        # Check if it is necessary at all to change something.
        # If not, return early
        temperatures = set(extract_temperatures(actions))
        if not temperatures.intersection(self.same_temperature_names):
            return actions

        for i, action in enumerate(actions):
            # Get the potential substitue in case "same temperature" is in the current action.
            substitute = self.get_last_temperature(actions[:i])
            if substitute is not None:
                # Create the callback for temperature replacement
                fn = self.create_replace_function(substitute)
                apply_to_temperatures([action], fn)

        return actions

    def get_last_temperature(self, actions: List[Action]) -> Optional[str]:
        """Get the last temperature in a list of actions"""
        temperatures = extract_temperatures(actions)
        valid_temperatures = [
            t for t in temperatures if t not in self.same_temperature_names
        ]
        if not valid_temperatures:
            return None
        return valid_temperatures[-1]

    def create_replace_function(self, substitute: str) -> Callable[[str], str]:
        """
        Creates a callback that can be used to replace a temperature member variable that specifies "same temperature".
        """

        def replace_fn(temperature: str) -> str:
            if temperature in self.same_temperature_names:
                return substitute
            return temperature

        return replace_fn
