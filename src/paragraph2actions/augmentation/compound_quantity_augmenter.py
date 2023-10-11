import copy
from typing import List

from paragraph2actions.misc import TextWithActions

from ..utils import extract_chemicals
from .substitution_augmenter import SubstitutionAugmenter


class CompoundQuantityAugmenter(SubstitutionAugmenter):
    """
    Augments data by substituting compound quantities.

    Adding or removing quantities is not considered, since this is more complex to change in the text.
    """

    def __init__(self, probability: float, quantities: List[str]):
        """
        Args:
            probability: probability with which to switch the compound name
            quantities: list of quantities to use for substitution
        """
        super().__init__(probability=probability, values=quantities)

    def augment(self, sample: TextWithActions) -> TextWithActions:
        sample = copy.deepcopy(sample)

        chemicals = extract_chemicals(sample.actions)

        quantity_blocks = [c.quantity for c in chemicals]
        all_quantities = [
            q for quantity_block in quantity_blocks for q in quantity_block
        ]

        unique_quantities = set(all_quantities)

        # remove quantities that are comprised in others; with this, if both '1.0 g' and
        # '21.0 g' are present as quantities, we will never substitute the short one.
        for q in list(unique_quantities):
            if any(q in quantity for quantity in unique_quantities if q != quantity):
                unique_quantities.remove(q)

        # For each quantity, try substitution
        for q in unique_quantities:
            if not self.random_draw_passes() or q not in sample.text:
                continue

            new_quantity = self.draw_value()
            sample.text = sample.text.replace(q, new_quantity)

            for quantity_block in quantity_blocks:
                for i in range(len(quantity_block)):
                    if q == quantity_block[i]:
                        quantity_block[i] = new_quantity

        return sample
