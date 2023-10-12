import logging
import random
from pathlib import Path
from typing import Iterable, List

from .actions import InvalidAction
from .conversion_utils import SingleActionConverter
from .misc import TextWithActions, load_samples, load_samples_from_json, save_samples
from .readable_converter import ReadableConverter
from .repr_converter import ReprConverter

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def invalid_filter(sample: TextWithActions) -> TextWithActions:
    """Replace sequences containing (potentially among others) an InvalidAction
    by a sequence with a single InvalidAction without error message."""
    if any(isinstance(a, InvalidAction) for a in sample.actions):
        return TextWithActions(text=sample.text, actions=[InvalidAction()])
    else:
        return sample


def create_annotation_splits(
    annotated_data_dir: Path,
    output_dir: Path,
    single_action_converters: Iterable[SingleActionConverter],  # type: ignore[type-arg]
    valid_fraction: float,
    test_fraction: float,
) -> None:
    repr_converter = ReprConverter()
    readable_converter = ReadableConverter(
        single_action_converters=single_action_converters
    )

    json_file = annotated_data_dir / "annotated.json"
    sents_file = annotated_data_dir / "sentences.txt"
    actns_file = annotated_data_dir / "actions.txt"

    if json_file.exists():
        items = load_samples_from_json(
            annotated_file=json_file,
            converter=readable_converter,
        )
    else:
        items = load_samples(
            text_file=sents_file,
            actions_file=actns_file,
            converter=repr_converter,
        )

    logger.info("Annotation count:", len(items))

    items = [invalid_filter(item) for item in items]

    # remove empty
    items = [item for item in items if len(item.actions) > 0]
    logger.info("Without empty:", len(items))

    # Shuffle
    random.shuffle(items)

    # Training splits
    n_valid_samples = int(valid_fraction * len(items))
    n_test_samples = int(test_fraction * len(items))
    test_items = items[:n_test_samples]
    valid_items = items[n_test_samples : n_test_samples + n_valid_samples]
    train_items = items[n_test_samples + n_valid_samples :]

    logger.info("Samples in train set:", len(train_items))
    logger.info("Samples in valid set:", len(valid_items))
    logger.info("Samples in test set:", len(test_items))

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
    save_to_file(train_items, "train")
    save_to_file(valid_items, "valid")
    save_to_file(test_items, "test")
