from abc import ABC, abstractmethod

from paragraph2actions.misc import TextWithActions


class Augmenter(ABC):
    """
    Interface for data augmentation for the action translation dataset.
    """

    @abstractmethod
    def augment(self, sample: TextWithActions) -> TextWithActions:
        """
        Generates a new sample that has potentially been data-augmented.
        """
