from typing import Tuple

import click

from paragraph2actions.analysis import full_sentence_accuracy, action_string_validity, modified_bleu, \
    levenshtein_similarity, partial_accuracy


@click.command()
@click.option('--ground_truth_file', '-g', required=True, help='File containing the ground truth')
@click.option('--prediction_files', '-p', multiple=True, help='File containing the translations to compare with the'
                                                              'ground truth')
def calculate_metrics(ground_truth_file: str, prediction_files: Tuple[str, ...]) -> None:
    """Calculate metrics for predictions generated by one or several translation models"""

    with open(ground_truth_file, 'rt') as f:
        ground_truth = [s.strip() for s in f]

    predictions = []
    for prediction_file in prediction_files:
        with open(prediction_file, 'rt') as f:
            p = [s.strip() for s in f]
            predictions.append(p)

    for filename, p in zip(prediction_files, predictions):
        print(filename)
        print('Full sentence accuracy, pr:', full_sentence_accuracy(ground_truth, p))
        print('String validity, pr:', action_string_validity(p))
        print('BLEU, pr:', modified_bleu(ground_truth, p))
        print('Levenshtein, pr:', levenshtein_similarity(ground_truth, p))
        print('100% accuracy, pr:', partial_accuracy(ground_truth, p, 1.0))
        print('90% accuracy, pr:', partial_accuracy(ground_truth, p, 0.9))
        print('75% accuracy, pr:', partial_accuracy(ground_truth, p, 0.75))
        print()


if __name__ == '__main__':
    calculate_metrics()
