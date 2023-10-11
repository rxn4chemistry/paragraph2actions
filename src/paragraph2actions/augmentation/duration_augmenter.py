from typing import List

from .action_attribute_augmenter import ActionAttributeAugmenter


class DurationAugmenter(ActionAttributeAugmenter):
    """
    Augments data by substituting action durations.
    """

    def __init__(self, probability: float, durations: List[str]):
        """
        Args:
            probability: probability with which to switch the compound name
            durations: list of durations to use for substitution
        """
        super().__init__(
            probability=probability, values=durations, attribute_name="duration"
        )
