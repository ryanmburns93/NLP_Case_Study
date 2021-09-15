# -*- coding: utf-8 -*-
"""
Created on Tue Sep 14 13:12:03 2021

@author: Ryan
"""

from pprint import pprint
import os
from tokenization import FullTokenizer


def manual_validation(sentence_list, max_character_length=500, num_cycles=3):
    long_sentence_index_bank = []
    cycle_count = 0
    starting_max_character_length = (max_character_length + num_cycles*20)
    sentence_count = len(sentence_list)
    while cycle_count < num_cycles:
        i = 0
        while i < sentence_count:
            if i in long_sentence_index_bank:
                i += 1
            elif len(sentence_list[i]) > (starting_max_character_length
                                          - 20*cycle_count):
                pprint(f'{i} ({len(sentence_list[i]) chars}):'
                       f'{sentence_list[i]}')
                split_word = input("Enter split word/phrase "
                                   "or 'None' if not needed: ")
                if split_word == 'None':
                    long_sentence_index_bank.append(i)
                    i += 1
                elif split_word not in sentence_list[i]:
                    pprint('Was that a typo? Cannot find phrase in sentence.'
                           'Try again?')
                    continue
                else:
                    temp_split_sents_list = sentence_list[i].split(split_word,
                                                                   1)
                    temp_split_sents_list[-1] = (split_word +
                                                 temp_split_sents_list[-1])
                    sentence_list = (sentence_list[:i] +
                                     temp_split_sents_list +
                                     sentence_list[i+1:])
                    # adjust long sentences index to account for new list index
                    for num in long_sentence_index_bank:
                        if i < num:
                            num += 1
                    i += 2
                    sentence_count += 1
            else:
                i += 1
        cycle_count += 1
        pprint(f'Completed review cycle {cycle_count} of {num_cycles}')
    return(sentence_list)


def add_document_line_breaks(sentence_list):
    sentence_count = len(sentence_list)
    i = 0
    split_doc = []
    while i < sentence_count:
        if 'By ' in sentence_list[i]:
            print(sentence_list[i])
            input_val = input("Beginning of document? Enter 'y' or 'n': ")
            if input_val == 'y':
                sentence_list = sentence_list.append('') + sentence_list[i+1:]
            sentence_count = len(sentence_list)
    return(sentence_list)


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

    tokenizer = FullTokenizer(vocab_file=vocab_file, do_lower_case=True)
    unique_label_list = set(label_list)
    unique_label_list = list(unique_label_list)

    if split_type == 'train':
        output_filename = os.path.join(save_dir,
                                       f'{model_size}_train_tf_'
                                       'examples.tfrecord')
        train_examples = create_examples(text_list=text_list,
                                         label_list=label_list,
                                         set_type=split_type)
        file_based_convert_examples_to_features(examples=train_examples,
                                                label_list=label_list,
                                                max_seq_length=MAX_SEQ_LENGTH,
                                                tokenizer=tokenizer,
                                                output_file=output_filename)
        return
    elif split_type == 'eval':
        output_filename = os.path.join(save_dir,
                                       f'{model_size}_eval_tf_'
                                       'examples.tfrecord')
        eval_examples = create_examples(text_list=text_list,
                                        label_list=unique_label_list,
                                        set_type='eval')
        file_based_convert_examples_to_features(examples=eval_examples,
                                                label_list=label_list,
                                                max_seq_length=MAX_SEQ_LENGTH,
                                                tokenizer=tokenizer,
                                                output_file=output_eval_filename)
        return
    else:
        return ValueError('Must be a pre-split data frame of eval or ' +
                          'train cuts. Please specify eval or train.')


def create_fintuning_datasets(X_list, y_list, train_eval_split=0.2, save_dir=None):
    if save_dir is None:
        save_dir = os.getcwd()
    assert (len(inquiry_label_list) == len(inquiry_text_list))
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
            print(f'Finished creating {size} model {data_type} data.')
    return
