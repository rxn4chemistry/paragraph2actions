from typing import Iterator, List, Optional, Sequence

import textdistance
from nltk.translate.bleu_score import corpus_bleu

from .conversion_utils import ActionStringConversionError
from .converter_interface import ActionStringConverter
from .readable_converter import ReadableConverter
from .utils import all_identical


def highlight_differences(
    source_sentences: List[str], translations: Sequence[List[str]]
) -> None:
    """
    Will highlight sentences that are translated differently by different models.

    Args:
        source_sentences: Sentences to translate (length: L)
        translations: Multiple lists of translations, depending on the number of translation models (size: n_models x L)
    """
    assert all(len(t) == len(source_sentences) for t in translations)

    for i, sentence in enumerate(source_sentences):
        sentence_translations = [t[i] for t in translations]

        if not all_identical(sentence_translations):
            print(f"Sample {i}: {sentence}")
            for model_no, s in enumerate(sentence_translations, 1):
                print(f"{model_no}) {s}")
            print()


def full_sentence_accuracy(truth: List[str], pred: List[str]) -> float:
    """
    Calculate the number of exact matches.
    """
    assert len(truth) == len(pred)

    correct_count = sum(int(t == p) for t, p in zip(truth, pred))
    return correct_count / len(truth)


def action_string_validity(
    preds: List[str], converter: Optional[ActionStringConverter] = None
) -> float:
    """
    Calculate the fraction of sentences that correspond to valid action strings.

    Returns:
        value between 0 (no string is valid) and 1.
    """

    if converter is None:
        converter = ReadableConverter()

    n_valid = 0
    for p in preds:
        try:
            converter.string_to_actions(p)
            n_valid += 1
        except ActionStringConversionError:
            pass

    return n_valid / len(preds)


def modified_bleu(truth: List[str], pred: List[str]) -> float:
    """
    Calculates the BLEU score of a translation, with a small modification in order not to penalize sentences
    with less than 4 words.

    Returns:
        value between 0 and 1.
    """
    references = [sentence.split() for sentence in truth]
    candidates = [sentence.split() for sentence in pred]

    # BLEU penalizes sentences with only one word. Even correct translations get a score of zero.
    references = [r + max(0, 4 - len(r)) * [""] for r in references]
    candidates = [c + max(0, 4 - len(c)) * [""] for c in candidates]

    # references must have a larger depth because it supports multiple choices
    refs = [[r] for r in references]
    return corpus_bleu(refs, candidates)  # type: ignore[no-any-return]


def original_bleu(truth: List[str], pred: List[str]) -> float:
    """
    Calculates the BLEU score of a translation, with the original function from nltk.

    Returns:
        value between 0 and 1.
    """
    references = [sentence.split() for sentence in truth]
    candidates = [sentence.split() for sentence in pred]

    # references must have a larger depth because it supports multiple choices
    refs = [[r] for r in references]
    return corpus_bleu(refs, candidates)  # type: ignore[no-any-return]


def levenshtein_similarity(truth: List[str], pred: List[str]) -> float:
    assert len(truth) == len(pred)
    scores: Iterator[float] = (
        textdistance.levenshtein.normalized_similarity(t, p)
        for t, p in zip(truth, pred)
    )
    return sum(scores) / len(truth)


def partial_accuracy(truth: List[str], pred: List[str], threshold: float) -> float:
    """
    Calculates the accuracy from the fraction of sentences that have a similarity to the
    ground truth higher than a given threshold.

    For threshold == 1.0, this function is equivalent to full_sentence_accuracy.

    Args:
        truth: ground truth action sequences
        pred: predicted truth action sequences
        threshold: threshold above which to consider it as a partial match, between 0 and 1
    """
    assert len(truth) == len(pred)
    match_count = sum(
        1
        for t, p in zip(truth, pred)
        if textdistance.levenshtein.normalized_similarity(t, p) >= threshold
    )
    return match_count / len(truth)
