from typing import Tuple

import click
import sentencepiece as spm


@click.command()
@click.option('--inputs', '-i', multiple=True, help='Input file(s) on which to train sentencepiece')
@click.option('--model', '-m', required=True, help='Where to save the sentencepiece model')
@click.option('--vocab_size', '-v', default=16000, type=int, help='Vocabulary size')
def save_tokenizer(inputs: Tuple[str, ...], model: str, vocab_size: int) -> None:
    """Learn sentencepiece model"""
    input_files = ','.join(inputs)
    spm.SentencePieceTrainer.Train(f'--input={input_files} --model_prefix={model} '
                                   f'--vocab_size={vocab_size} --character_coverage=1.0 '
                                   f'--normalization_rule_name=identity')


if __name__ == '__main__':
    save_tokenizer()
