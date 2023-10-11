import copy
from typing import List, Type

from ..actions import Action, Concentrate, DrySolid, DrySolution, Filter
from ..utils import pairwise
from .action_postprocessor import ActionPostprocessor


class FilterPostprocessor(ActionPostprocessor):
    """
    Sets what to keep (filtrate vs precipitate) in a Filter action based on the following action.
    """

    def __init__(self) -> None:
        self.pre_filtrate_classes: List[Type[Action]] = [DrySolution]
        self.post_filtrate_classes: List[Type[Action]] = [Concentrate, DrySolution]
        self.pre_precipitate_classes: List[Type[Action]] = []
        self.post_precipitate_classes: List[Type[Action]] = [DrySolid]

    def postprocess(self, actions: List[Action]) -> List[Action]:
        actions = copy.deepcopy(actions)

        for a, b in pairwise(actions):
            self.update_based_on_following_action(filter_action=a, following_action=b)
            self.update_based_on_previous_action(filter_action=b, previous_action=a)

        return actions

    def update_based_on_previous_action(
        self, filter_action: Action, previous_action: Action
    ) -> None:
        self.update_based_on_other_action(
            filter_action,
            previous_action,
            self.pre_filtrate_classes,
            self.pre_precipitate_classes,
        )

    def update_based_on_following_action(
        self, filter_action: Action, following_action: Action
    ) -> None:
        self.update_based_on_other_action(
            filter_action,
            following_action,
            self.post_filtrate_classes,
            self.post_precipitate_classes,
        )

    def update_based_on_other_action(
        self,
        filter_action: Action,
        other_action: Action,
        filtrate_related_classes: List[Type[Action]],
        precipitate_related_classes: List[Type[Action]],
    ) -> None:
        if (
            not isinstance(filter_action, Filter)
            or filter_action.phase_to_keep is not None
        ):
            return

        if any(isinstance(other_action, cls) for cls in filtrate_related_classes):
            filter_action.phase_to_keep = "filtrate"

        if any(isinstance(other_action, cls) for cls in precipitate_related_classes):
            filter_action.phase_to_keep = "precipitate"
