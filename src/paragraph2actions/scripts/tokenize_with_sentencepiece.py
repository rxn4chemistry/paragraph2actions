import click

from paragraph2actions.sentencepiece_tokenizer import SentencePieceTokenizer


@click.command()
@click.option("--model", "-m", required=True, help="SentencePiece model path")
@click.option("--input_filename", "-i", required=True, help="File to (de)tokenize")
@click.option(
    "--output_filename", "-o", required=True, help="Where to save (de)tokenized text"
)
@click.option("--reverse", "-r", is_flag=True, help="If given, will do detokenization")
def main(model: str, input_filename: str, output_filename: str, reverse: bool) -> None:
    """Tokenize / detokenize with sentencepiece"""

    sp = SentencePieceTokenizer(model)

    with open(input_filename, "rt", encoding="utf-8") as f_in, open(
        output_filename, "wt", encoding="utf-8"
    ) as f_out:
        for line in f_in:
            line = line.strip()
            if reverse:
                detokenized = sp.detokenize(line)
                f_out.write(f"{detokenized}\n")
            else:
                tokenized = sp.tokenize(line)
                f_out.write(f"{tokenized}\n")


if __name__ == "__main__":
    main()
