import copy
from typing import List

from ..actions import Action, NoAction
from .action_postprocessor import ActionPostprocessor


class NoActionPostprocessor(ActionPostprocessor):
    """
    Postprocessor that removes "NoAction" from a list of actions.
    """

    def postprocess(self, actions: List[Action]) -> List[Action]:
        actions = copy.deepcopy(actions)
        return [a for a in actions if not isinstance(a, NoAction)]
