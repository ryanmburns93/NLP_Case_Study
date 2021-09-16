# -*- coding: utf-8 -*-
"""
Created on Wed Sep 15 22:10:05 2021

@author: Ryan
"""
from pprint import pprint
import os
from tokenization import FullTokenizer, convert_to_unicode
import time
import sys
import tokenization


def create_examples(text_list, label_list, set_type):
    """Creates examples for the training and dev sets."""
    assert(len(text_list) == len(label_list))
    examples = []
    for i in range(len(text_list)):
        guid = "%s-%s" % (set_type, i)
        text_a = convert_to_unicode(text_list[i])
        text_b = None
        if set_type == "test":
            label = "0"
        else:
            label = convert_to_unicode(label_list[i])
        examples.append(InputExample(guid=guid,
                                     text_a=text_a,
                                     text_b=text_b,
                                     label=label))
    return examples


def file_based_convert_examples_to_features(examples,
                                            label_list,
                                            max_seq_length,
                                            tokenizer,
                                            output_file):
    """Convert a set of `InputExample`s to a TFRecord file."""

    writer = tf.python_io.TFRecordWriter(output_file)

    for (ex_index, example) in enumerate(examples):
        if ex_index % 10000 == 0:
            tf.logging.info("Writing example %d of %d" % (ex_index,
                                                          len(examples)))

        feature = convert_single_example(ex_index, example, label_list,
                                         max_seq_length, tokenizer)

        def create_int_feature(values):
            f = tf.train.Feature(int64_list=tf.
                                 train.Int64List(value=list(values)))
            return f

        features = collections.OrderedDict()
        features["input_ids"] = create_int_feature(feature.input_ids)
        features["input_mask"] = create_int_feature(feature.input_mask)
        features["segment_ids"] = create_int_feature(feature.segment_ids)
        features["label_ids"] = create_int_feature([feature.label_id])
        features["is_real_example"] = (create_int_feature(
            [int(feature.is_real_example)]))

        tf_example = tf.train.Example(features=tf.
                                      train.
                                      Features(feature=features))
        writer.write(tf_example.SerializeToString())
    writer.close()


def convert_examples_to_features(examples, label_list,
                                 max_seq_length, tokenizer):
    """Convert a set of `InputExample`s to a list of `InputFeatures`."""

    features = []
    for (ex_index, example) in enumerate(examples):
        if ex_index % 10000 == 0:
            tf.logging.info("Writing example %d of %d" % (ex_index,
                                                          len(examples)))

        feature = convert_single_example(ex_index, example, label_list,
                                         max_seq_length, tokenizer)

        features.append(feature)
    return features


