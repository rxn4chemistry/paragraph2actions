import copy
import re
from collections import defaultdict
from typing import Dict, List

from paragraph2actions.misc import TextWithActions

from ..actions import Chemical
from ..utils import extract_chemicals
from .substitution_augmenter import SubstitutionAugmenter


class CompoundNameAugmenter(SubstitutionAugmenter):
    """
    Augments data by substituting compound names.
    """

    def __init__(self, probability: float, compounds: List[str]):
        """
        Args:
            probability: probability with which to switch the compound name
            compounds: list of names to use for substitution
        """
        super().__init__(probability=probability, values=compounds)

    def augment(self, sample: TextWithActions) -> TextWithActions:
        sample = copy.deepcopy(sample)

        chemicals = extract_chemicals(sample.actions)

        # Build a dictionary of compound names and associated chemicals
        # (necessary if the same chemical is present twice)
        cpd_dict: Dict[str, List[Chemical]] = defaultdict(list)
        for c in chemicals:
            cpd_dict[c.name].append(c)

        # remove compound names that are comprised in others; with this, if both '3-ethyltoluene' and
        # '2-bromo-3-ethyltoluene' are present as compounds, we will never substitute the short one.
        for chemical_name in list(cpd_dict.keys()):
            if any(
                chemical_name in cpd for cpd in cpd_dict.keys() if chemical_name != cpd
            ):
                cpd_dict.pop(chemical_name)

        # For each chemical name, try substitution
        for cpd_name in cpd_dict:
            if not self.random_draw_passes() or cpd_name not in sample.text:
                continue
            new_name = self.draw_value()
            sample.text = self.replace_in_text(
                text=sample.text, compound=cpd_name, new_name=new_name
            )
            for c in cpd_dict[cpd_name]:
                c.name = new_name

        return sample

    def replace_in_text(self, text: str, compound: str, new_name: str) -> str:
        # We replace only at word boundaries, to avoid things like 'H2SO4 -> waterSO4' when replacing 'H2' by 'water'
        pattern = re.compile(rf"\b{re.escape(compound)}\b")
        return pattern.sub(new_name, text)
