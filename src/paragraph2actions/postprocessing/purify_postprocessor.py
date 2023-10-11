import copy
from typing import List

from ..actions import Action, Purify
from .action_postprocessor import ActionPostprocessor


class RemovePurifyPostprocessor(ActionPostprocessor):
    """
    Postprocessor that removes "Purify" from a list of actions.
    """

    def postprocess(self, actions: List[Action]) -> List[Action]:
        actions = copy.deepcopy(actions)
        return [a for a in actions if not isinstance(a, Purify)]
