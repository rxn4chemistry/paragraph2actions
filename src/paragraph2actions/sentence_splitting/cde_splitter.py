import logging
from typing import List

import chemdataextractor
from chemdataextractor.data import Package

from .sentence_splitter import SentenceSplitter, SentenceSplittingError

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class CdeSplitter(SentenceSplitter):
    """
    Splits sentences using the CDE library.
    """

    def __init__(self, split_sentences_at_newlines: bool = True):
        super().__init__(split_sentences_at_newlines=split_sentences_at_newlines)
        download_cde_data()

    def _split_impl(self, text: str) -> List[str]:
        try:
            paragraph = chemdataextractor.doc.Paragraph(text)
            return [sentence.text for sentence in paragraph.sentences]
        except Exception as e:
            raise SentenceSplittingError(text) from e


def download_cde_data() -> None:
    """Explicitly download the CDE model necessary for splitting sentences, if needed."""
    package = Package("models/punkt_chem-1.0.pickle")
    if package.local_exists():
        return

    logger.info("Downloading the necessary ChemDataExtractor data...")
    package.download()
    logger.info("Downloading the necessary ChemDataExtractor data... Done.")
