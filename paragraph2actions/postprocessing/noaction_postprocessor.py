import copy
from typing import List

from .action_postprocessor import ActionPostprocessor
from ..actions import Action, NoAction


class NoActionPostprocessor(ActionPostprocessor):
    """
    Postprocessor that removes "NoAction" from a list of actions.
    """

    def postprocess(self, actions: List[Action]) -> List[Action]:
        actions = copy.deepcopy(actions)
        return [a for a in actions if not isinstance(a, NoAction)]
