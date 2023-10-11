from typing import Tuple

import click

from paragraph2actions.translator import Translator


@click.command()
@click.option(
    "--translation_models",
    "-t",
    multiple=True,
    help="Translation model file. If multiple are given, will " "be an ensemble model.",
)
@click.option(
    "--sentencepiece_model", "-p", required=True, help="SentencePiece model file"
)
@click.option("--src_file", "-s", required=True, help="File to translate")
@click.option("--output_file", "-o", required=True, help="Where to save translation")
def translate_actions(
    translation_models: Tuple[str, ...],
    sentencepiece_model: str,
    src_file: str,
    output_file: str,
):
    """
    Translate a text with an OpenNMT model.

    This script is derived from the one in the OpenNMT-Py repository, and adds pre-processing and post-processing
    in the form of tokenization and de-tokenization with sentencepiece.
    """
    translator = Translator(
        translation_model=translation_models, sentencepiece_model=sentencepiece_model
    )

    with open(src_file, "rt") as f:
        sentences = [line.strip() for line in f]

    translations = translator.translate_sentences(sentences)

    with open(output_file, "wt") as f:
        for t in translations:
            f.write(f"{t}\n")


if __name__ == "__main__":
    translate_actions()
