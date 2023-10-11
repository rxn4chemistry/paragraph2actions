import copy
from typing import List

from ..actions import Action, Microwave, Reflux, Stir
from .action_postprocessor import ActionPostprocessor


class DuplicateActionsPostprocessor(ActionPostprocessor):
    """
    Postprocessor that removes repeated actions, if they are not
    type of Stir, Reflux or Microwave.
    """

    def postprocess(self, actions: List[Action]) -> List[Action]:
        actions = copy.deepcopy(actions)

        last_action = None
        new_actions = []

        for i, action in enumerate(actions):
            if action != last_action or type(action) in [Stir, Reflux, Microwave]:
                new_actions.append(action)
            last_action = action

        return new_actions
