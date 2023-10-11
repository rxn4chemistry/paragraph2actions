from typing import Iterable, Iterator, List, Union

from rxn.onmt_utils.internal_translation_utils import TranslationResult
from rxn.onmt_utils.translator import Translator as RawTranslator

from .sentencepiece_tokenizer import SentencePieceTokenizer


class Translator:
    """
    Wraps the OpenNMT translation functionality into a class.
    """

    def __init__(
        self, translation_model: Union[str, Iterable[str]], sentencepiece_model: str
    ):
        """
        Args:
            translation_model: path to the translation model file(s). If multiple are given, will be an ensemble model.
            sentencepiece_model: path to the sentencepiece model file
        """
        self.sp = SentencePieceTokenizer(sentencepiece_model)
        self.onmt_translator = RawTranslator.from_model_path(translation_model)

    def translate_single(self, sentence: str) -> str:
        """
        Translate one single sentence.
        """
        translations = self.translate_sentences([sentence])
        assert len(translations) == 1
        return translations[0]

    def translate_sentences(self, sentences: List[str]) -> List[str]:
        """
        Translate multiple sentences.
        """
        translations = self.translate_multiple_with_scores(sentences)
        return [t[0].text for t in translations]

    def translate_multiple_with_scores(
        self, sentences: List[str], n_best: int = 1
    ) -> Iterator[List[TranslationResult]]:
        tokenized_sentences = [self.sp.tokenize(s) for s in sentences]

        translations = self.onmt_translator.translate_multiple_with_scores(
            tokenized_sentences, n_best
        )

        for translation_group in translations:
            for t in translation_group:
                t.text = self.sp.detokenize(t.text)
            yield translation_group
