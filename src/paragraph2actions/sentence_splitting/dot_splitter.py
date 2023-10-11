import re
from typing import List

from .sentence_splitter import SentenceSplitter


class DotSplitter(SentenceSplitter):
    """
    Splits sentences where there are dots followed by spaces.
    """

    def __init__(self) -> None:
        super().__init__(
            split_sentences_at_newlines=True, add_full_stop_if_missing=True
        )

    def _split_impl(self, text: str) -> List[str]:
        # replace multiple spaces / tabs by one single space
        text = re.sub(r"\s+", " ", text)

        # split at ". "
        sentences = text.split(". ")

        # Add the dots back
        sentences = [self._maybe_add_full_stop(s) for s in sentences]

        return sentences

    def _maybe_add_full_stop(self, sentence: str) -> str:
        if sentence.endswith("."):
            return sentence
        return sentence + "."
