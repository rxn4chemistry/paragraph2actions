from typing import List

from ..actions import Action
from .action_postprocessor import ActionPostprocessor


class PostprocessorCombiner(ActionPostprocessor):
    """
    Combines multiple other postprocessors
    """

    def __init__(self, postprocessors: List[ActionPostprocessor]):
        self.postprocessors = postprocessors

    def postprocess(self, actions: List[Action]) -> List[Action]:
        for p in self.postprocessors:
            actions = p.postprocess(actions)
        return actions
