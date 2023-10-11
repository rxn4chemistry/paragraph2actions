from typing import List

from ..actions import Action, DrySolution, Filter
from .action_postprocessor import ActionPostprocessor


class DrysolutionPostprocessor(ActionPostprocessor):
    """
    Ensures that a DrySolution action is followed by a Filter action.

    Often in paragraphs the filtering step is not mentioned. The data was
    analyzed to check if sometimes it comes just a few steps later. Most of
    these cases, however, relate to another filtering step. For instance, it is
    common to dry the solution with desiccant, then concentrate, and then filter
    again, this time to keep the precipitate.
    The safest is therefore probably to always ensure that there is a Filter
    action after DrySolution.
    """

    def postprocess(self, actions: List[Action]) -> List[Action]:
        postprocessed: List[Action] = []

        for i, action in enumerate(actions):
            postprocessed.append(action)

            # If the current action is not a DrySolution: go to the next one
            if not isinstance(action, DrySolution):
                continue

            # If the next action is not Filter: add it.
            next_action = actions[i + 1] if i < len(actions) - 1 else None
            if not isinstance(next_action, Filter):
                postprocessed.append(Filter("filtrate"))

        return postprocessed
