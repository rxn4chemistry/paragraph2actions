from pathlib import Path
from typing import Tuple

import click
from rxn.utilities.files import dump_list_to_file, load_list_from_file

from paragraph2actions.translator import Translator


@click.command()
@click.option(
    "--translation_models",
    "-t",
    multiple=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Translation model file. If multiple are given, will be an ensemble model.",
)
@click.option(
    "--sentencepiece_model",
    "-p",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="SentencePiece model file",
)
@click.option(
    "--src_file",
    "-s",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="File to translate",
)
@click.option(
    "--output_file",
    "-o",
    required=True,
    type=click.Path(writable=True, path_type=Path),
    help="Where to save translation",
)
def main(
    translation_models: Tuple[Path, ...],
    sentencepiece_model: Path,
    src_file: Path,
    output_file: Path,
) -> None:
    """
    Translate a text with an OpenNMT model.

    This script is derived from the one in the OpenNMT-Py repository, and adds pre-processing and post-processing
    in the form of tokenization and de-tokenization with sentencepiece.
    """
    translator = Translator(
        translation_model=[str(m) for m in translation_models],
        sentencepiece_model=str(sentencepiece_model),
    )

    sentences = load_list_from_file(src_file)
    translations = translator.translate_sentences(sentences)
    dump_list_to_file(translations, output_file)


if __name__ == "__main__":
    main()
