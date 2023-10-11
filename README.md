# Extraction of actions from experimental procedures

This repository contains the code for [Automated Extraction of Chemical Synthesis Actions from Experimental Procedures](https://doi.org/10.1038/s41467-020-17266-6).

- [Overview](#overview)
- [System Requirements](#system-requirements)
- [Installation Guide](#installation-guide)
- [Training the transformer model for action extraction](#training-the-transformer-model-for-action-extraction)
- [Data augmentation example](#data-augmentation)
- [Action post-processing example](#action-post-processing)

# Overview

This repository contains code to extract actions from experimental procedures. In particular, it contains the following:
* Definition and handling of synthesis actions
* Code for data augmentation
* Training and usage of a transformer-based model

A trained model can be freely used online at https://rxn.res.ibm.com or with the Python wrapper available [here](https://github.com/rxn4chemistry/rxn4chemistry).

Links:
* [GitHub repository](https://github.com/rxn4chemistry/paragraph2actions)
* [PyPI package](https://pypi.org/project/paragraph2actions/)

# System Requirements

## Hardware requirements
The code can run on any standard computer.
It is recommended to run the training scripts in a GPU-enabled environment.

## Software requirements
### OS Requirements
This package is supported for *macOS* and *Linux*. The package has been tested on the following systems:
+ macOS: Catalina (10.15.4)
+ Linux: Ubuntu 16.04.3

### Python
A Python version of 3.6 or greater is recommended.
The Python package dependencies are listed in [`setup.cfg`](./setup.cfg).

# Installation guide

To use the package, we recommended to create a dedicated `conda` or `venv` environment:
```bash
# Conda
conda create -n p2a python=3.8
conda activate p2a

# venv
python3.8 -m venv myenv
source myenv/bin/activate
```

The package can then be installed from Pypi:
```bash
pip install paragraph2actions
```

For local development, the package can be installed with:
```bash
pip install -e .[dev]
```
The installation should not take more than a few minutes.

# Training the transformer model for action extraction

This section explains how to train the translation model for action extraction.

## General setup

For simplicity, set the following environment variable:
```bash
export DATA_DIR="$(pwd)/test_data"
```
`DATA_DIR` can be changed to any other location containing the data to train on.
We assume that `DATA_DIR` contains the following files:
```bash
src-test.txt    src-train.txt   src-valid.txt   tgt-test.txt    tgt-train.txt   tgt-valid.txt
```

## Subword tokenization

We train a SentencePiece tokenizer on the train split:
```bash
export VOCAB_SIZE=200  # for the production model, a size of 16000 is used
paragraph2actions-create-tokenizer -i $DATA_DIR/src-train.txt -i $DATA_DIR/tgt-train.txt -m $DATA_DIR/sp_model -v $VOCAB_SIZE
```

We then tokenize the data:
```bash
paragraph2actions-tokenize -m $DATA_DIR/sp_model.model -i $DATA_DIR/src-train.txt -o $DATA_DIR/tok-src-train.txt
paragraph2actions-tokenize -m $DATA_DIR/sp_model.model -i $DATA_DIR/src-valid.txt -o $DATA_DIR/tok-src-valid.txt
paragraph2actions-tokenize -m $DATA_DIR/sp_model.model -i $DATA_DIR/tgt-train.txt -o $DATA_DIR/tok-tgt-train.txt
paragraph2actions-tokenize -m $DATA_DIR/sp_model.model -i $DATA_DIR/tgt-valid.txt -o $DATA_DIR/tok-tgt-valid.txt
```

## Training

Convert the data to the format required by OpenNMT:
```bash
onmt_preprocess \
  -train_src $DATA_DIR/tok-src-train.txt -train_tgt $DATA_DIR/tok-tgt-train.txt \
  -valid_src $DATA_DIR/tok-src-valid.txt -valid_tgt $DATA_DIR/tok-tgt-valid.txt \
  -save_data $DATA_DIR/preprocessed -src_seq_length 300 -tgt_seq_length 300 \
  -src_vocab_size $VOCAB_SIZE -tgt_vocab_size $VOCAB_SIZE -share_vocab
```

To then train the transformer model with OpenNMT: 
```bash
onmt_train \
  -data $DATA_DIR/preprocessed  -save_model  $DATA_DIR/models/model  \
  -seed 42 -save_checkpoint_steps 10000 -keep_checkpoint 5 \
  -train_steps 500000 -param_init 0  -param_init_glorot -max_generator_batches 32 \
  -batch_size 4096 -batch_type tokens -normalization tokens -max_grad_norm 0  -accum_count 4 \
  -optim adam -adam_beta1 0.9 -adam_beta2 0.998 -decay_method noam -warmup_steps 8000  \
  -learning_rate 2 -label_smoothing 0.0 -report_every 1000  -valid_batch_size 32 \
  -layers 4 -rnn_size 256 -word_vec_size 256 -encoder_type transformer -decoder_type transformer \
  -dropout 0.1 -position_encoding -share_embeddings -valid_steps 20000 \
  -global_attention general -global_attention_function softmax -self_attn_type scaled-dot \
  -heads 8 -transformer_ff 2048
```
Training the model can take up to a few days in a GPU-enabled environment.
For testing purposes in a CPU-only environment, the same command with `-save_checkpoint_steps 10` and `-train_steps 10` will take only a few minutes.

## Finetuning

For finetuning, we first generate appropriate data in OpenNMT format by following the steps described above.
We assume that the preprocessed data is then available as `$DATA_DIR/preprocessed_finetuning `

We then use the same training command with slightly different parameters 
```bash
onmt_train \
  -data $DATA_DIR/preprocessed_finetuning  \
  -train_from $DATA_DIR/models/model_step_500000.pt \
  -save_model  $DATA_DIR/models/model  \
  -seed 42 -save_checkpoint_steps 1000 -keep_checkpoint 40 \
  -train_steps 530000 -param_init 0  -param_init_glorot -max_generator_batches 32 \
  -batch_size 4096 -batch_type tokens -normalization tokens -max_grad_norm 0  -accum_count 4 \
  -optim adam -adam_beta1 0.9 -adam_beta2 0.998 -decay_method noam -warmup_steps 8000  \
  -learning_rate 2 -label_smoothing 0.0 -report_every 200  -valid_batch_size 512 \
  -layers 4 -rnn_size 256 -word_vec_size 256 -encoder_type transformer -decoder_type transformer \
  -dropout 0.1 -position_encoding -share_embeddings -valid_steps 200 \
  -global_attention general -global_attention_function softmax -self_attn_type scaled-dot \
  -heads 8 -transformer_ff 2048
```

## Extraction of actions with the transformer model

Experimental procedure sentences can then be translated to action sequences with the following:
```bash
# Update the path to the OpenNMT model as required
export MODEL="$DATA_DIR/models/model_step_520000.pt"

paragraph2actions-translate -t $MODEL -p $DATA_DIR/sp_model.model -s $DATA_DIR/src-test.txt -o $DATA_DIR/pred.txt
```

## Evaluation

To print the metrics on the predictions, the following command can be used:
```bash
paragraph2actions-calculate-metrics -g $DATA_DIR/tgt-test.txt -p $DATA_DIR/pred.txt
```


# Data augmentation

The following code illustrate how to augment the data for existing sentences and associated action sequences.

```python
from paragraph2actions.augmentation.compound_name_augmenter import CompoundNameAugmenter
from paragraph2actions.augmentation.compound_quantity_augmenter import CompoundQuantityAugmenter
from paragraph2actions.augmentation.duration_augmenter import DurationAugmenter
from paragraph2actions.augmentation.temperature_augmenter import TemperatureAugmenter
from paragraph2actions.misc import load_samples, TextWithActions
from paragraph2actions.readable_converter import ReadableConverter

converter = ReadableConverter()
samples = load_samples('test_data/src-test.txt', 'test_data/tgt-test.txt', converter)

cna = CompoundNameAugmenter(0.5, ['NaH', 'hydrogen', 'C2H6', 'water'])
cqa = CompoundQuantityAugmenter(0.5, ['5.0 g', '8 mL', '3 mmol'])
da = DurationAugmenter(0.5, ['overnight', '15 minutes', '6 h'])
ta = TemperatureAugmenter(0.5, ['room temperature', '30 °C', '-5 °C'])


def augment(sample: TextWithActions) -> TextWithActions:
    sample = cna.augment(sample)
    sample = cqa.augment(sample)
    sample = da.augment(sample)
    sample = ta.augment(sample)
    return sample


for sample in samples:
    print('Original:')
    print(sample.text)
    print(converter.actions_to_string(sample.actions))
    for _ in range(5):
        augmented = augment(sample)
        print('  Augmented:')
        print(' ', augmented.text)
        print(' ', converter.actions_to_string(augmented.actions))
    print()
```
This script can produce the following output:
```
Original:
The reaction mixture is allowed to warm to room temperature and stirred overnight.
STIR for overnight at room temperature.
  Augmented:
  The reaction mixture is allowed to warm to -5 °C and stirred overnight.
  STIR for overnight at -5 °C.
  Augmented:
  The reaction mixture is allowed to warm to room temperature and stirred 15 minutes.
  STIR for 15 minutes at room temperature.
[...]
```

# Action post-processing

The following code illustrate the postprocessing of actions.

```python
from paragraph2actions.postprocessing.filter_postprocessor import FilterPostprocessor
from paragraph2actions.postprocessing.noaction_postprocessor import NoActionPostprocessor
from paragraph2actions.postprocessing.postprocessor_combiner import PostprocessorCombiner
from paragraph2actions.postprocessing.wait_postprocessor import WaitPostprocessor
from paragraph2actions.readable_converter import ReadableConverter

converter = ReadableConverter()
postprocessor = PostprocessorCombiner([
    FilterPostprocessor(),
    NoActionPostprocessor(),
    WaitPostprocessor(),
])

original_action_string = 'NOACTION; STIR at 5 °C; WAIT for 10 minutes; FILTER; DRYSOLUTION over sodium sulfate.'
original_actions = converter.string_to_actions(original_action_string)

postprocessed_actions = postprocessor.postprocess(original_actions)
postprocessed_action_string = converter.actions_to_string(postprocessed_actions)

print('Original actions     :', original_action_string)
print('Postprocessed actions:', postprocessed_action_string)
```

The output of this code will be the following:
```
Original actions     : NOACTION; STIR at 5 °C; WAIT for 10 minutes; FILTER; DRYSOLUTION over sodium sulfate.
Postprocessed actions: STIR for 10 minutes at 5 °C; FILTER keep filtrate; DRYSOLUTION over sodium sulfate.
```
