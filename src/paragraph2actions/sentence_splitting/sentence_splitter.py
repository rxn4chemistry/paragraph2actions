from abc import ABC, abstractmethod
from typing import List


class SentenceSplittingError(ValueError):
    def __init__(self, text_to_split: str):
        super().__init__(
            f"Error when splitting the following text in sentences: {text_to_split}"
        )


class SentenceSplitter(ABC):
    def __init__(
        self,
        split_sentences_at_newlines: bool = True,
        add_full_stop_if_missing: bool = True,
    ):
        """
        Args:
            split_sentences_at_newlines: whether to consider newlines as sentence separators.
            add_full_stop_if_missing: if the paragraph(s) do not have a full stop at the end,
                add it.
        """
        self.split_sentences_at_newlines = split_sentences_at_newlines
        self.add_full_stop_if_missing = add_full_stop_if_missing

    def split(self, text: str) -> List[str]:
        """
        Splits a text into sentences.

        As an example, this is required for the translation model paragraphs->actions:
        the paragraph must be split in sentences before translation.
        """

        # If the text contains newlines: split there already
        if self.split_sentences_at_newlines:
            pre_split_paragraphs = text.splitlines()
        else:
            pre_split_paragraphs = [text]

        sentences = []
        for paragraph in pre_split_paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            if self.add_full_stop_if_missing and not paragraph.endswith("."):
                paragraph += "."
            sentences.extend(self._split_impl(paragraph))

        return sentences

    @abstractmethod
    def _split_impl(self, text: str) -> List[str]:
        """
        Internal, implementation-specific splitting of sentences.

        Applied after any processing in the base class.
        """
