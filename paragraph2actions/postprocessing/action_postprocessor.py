from abc import ABC, abstractmethod
from typing import List

from ..actions import Action


class ActionPostprocessor(ABC):
    """
    Interface for postprocessing on a list of actions.

    In this context, postprocessing means any change to the actions (merging, removal, edition, etc.)
    ActionProcessor classes can be applied to both sentences or to full paragraphs.
    """

    @abstractmethod
    def postprocess(self, actions: List[Action]) -> List[Action]:
        """
        Args:
            actions: list of actions to postprocess

        Returns:
            New (postprocessed) list of actions
        """
