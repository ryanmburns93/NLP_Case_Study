# -*- coding: utf-8 -*-
"""
Created on Wed Sep 15 23:46:30 2021

@author: Ryan
"""
from random import randint
import numpy as np
import pandas as pd
import time
from bs4 import BeautifulSoup
import os
import sys
try:
    from project_utilities import scroll, launch_webdriver, \
        gather_file_names, replace_illegal_chars, \
        extract_text_from_pdf_files
    from proprietary_loader import load_request_data, \
        get_topic_search_url, get_xpath_lib, \
        get_target_topic_list
    from research_doc_preprocessing import download_docs
except ModuleNotFoundError or ImportError:
    sys.path.append(os.getcwd())
    from project_utilities import scroll, launch_webdriver, \
        gather_file_names, replace_illegal_chars, \
        extract_text_from_pdf_files
    from proprietary_loader import load_request_data, \
        get_topic_search_url, get_xpath_lib, \
        get_target_topic_list
    from research_doc_preprocessing import download_docs


xpath_lib = get_xpath_lib()


def get_topic_search_results(topic, driver):
    """
    Capture search results page source for single intiative.

    Topics are the content verticals defined by *Alpha Corporation
    into which research documents are published. Infinite scrolling of
    search results page allows capture of all unarchived documents tagged to
    a topic in the page source.

    Parameters
    ----------
    topic : string
        String of topic to filter by in search.
    driver : webdriver Object
        Initialized webdriver for retrieving and manipulating web pages.

    Returns
    -------
    topic_page_source : string
        String of entire webpage source from fully-scrolled search
        results page filtered by a single topic.

    """
    url = get_topic_search_url(topic)
    driver.get(url)
    num_results = -1
    search_results_list = []
    while num_results < len(search_results_list):
        num_results = len(search_results_list)
        scroll(driver, randint(2, 5))
        search_results_list = (driver.
                               find_elements_by_xpath(
                                   xpath_lib['search_results_list']))
    topic_page_source = driver.page_source
    return topic_page_source


def collect_topic_search_results(driver, save_dir):
    """
    Collect topic search results page source. Parse and save to .txt file.

    In the case of Alpha* Corporation, the topic of a request is assigned
    on completion, while unsupported requests, scheduling difficulties,
    or other factors may prevent the request from being fulfilled. Filtering
    to requests which had been tagged to a topic cut the total number of
    requests by approximately half.

    Parameters
    ----------
    driver : webdriver Object
        Initialized webdriver for retrieving and manipulating web pages.

    Returns
    -------
    None.

    """
    total_request_df = load_request_data()
    topic_list = total_request_df.KI.unique()
    topic_list = list(topic_list)
    topic_list.remove(np.NaN)
    i = 0
    for topic in topic_list:
        filename = topic
        filename = replace_illegal_chars(filename)
        filename = (save_dir + topic + '.txt')
        source = get_topic_search_results(topic, driver)
        soup = BeautifulSoup(source)
        with open(filename, 'wb') as file:
            file.write(soup.encode('utf-8'))
        print(f'Completed topic {i+1} of {len(topic_list)}'
              f' - {topic}.')
        i += 1
        time.sleep(randint(5, 10))
    return


def collect_foundational_links(search_results_filename, save_dir):
    """
    Harvest 'foundational' doc names and links from search results page source.

    Certain research documents are tagged as 'foundational' to an topic
    by the authors. These documents serve as cornerstones of client advisory
    conversations and support.

    Parameters
    ----------
    search_results_filename : string
        Name of the .txt file containing the saved topic search results
        page source.

    Returns
    -------
    link_list : list
        List of url links to 'foundational' documents for single topic.
    name_list : list
        List of 'foundational' documents names for single topic.

    """
    with open(os.path.join(save_dir,
                           search_results_filename),
              'r+', encoding='utf-8') as file:
        source = file.read()
    soup = BeautifulSoup(source)
    link_list = []
    name_list = []
    for card in soup.find_all('div', 'all-card-title-grid'):
        if ('foundational' in (card.next_sibling.
                               next_element.next_element.get('class'))):
            link_list.append(card.find('a').get('href'))
            name_list.append(card.text)
    assert(len(link_list) == len(name_list))
    return link_list, name_list


def retrieve_foundational_doc_links(save_dir):
    """
    Construct dataframe with all topics, foundational docs, and url links.

    Returns
    -------
    foundational_link_df : pandas dataframe
        Dataframe containing all 'foundational' document file names, url links,
        and the respective topic to which the document is tagged.

    """
    filename_list = gather_file_names(save_dir, 'txt')
    foundational_link_df = pd.DataFrame(columns=['topic_name',
                                                 'link',
                                                 'doc_name'])
    i = 0
    file_count = len(filename_list)
    for file in filename_list:
        link_list, name_list = collect_foundational_links(file, save_dir)
        for index_val in range(len(link_list)):
            temp = pd.DataFrame({'topic_name': file[:-4],
                                 'link': link_list[index_val],
                                 'doc_name': name_list[index_val]}, index=[0])
            foundational_link_df = pd.concat([foundational_link_df, temp],
                                             ignore_index=True)
        i += 1
        print('Completed {:0.2f}% of files.'.format((i/file_count)*100))
    return foundational_link_df


def download_foundational_files(driver, foundational_link_df,
                                save_type, save_dir):
    """Download each foundational document file."""
    link_list = list(foundational_link_df.link)
    page_name_list = list(foundational_link_df.doc_name)
    download_docs(driver, link_list, page_name_list, save_type, save_dir)
    return


def prompt_for_save_type():
    """Prompt user to input doc type."""
    save_type = None
    while save_type != 'pdf' and save_type != 'source':
        save_type = input("Please enter 'source' or 'pdf' to " +
                          "indicate whether: ")
    return save_type


def main():
    driver = launch_webdriver()
    save_dir = input('Please enter the directory where you would'
                     ' like to save your files: ')
    save_type = prompt_for_save_type()
    collect_topic_search_results()
    foundational_link_df = retrieve_foundational_doc_links()
    target_topic_list = get_target_topic_list(level=1)
    filtered_link_df = foundational_link_df[foundational_link_df.
                                            topic_name.
                                            isin(target_topic_list)]
    download_foundational_files(driver, filtered_link_df,
                                save_type, save_dir)
    if save_type == 'pdf':
        pdf_file_list = gather_file_names(save_dir, 'pdf')
        extract_text_from_pdf_files(pdf_file_list, save_dir)


if __name__ == "__main__":
    main()
