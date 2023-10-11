import copy
from typing import List, Set

from paragraph2actions.misc import TextWithActions

from .substitution_augmenter import SubstitutionAugmenter


class ActionAttributeAugmenter(SubstitutionAugmenter):
    """
    Augments data by substituting a given attribute of actions (such as durations or values).
    """

    def __init__(self, probability: float, values: List[str], attribute_name: str):
        """
        Args:
            probability: probability with which to switch the compound name
            values: list of values to use for substitution
            attribute_name: name of the variable of Action classes that contains the values to substitue
        """
        super().__init__(probability=probability, values=values)
        self.attribute_name = attribute_name

    def augment(self, sample: TextWithActions) -> TextWithActions:
        sample = copy.deepcopy(sample)

        values: Set[str] = set()
        for a in sample.actions:
            value = getattr(a, self.attribute_name, None)
            if value is not None:
                values.add(value)

        # remove values that are comprised in others; with this, if both '0 °C' and
        # '10 °C' are present as values, we will never substitute the short one.
        for d in list(values):
            if any(d in value for value in values if d != value):
                values.remove(d)

        # For each quantity, try substitution
        for d in values:
            if not self.random_draw_passes() or d not in sample.text:
                continue

            new_value = self.draw_value()
            sample.text = sample.text.replace(d, new_value)

            for a in sample.actions:
                action_value = getattr(a, self.attribute_name, None)
                if action_value == d:
                    setattr(a, self.attribute_name, new_value)

        return sample
