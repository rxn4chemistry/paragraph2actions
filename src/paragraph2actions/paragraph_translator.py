import logging
from typing import Iterable, List, Optional, Union

import attr

from .actions import Action
from .converter_interface import ActionStringConverter
from .readable_converter import ReadableConverter
from .sentence_splitting.dot_splitter import DotSplitter
from .sentence_splitting.sentence_splitter import (
    SentenceSplitter,
    SentenceSplittingError,
)
from .translator import Translator

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@attr.s(auto_attribs=True)
class Sentence:
    """
    Sentence from a synthesis recipe with the corresponding actions.
    """

    text: str
    actions: List[Action]


@attr.s(auto_attribs=True)
class Paragraph:
    """
    Recipe paragraph and the corresponding actions (available through the contained sentences).
    """

    text: str
    sentences: List[Sentence]

    @property
    def actions(self) -> List[Action]:
        return [action for sentence in self.sentences for action in sentence.actions]

    @property
    def sentence_texts(self) -> List[str]:
        return [s.text for s in self.sentences]


class ParagraphTranslator:
    """
    Translates paragraphs into series of actions.
    """

    def __init__(
        self,
        translation_model: Union[str, Iterable[str]],
        sentencepiece_model: str,
        sentence_splitter: Optional[SentenceSplitter] = None,
        action_string_converter: Optional[ActionStringConverter] = None,
        wrap_errors_into_invalidaction: bool = True,
    ):
        """
        Translates a paragraph and returns the action representation.

        Args:
            translation_model: path(s) to translation model(s)
            sentencepiece_model: path to SentencePiece model
            sentence_splitter: splits the sentences, defaults to ``DotSplitter``.
            action_string_converter: converter to get the actual actions,
                defaults to the ReadableConverter
        """

        self.translator = Translator(
            translation_model=translation_model, sentencepiece_model=sentencepiece_model
        )
        self.converter = (
            action_string_converter
            if action_string_converter is not None
            else ReadableConverter()
        )

        self.sentence_splitter = (
            sentence_splitter if sentence_splitter is not None else DotSplitter()
        )
        # splitter to use when the sentence_splitter fails
        self.fallback_splitter = DotSplitter()

        self.wrap_errors_into_invalidaction = wrap_errors_into_invalidaction

    def extract_paragraph(self, text: str) -> Paragraph:
        """
        Translates a paragraph and returns the action representation.
        """
        sentences = self.split_sentences(text)
        action_strings = self.translator.translate_sentences(sentences)

        actions_per_sentence = [
            self.converter.string_to_actions(
                action_string,
                wrap_errors_into_invalidaction=self.wrap_errors_into_invalidaction,
            )
            for action_string in action_strings
        ]

        paragraph = Paragraph(
            text=text,
            sentences=[
                Sentence(text=s, actions=a)
                for s, a in zip(sentences, actions_per_sentence)
            ],
        )
        return paragraph

    def extract_actions(self, text: str) -> List[Action]:
        """
        Translates a paragraph and returns the action representation.
        """
        p = self.extract_paragraph(text)
        return p.actions

    def split_sentences(self, text: str) -> List[str]:
        try:
            return self.sentence_splitter.split(text)
        except SentenceSplittingError:
            logger.warning(
                "Error during splitting of paragraph in sentences; using fallback splitter."
            )
            return self.fallback_splitter.split(text)