def convert_single_example(ex_index, example, label_list,
                           max_seq_length, tokenizer):
    """Converts a single `InputExample` into a single `InputFeatures`."""

    if isinstance(example, PaddingInputExample):
        return InputFeatures(
            input_ids=[0] * max_seq_length,
            input_mask=[0] * max_seq_length,
            segment_ids=[0] * max_seq_length,
            label_id=0,
            is_real_example=False)

    label_map = {}
    for (i, label) in enumerate(label_list):
        label_map[label] = i

    tokens_a = tokenizer.tokenize(example.text_a)
    tokens_b = None
    if example.text_b:
        tokens_b = tokenizer.tokenize(example.text_b)

    if tokens_b:
        # Modifies `tokens_a` and `tokens_b` in place so that the total
        # length is less than the specified length.
        # Account for [CLS], [SEP], [SEP] with "- 3"
        pass  # never gonna happen
    else:
        # Account for [CLS] and [SEP] with "- 2"
        if len(tokens_a) > max_seq_length - 2:
            tokens_a = tokens_a[0:(max_seq_length - 2)]

    # The convention in BERT is:
    # (a) For sequence pairs:
    #  tokens:   [CLS] is this jack ##son ##ville ? [SEP] no it is not . [SEP]
    #  type_ids: 0     0  0    0    0     0       0 0     1  1  1  1   1 1
    # (b) For single sequences:
    #  tokens:   [CLS] the dog is hairy . [SEP]
    #  type_ids: 0     0   0   0  0     0 0
    #
    # Where "type_ids" are used to indicate whether this is the first
    # sequence or the second sequence. The embedding vectors for `type=0` and
    # `type=1` were learned during pre-training and are added to the wordpiece
    # embedding vector (and position vector). This is not *strictly* necessary
    # since the [SEP] token unambiguously separates the sequences, but it makes
    # it easier for the model to learn the concept of sequences.
    #
    # For classification tasks, the first vector (corresponding to [CLS]) is
    # used as the "sentence vector". Note that this only makes sense because
    # the entire model is fine-tuned.
    tokens = []
    segment_ids = []
    tokens.append("[CLS]")
    segment_ids.append(0)
    for token in tokens_a:
        tokens.append(token)
        segment_ids.append(0)
    tokens.append("[SEP]")
    segment_ids.append(0)

    if tokens_b:
        for token in tokens_b:
            tokens.append(token)
            segment_ids.append(1)
        tokens.append("[SEP]")
        segment_ids.append(1)

    input_ids = tokenizer.convert_tokens_to_ids(tokens)

    # The mask has 1 for real tokens and 0 for padding tokens. Only real
    # tokens are attended to.
    input_mask = [1] * len(input_ids)

    # Zero-pad up to the sequence length.
    while len(input_ids) < max_seq_length:
        input_ids.append(0)
        input_mask.append(0)
        segment_ids.append(0)

    assert len(input_ids) == max_seq_length
    assert len(input_mask) == max_seq_length
    assert len(segment_ids) == max_seq_length

    label_id = label_map[example.label]
    if ex_index < 5:
        tf.logging.info("*** Example ***")
        tf.logging.info("guid: %s" % (example.guid))
        tf.logging.info("tokens: %s" % " ".join(
            [printable_text(x) for x in tokens]))
        tf.logging.info("input_ids: %s" % " ".join([str(x) for
                                                    x in input_ids]))
        tf.logging.info("input_mask: %s" % " ".join([str(x) for
                                                     x in input_mask]))
        tf.logging.info("segment_ids: %s" % " ".join([str(x) for
                                                      x in segment_ids]))
        tf.logging.info("label: %s (id = %d)" % (example.label, label_id))

    feature = InputFeatures(
        input_ids=input_ids,
        input_mask=input_mask,
        segment_ids=segment_ids,
        label_id=label_id,
        is_real_example=True)
    return feature


def create_single_data_split(model_size, text_list,
                             label_list, split_type,
                             save_dir, vocab_file):
    # create single examples from data
    model_size = model_size.lower()
    vocab_file = vocab_file
    if model_size == 'tiny':
        MAX_SEQ_LENGTH = 128
    elif model_size == 'mini':
        MAX_SEQ_LENGTH = 256
    elif model_size == 'medium':
        MAX_SEQ_LENGTH = 512
    else:
        raise ValueError("Unsupported model size.")

    if split_type != 'eval' and split_type != 'train':
        raise ValueError('Must be a pre-split data frame of eval or ' +
                         'train cuts. Please specify eval or train.')

    tokenizer = FullTokenizer(vocab_file=vocab_file, do_lower_case=True)
    unique_label_list = set(label_list)
    unique_label_list = list(unique_label_list)

    output_filename = os.path.join(save_dir,
                                   f'{model_size}_{split_type}_tf_'
                                   'examples.tfrecord')
    examples = create_examples(text_list=text_list,
                               label_list=label_list,
                               set_type=split_type)
    file_based_convert_examples_to_features(examples=examples,
                                            label_list=label_list,
                                            max_seq_length=MAX_SEQ_LENGTH,
                                            tokenizer=tokenizer,
                                            output_file=output_filename)
    return


def create_fintuning_datasets(X_list, y_list,
                              train_eval_split=0.2, save_dir=None,
                              vocab_file=None):
    if save_dir is None:
        save_dir = os.getcwd()
    assert (len(X_list) == len(y_list))
    y_list = list(y_list)
    X_list = list(X_list)

    X_list = [text.replace('\n\n', ' ') for
              text in X_list]
    X_list = [text.replace('\n', ' ') for
              text in X_list]
    X_list = [text.replace('\t', ' ') for
              text in X_list]

    for data_type in ['train', 'eval']:
        for model_size in ['Tiny', 'Mini', 'Medium']:
            create_single_data_split(model_size,
                                     X_list,
                                     y_list,
                                     data_type,
                                     save_dir,
                                     vocab_file)
            print(f'Finished creating {model_size} model {data_type} data.')
    return