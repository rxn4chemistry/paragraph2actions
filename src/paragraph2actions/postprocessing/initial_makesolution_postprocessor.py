import copy
import logging
from typing import List

from ..actions import Action, Add, MakeSolution
from .action_postprocessor import ActionPostprocessor

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class InitialMakesolutionPostprocessor(ActionPostprocessor):
    """
    Replaces MakeSolution actions at the beginning of a sequence by Add actions.
    """

    def postprocess(self, actions: List[Action]) -> List[Action]:
        actions = copy.deepcopy(actions)

        if not self.has_makesolution_at_beginning(actions):
            return actions

        makesolution = actions[0]
        add = actions[1]
        assert isinstance(makesolution, MakeSolution)
        assert isinstance(add, Add)

        atmosphere = add.atmosphere
        temperature = add.temperature
        if add.dropwise:
            logger.warning("Dropwise addition of initial MakeSolution is ignored")
        if add.duration is not None:
            logger.warning("Duration of addition of initial MakeSolution is ignored")

        adds = [
            Add(m, temperature=temperature, atmosphere=atmosphere)
            for m in makesolution.materials
        ]

        # replace "MakeSolution X; Add SLN" by the new Adds
        actions[0:2] = adds

        return actions

    def has_makesolution_at_beginning(self, actions: List[Action]) -> bool:
        if len(actions) < 2:
            return False

        if not isinstance(actions[0], MakeSolution):
            return False

        add = actions[1]
        if not isinstance(add, Add):
            return False

        if add.material.name != "SLN":
            return False

        return True
