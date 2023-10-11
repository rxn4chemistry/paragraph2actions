from typing import Iterable, List, Union

from .internal_translation_utils import RawTranslator, Translation, get_onmt_opt
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

        if isinstance(translation_model, str):
            translation_model = [translation_model]
        self.translation_model = list(translation_model)

        self.onmt_translator = RawTranslator(self.translation_model)

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
        self, sentences: List[str], n_best=1
    ) -> List[List[Translation]]:
        onmt_opt = get_onmt_opt(translation_model=self.translation_model, n_best=n_best)
        tokenized_sentences = [self.sp.tokenize(s) for s in sentences]

        translations = self.onmt_translator.translate_sentences_with_onmt(
            onmt_opt, tokenized_sentences
        )

        for translation_group in translations:
            for t in translation_group:
                t.text = self.sp.detokenize(t.text)

        return translations
