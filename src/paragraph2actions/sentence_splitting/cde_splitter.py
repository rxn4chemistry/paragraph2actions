from typing import List

import chemdataextractor

from .sentence_splitter import SentenceSplitter, SentenceSplittingError


class CdeSplitter(SentenceSplitter):
    """
    Splits sentences using the CDE library.
    """

    def __init__(self, split_sentences_at_newlines: bool = True):
        super().__init__(split_sentences_at_newlines=split_sentences_at_newlines)

    def _split_impl(self, text: str) -> List[str]:
        try:
            paragraph = chemdataextractor.doc.Paragraph(text)
            return [sentence.text for sentence in paragraph.sentences]
        except Exception as e:
            raise SentenceSplittingError(text) from e
