import sentencepiece as spm


class SentencePieceTokenizer:
    """
    Wrapper for the SentencePiece tokenizer
    """

    def __init__(self, model_file: str):
        self.sp = spm.SentencePieceProcessor()
        self.sp.Load(model_file)

    def tokenize(self, sentence: str) -> str:
        tokens = self.sp.EncodeAsPieces(sentence)
        tokenized = " ".join(tokens)
        return tokenized

    def detokenize(self, sentence: str) -> str:
        tokens = sentence.split(" ")
        detokenized: str = self.sp.DecodePieces(tokens)
        return detokenized
