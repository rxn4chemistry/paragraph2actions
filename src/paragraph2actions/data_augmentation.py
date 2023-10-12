import logging
import random
from itertools import cycle, islice
from pathlib import Path
from typing import Iterable, List

from rxn.utilities.containers import remove_duplicates
from rxn.utilities.files import load_list_from_file

from .augmentation.compound_name_augmenter import CompoundNameAugmenter
from .augmentation.compound_quantity_augmenter import CompoundQuantityAugmenter
from .augmentation.duration_augmenter import DurationAugmenter
from .augmentation.temperature_augmenter import TemperatureAugmenter
from .conversion_utils import SingleActionConverter
from .misc import TextWithActions, load_samples, save_samples
from .readable_converter import ReadableConverter

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def augment_annotations(
    data_dir: Path,
    value_lists_dir: Path,
    output_dir: Path,
    single_action_converters: Iterable[SingleActionConverter],  # type: ignore[type-arg]
    n_augmentations: int,
) -> None:
    readable_converter = ReadableConverter(
        single_action_converters=single_action_converters
    )

    train_items = load_samples(
        text_file=str(data_dir / "src-train.txt"),
        actions_file=str(data_dir / "tgt-train.txt"),
        converter=readable_converter,
    )

    logger.info("Samples in train set:", len(train_items))

    # data augmentation for train split
    compound_names = load_list_from_file(str(value_lists_dir / "compound_names.txt"))
    quantities = load_list_from_file(str(value_lists_dir / "quantities.txt"))
    durations = load_list_from_file(str(value_lists_dir / "durations.txt"))
    temperatures = load_list_from_file(str(value_lists_dir / "temperatures.txt"))

    cna = CompoundNameAugmenter(0.5, compound_names)
    cqa = CompoundQuantityAugmenter(0.5, quantities)
    da = DurationAugmenter(0.5, durations)
    ta = TemperatureAugmenter(0.5, temperatures)

    def augment(sample: TextWithActions) -> TextWithActions:
        sample = cna.augment(sample)
        sample = cqa.augment(sample)
        sample = da.augment(sample)
        sample = ta.augment(sample)
        return sample

    augmented_samples = [
        augment(sample)
        for sample in islice(cycle(train_items), n_augmentations * len(train_items))
    ]

    random.shuffle(augmented_samples)
    logger.info("Samples in augmented train set:", len(augmented_samples))

    augmented_samples_unique = remove_duplicates(
        augmented_samples, key=lambda x: x.text
    )
    logger.info(
        "Samples in augmented train set after removing duplicates:",
        len(augmented_samples_unique),
    )

    def save_to_file(sample_list: List[TextWithActions], subset_name: str) -> None:
        src_file = f"{output_dir}/src-{subset_name}.txt"
        tgt_file = f"{output_dir}/tgt-{subset_name}.txt"

        logger.info(f"Saving {len(sample_list)} samples to {src_file} and {tgt_file}")
        save_samples(
            samples=sample_list,
            converter=readable_converter,
            text_file=src_file,
            actions_file=tgt_file,
        )

    output_dir.mkdir(exist_ok=True)
    save_to_file(augmented_samples_unique, "train-augmented-unique")
    save_to_file(augmented_samples, "train-augmented")
