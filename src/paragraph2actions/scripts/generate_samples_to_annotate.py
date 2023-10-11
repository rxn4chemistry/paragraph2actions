import random
from pathlib import Path
from typing import Callable, List, Set

import click

from paragraph2actions.actions import (
    PH,
    Filter,
    FollowOtherProcedure,
    InvalidAction,
    NoAction,
    Stir,
)
from paragraph2actions.misc import TextWithActions, load_samples, save_samples
from paragraph2actions.readable_converter import ReadableConverter
from paragraph2actions.utils import extract_chemicals


def is_empty(sample: TextWithActions) -> bool:
    return len(sample.actions) == 0


def is_noaction(sample: TextWithActions) -> bool:
    return len(sample.actions) == 1 and isinstance(sample.actions[0], NoAction)


def includes_invalid_action(sample: TextWithActions) -> bool:
    return any(isinstance(a, InvalidAction) for a in sample.actions)


def contains_followed_by(sample: TextWithActions) -> bool:
    return "followed by" in sample.text


def contains_allowed_to(sample: TextWithActions) -> bool:
    return "allowed to" in sample.text


def contains_permitted_to(sample: TextWithActions) -> bool:
    return "permitted to" in sample.text


def contains_left_to(sample: TextWithActions) -> bool:
    return "left to" in sample.text


def contains_saturated(sample: TextWithActions) -> bool:
    return "saturated" in sample.text


def contains_under(sample: TextWithActions) -> bool:
    return " under " in sample.text and not any(
        w in sample.text for w in ["under vac", "reduced pressure"]
    )


def contains_maintain(sample: TextWithActions) -> bool:
    return "maintain" in sample.text


def contains_ice(sample: TextWithActions) -> bool:
    return " ice" in sample.text


def contains_bath(sample: TextWithActions) -> bool:
    return "bath" in sample.text


def contains_neutralize(sample: TextWithActions) -> bool:
    return "neutraliz" in sample.text


def starts_with_after(sample: TextWithActions) -> bool:
    return sample.text.startswith("After")


def includes_unclear_filtration(sample: TextWithActions) -> bool:
    for a in sample.actions:
        if isinstance(a, Filter):
            if a.phase_to_keep is None:
                return True
    return False


def includes_duplicated_chemicals(sample: TextWithActions) -> bool:
    chemicals = extract_chemicals(sample.actions)
    reprs = [repr(c) for c in chemicals]
    return len(chemicals) != len(set(reprs))


def includes_ph(sample: TextWithActions) -> bool:
    return " pH " in sample.text or any(isinstance(a, PH) for a in sample.actions)


def lonely_stir(sample: TextWithActions) -> bool:
    stir_actions = [a for a in sample.actions if isinstance(a, Stir)]
    lonely_stirs = [
        a for a in stir_actions if a.duration is None and a.temperature is None
    ]
    return len(lonely_stirs) != 0


def maybe_follow_other_procedure(sample: TextWithActions) -> bool:
    # do not include the ones already marked to be following other procedures
    if any(isinstance(a, FollowOtherProcedure) for a in sample.actions):
        return False

    return any(w in sample.text.lower() for w in ["prepared", "synthesi"])


subsets: List[Callable[[TextWithActions], bool]] = [
    is_empty,
    is_noaction,
    includes_invalid_action,
    contains_followed_by,
    contains_allowed_to,
    contains_permitted_to,
    contains_left_to,
    contains_saturated,
    contains_under,
    contains_maintain,
    contains_ice,
    contains_bath,
    contains_neutralize,
    starts_with_after,
    includes_unclear_filtration,
    includes_ph,
    includes_duplicated_chemicals,
    lonely_stir,
    maybe_follow_other_procedure,
]


def select_samples(
    samples: List[TextWithActions], n_per_subset: int = 500, n_from_random: int = 2000
) -> List[TextWithActions]:
    # for each subset, get the corresponding samples
    samples_for_subsets = [
        [sample for sample in samples if predicate(sample)] for predicate in subsets
    ]
    print("Total filtered samples:", sum(len(s) for s in samples_for_subsets))

    # Take a given number of samples from each subset and put them together
    merged_samples = []
    for sample_list in samples_for_subsets:
        merged_samples.extend(sample_list[:n_per_subset])
    print(
        f"Size after keeping max {n_per_subset} for each category: {len(merged_samples)}"
    )

    # extend with random (normal) samples
    merged_samples.extend(samples[:n_from_random])
    print("Size after addition of random samples:", len(merged_samples))

    # Remove duplicates
    seen_sentences: Set[str] = set()
    unique_samples: List[TextWithActions] = []
    for sample in merged_samples:
        if sample.text not in seen_sentences:
            seen_sentences.add(sample.text)
            unique_samples.append(sample)

    # shuffle
    random.shuffle(unique_samples)

    print("Size after removing identical sentences:", len(unique_samples))
    return unique_samples


@click.command()
@click.option(
    "--src_in",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="File containing original sentences",
)
@click.option(
    "--tgt_in",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="File containing original sequences",
)
@click.option(
    "--src_out",
    required=True,
    type=click.Path(writable=True, path_type=Path),
    help="Where to save sentences selected for annotation",
)
@click.option(
    "--tgt_out",
    required=True,
    type=click.Path(writable=True, path_type=Path),
    help="Where to save sequences selected for annotation",
)
def main(src_in: Path, tgt_in: Path, src_out: Path, tgt_out: Path) -> None:
    """Generate samples for annotation"""
    action_string_converter = ReadableConverter()

    # Load the data
    samples = load_samples(
        text_file=src_in, actions_file=tgt_in, converter=action_string_converter
    )

    selected_samples = select_samples(samples)

    save_samples(
        samples=selected_samples,
        converter=action_string_converter,
        text_file=src_out,
        actions_file=tgt_out,
    )


if __name__ == "__main__":
    main()
