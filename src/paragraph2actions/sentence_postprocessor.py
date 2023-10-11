from typing import List, Optional

from .actions import Action, InvalidAction, NoAction
from .utils import Sentence


class SentencePostprocessor:
    """
    Given sentences with corresponding actions, will post-process them:
    * "NoAction" for empty sentences? which ones?
    * Keep invalid actions?
    * Remove unknown actions?
    """

    def __init__(
        self,
        consider_straightforward_empty_sentences_as_noaction: bool = True,
        remove_sentences_with_invalid_actions: bool = True,
        remove_empty_sentences: bool = True,
    ):
        """
        Args:
            consider_straightforward_empty_sentences_as_noaction: For simple sentences with no action, add "NoAction" and keep them
            remove_sentences_with_invalid_actions: remove sentences where the conversion failed
            remove_empty_sentences: whether to keep empty sentences (NB: NoAction is not considered to be empty)
        """

        self.consider_straightforward_empty_sentences_as_noaction = (
            consider_straightforward_empty_sentences_as_noaction
        )
        self.remove_sentences_with_invalid_actions = (
            remove_sentences_with_invalid_actions
        )
        self.remove_empty_sentences = remove_empty_sentences

        self.no_action_keywords = [
            "MS",
            "found:",
            "Found:",
            "ppm",
            "ESI",
            "NMR",
            "m/z",
            "retention",
            "Retention",
            "HPLC",
            "TLC",
            "M+H",
            "M+1",
            "mp:",
            "Mp:",
        ]
        self.no_action_length = 30

    def process(self, sentence: Sentence) -> Optional[Sentence]:
        """
        Post-processes a sentence

        Returns:
            The post-processed sentence, or None if it should not be included in the dataset
        """

        def replace_actions(actions: List[Action]) -> Sentence:
            return Sentence(text=sentence.text, actions=actions)

        if self.remove_sentences_with_invalid_actions:
            if any(isinstance(action, InvalidAction) for action in sentence.actions):
                return None

        if self.consider_straightforward_empty_sentences_as_noaction:
            if len(sentence.actions) == 0 and self.empty_sentence_is_straightforward(
                sentence.text
            ):
                return replace_actions([NoAction()])

        if self.remove_empty_sentences and len(sentence.actions) == 0:
            return None

        # If we got here, no post-processing is needed and we return the same actions
        return replace_actions(sentence.actions)

    def empty_sentence_is_straightforward(self, sentence_text: str) -> bool:
        """
        Returns True if we are reasonably certain that no actions are included
        """
        # TODO: there's likely an error below: should it be ``in sentence_text.split(" ")``?
        has_analysis_keyword = any(w in sentence_text for w in self.no_action_keywords)
        short_sentence = len(sentence_text) < self.no_action_length

        return has_analysis_keyword or short_sentence
