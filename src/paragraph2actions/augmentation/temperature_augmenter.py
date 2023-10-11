from typing import List

from .action_attribute_augmenter import ActionAttributeAugmenter


class TemperatureAugmenter(ActionAttributeAugmenter):
    """
    Augments data by substituting action temperatures.
    """

    def __init__(self, probability: float, temperatures: List[str]):
        """
        Args:
            probability: probability with which to switch the compound name
            temperatures: list of temperatures to use for substitution
        """
        super().__init__(
            probability=probability, values=temperatures, attribute_name="temperature"
        )
