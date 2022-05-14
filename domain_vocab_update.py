# -*- coding: utf-8 -*-
"""
Created on Thu Sep 16 00:59:28 2021

@author: Ryan
"""

import bvb_tokenizer
from nltk.corpus import stopwords
import pandas as pd
import os


def get_vocab_and_corpus_paths():
    """
    Prompt the user for the string paths to the BERT vocab and full corpus file.

    Returns
    -------
    BERT_vocab_file_loc : str
        The string path to the BERT vocabulary words file.
    total_corpus_txt_file_loc : str
        The string path to the full training corpus .txt file.

    """
    BERT_vocab_file_loc = input('Please enter the full filepath to the '
                                'BERT pretrained model vocabulary: ')
    total_corpus_txt_file_loc = input('Please enter the full filepath to '
                                      'the total corpus .txt file: ')
    return BERT_vocab_file_loc, total_corpus_txt_file_loc


def read_vocab_files(BERT_vocab_file_loc, total_corpus_txt_file_loc):
    """
    Read the BERT vocab and corpus files into memory and return list of 
    BERT vocab and lowercase corpus sentences.

    Parameters
    -------
    BERT_vocab_file_loc : str
        The string path to the BERT vocabulary words file.
    total_corpus_txt_file_loc : str
        The string path to the full training corpus .txt file.

    Returns
    -------
    pretrained_vocab : list
        List of all BERT pretrained vocabulary words.
    sentences_list : list
        List of all lowercase sentences in the training corpus.

    """
    # confirmed all vocab files are same across models
    with open(BERT_vocab_file_loc, 'r', encoding='utf-8') as file:
        pretrained_vocab = file.readlines()
    # read in single .txt with total corpus
    with open(total_corpus_txt_file_loc,
              'r', encoding='utf-8') as file:
        sentences_list = file.readlines()
        sentences_list = [sentence.lower() for sentence in sentences_list]
    return pretrained_vocab, sentences_list


def create_token_dict_from_corpus(total_corpus_txt_file_loc):
    """
    Create a token count dictionary with an ordered list of tokens appearing
    in the target corpus and the frequency of the tokens' appearances.

    Parameters
    -------
    total_corpus_txt_file_loc : str
        The string path to the full training corpus .txt file.

    Returns
    -------
    token_count_dict : dict
        Dictionary of corpus tokens and appearance frequency.

    """
    stop_words = set(stopwords.words('english'))
    token_count = bvb_tokenizer.corpus_token_counts(total_corpus_txt_file_loc,
                                                    None)
    token_count_dict = dict(sorted(token_count.items(),
                                   key=lambda item: item[1],
                                   reverse=True))
    for subword in list(token_count_dict.keys()):
        # remove punctuation-only tokens from dictionary
        if any(char.isalpha() for char in subword):
            pass
        else:
            token_count_dict.pop(subword)
        # remove stop words from dictionary
        if subword in stop_words:
            token_count_dict.pop(subword)
    return token_count_dict


def merge_domain_vocab(token_count_dict,
                       pretrained_vocab,
                       min_token_count=0,
                       max_token_count=None,
                       max_domain_vocab_additions=994):
    """
    Create a token count dictionary with an ordered list of tokens appearing
    in the target corpus and the frequency of the tokens' appearances.

    Parameters
    -------
    token_count_dict : dict
        Dictionary of corpus tokens and appearance frequency.
    pretrained_vocab : list
        List of all BERT pretrained vocabulary words.
    min_token_count : int, optional
        Minimum number of times a token must appear in the corpus to be 
        included in the combined list of pretrained vocabulary and domain-specific
        vocabulary identified in the corpus. The default is 0.
    max_token_count : int, optional
        Maximum number of times a token may appear in the corpus before
        exclusion from the combined list of pretrained vocabulary and domain-specific
        vocabulary identified in the corpus. The default is None.
    max_domain_vocab_additions : int, optional
        The maximum number of new vocabulary permitted to be added to the combined 
        vocabulary list sourced from the target corpus.

    Returns
    -------
    pretrained_vocab : list
        List of vocabulary from BERT pretraining and the target corpus to use for
        further pretraining.

    """
    if max_domain_vocab_additions > 994:
        raise ValueError('BERT models only have 994 available vocabulary slots'
                         ' for domain adaption.')
    vocab_additions_df = pd.DataFrame(columns=['vocab', 'count'])
    for item in token_count_dict.items():
        if item[1] > min_token_count:
            temp_df = pd.DataFrame({'vocab': item[0],
                                    'count': item[1]},
                                   index=[0])
            vocab_additions_df = vocab_additions_df.append(temp_df,
                                                           ignore_index=True)

    # number of available vocab words: len(unused_index_list) = 994
    top_domain_vocab = list(token_count_dict.
                            items())[:max_domain_vocab_additions]

    # time to replace the unused tokens in the vocab files
    temp_count = 0
    k = 0
    while temp_count < max_domain_vocab_additions:
        subword = pretrained_vocab[k]
        if 'unused' in subword:
            pretrained_vocab[k] = top_domain_vocab[temp_count][0]
            temp_count += 1
        k += 1
    return pretrained_vocab


def main():
    """
    Add valuable words identified in the target corpus to the existing
    BERT pretraining vocabulary list to continue pretraining on the
    target corpus.

    Returns
    -------
    None.

    """
    (BERT_vocab_file_loc,
     total_corpus_txt_file_loc) = get_vocab_and_corpus_paths()
    pretrained_vocab = read_vocab_files(BERT_vocab_file_loc,
                                        total_corpus_txt_file_loc)
    domain_token_count_dict = create_token_dict_from_corpus(
        total_corpus_txt_file_loc)
    enhanced_vocab = merge_domain_vocab(domain_token_count_dict,
                                        pretrained_vocab)

    with open(os.path.join(os.getcwd(), 'domain_corpus_vocab.txt'), 'w+',
              encoding='utf-8') as file:
        for token in enhanced_vocab:
            file.write(token)
            file.write('\n')


if __name__ == "__main__":
    main()
