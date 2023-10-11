from pathlib import Path
from typing import Tuple

import click
import sentencepiece as spm


@click.command()
@click.option(
    "--inputs",
    "-i",
    multiple=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Input file(s) on which to train sentencepiece",
)
@click.option(
    "--model",
    "-m",
    required=True,
    type=click.Path(writable=True, path_type=Path),
    help="Where to save the sentencepiece model",
)
@click.option("--vocab_size", "-v", default=16000, type=int, help="Vocabulary size")
def main(inputs: Tuple[Path, ...], model: Path, vocab_size: int) -> None:
    """Learn sentencepiece model"""
    input_files = ",".join(str(p) for p in inputs)
    spm.SentencePieceTrainer.Train(
        f"--input={input_files} --model_prefix={model} "
        f"--vocab_size={vocab_size} --character_coverage=1.0 "
        f"--normalization_rule_name=identity"
    )


if __name__ == "__main__":
    main()
