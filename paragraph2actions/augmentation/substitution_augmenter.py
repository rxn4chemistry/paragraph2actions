import random
from abc import ABC
from typing import List

from .augmenter import Augmenter


class SubstitutionAugmenter(Augmenter, ABC):
    """
    Base class for data augmentation relying on substitution.
    """

    def __init__(self, probability: float, values: List[str]):
        """
        Args:
            probability: probability with which to switch a value when prompted
            values: list of values to use for substitution
        """
        self.probability = probability
        self.values = list(values)

        assert 0 <= self.probability <= 1
        assert len(self.values) > 0

    def random_draw_passes(self) -> bool:
        return random.uniform(0, 1) < self.probability

    def draw_value(self) -> str:
        return random.choice(self.values)
