import json
import logging
from typing import Iterable, List

import attr
from rxn.utilities.files import PathLike

from .actions import Action
from .converter_interface import ActionStringConverter

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@attr.s(auto_attribs=True)
class TextWithActions:
    """
    Sentence (or paragraph) and its corresponding actions.
    """

    text: str
    actions: List[Action]


def load_samples(
    text_file: PathLike, actions_file: PathLike, converter: ActionStringConverter
) -> List[TextWithActions]:
    """
    Loads samples of sentences with corresponding actions from files.
    Sentences and actions are loaded from different files, which corresponds to the format of OpenNMT.

    Args:
        text_file: where to load the original text from
        actions_file: where to load the actions from
        converter: how to convert from the string representation to the actions
    """

    with open(text_file, "rt") as f_sents, open(actions_file, "rt") as f_actns:
        sentences = [line.strip() for line in f_sents]
        actions_lists = [converter.string_to_actions(line.strip()) for line in f_actns]

    assert len(sentences) == len(actions_lists)
    return [
        TextWithActions(sentence, actions)
        for sentence, actions in zip(sentences, actions_lists)
    ]


def save_samples(
    samples: Iterable[TextWithActions],
    converter: ActionStringConverter,
    text_file: PathLike,
    actions_file: PathLike,
) -> None:
    """
    Saves samples of sentences with corresponding actions to files.
    Sentences and actions are saved to different files, which corresponds to the input required by OpenNMT.

    Args:
        samples: samples to save to the file
        converter: how to convert the actions to a string representation
        text_file: where to save the original text
        actions_file: where to save the actions
    """

    with open(text_file, "wt") as f_src, open(actions_file, "wt") as f_tgt:
        for s in samples:
            f_src.write(f"{s.text}\n")
            f_tgt.write(f"{converter.actions_to_string(s.actions)}\n")


def load_samples_from_json(
    annotated_file: PathLike, converter: ActionStringConverter
) -> List[TextWithActions]:
    """
    Loads samples of sentences with corresponding actions from the JSON file.

    Args:
        annotated_file: where to load the text and actions from.
        converter: how to convert from the string representation to the actions.
    """

    samples = []
    with open(annotated_file, "rt") as f:
        for line in f:
            d = json.loads(line)
            approved = d.get("approved", True)
            if not approved:
                continue

            try:
                actions = converter.string_to_actions(d["actions"])
            except Exception as e:
                logger.error(f"Error converting action \"{d['actions']}\": {e}")
                continue

            samples.append(
                TextWithActions(
                    text=d["sentence"],
                    actions=actions,
                )
            )

    return samples
