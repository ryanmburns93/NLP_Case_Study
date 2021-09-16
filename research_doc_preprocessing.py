# -*- coding: utf-8 -*-
"""
Created on Wed Sep 15 19:12:36 2021

@author: Ryan
"""

import time
from bs4 import BeautifulSoup
import re
import os
from random import randint
import sys
try:
    from project_utilities import launch_webdriver, \
        gather_file_names, replace_illegal_chars, \
        extract_text_from_pdf_files
    from proprietary_loader import get_xpath_lib
except ModuleNotFoundError:
    sys.path.append(os.getcwd())
    from project_utilities import launch_webdriver, \
        gather_file_names, replace_illegal_chars, \
        extract_text_from_pdf_files
    from proprietary_loader import get_xpath_lib


xpath_lib = get_xpath_lib()


def collect_doc_links(driver, url):
    """Collect the webpage page source for the specified url."""
    driver.get(url)
    time.sleep(randint(30, 60))
    page_source = driver.page_source
    return page_source


def matches_href_but_no_data_section(href):
    """"Assert href attribute but no 'data-ga' class."""
    return href and not re.compile("data-ga").search(href)


def extract_link_list(soup):
    """
    Extract list of links from soup object.

    Parameters
    ----------
    soup : BeautifulSoup Object
        BeautifulSoup object containing page source for single document.

    Returns
    -------
    link_list : list
        List containing relevant url links collected from document page source.
    page_name_list : list
        List containing relevant document page names collected from document
        page source.

    """
    search_list = soup.find_all(href=re.compile("gartner.com/document"))
    tag_list = []
    link_list = []
    page_name_list = []
    for result in search_list:
        name_temp = result.string
        link_temp = result.attrs
        if len(link_temp) == 1:
            tag_list.append(link_temp)
            page_name_list.append(name_temp)
    for link in tag_list:
        link_list.append(link['href'])
    return link_list, page_name_list


def get_full_doc_view_link(link):
    """Convert url to access full document view."""
    link_base = link.split('?')[0]
    link = link_base + '?toggle=1'
    return(link)


def download_docs(driver, link_list, page_name_list,
                  download_type, save_dir):
    """
    Download all listed research documents.

    Parameters
    ----------
    driver : webdriver Object
        Initialized webdriver for retrieving and manipulating web pages.
    link_list : list
        List of url addresses for documents to download.
    page_name_list : list
        List of document titles downloaded from links in link_list. The
        link_list and page_name_list should be the same length.
    download_type : string
        Signal for whether to collect the page source and save to a .txt file
        or navigate to the download button and download pdf version hosted on
        website.

    Raises
    ------
    ValueError
        Prompt user to retry function call with correct download_type string
        option (either 'source' or 'pdf').

    Returns
    -------
    None.

    """
    if download_type == 'source':
        for link_index in range(len(link_list)):
            link = get_full_doc_view_link(link_list[link_index])
            driver.get(link)
            rand = randint(3, 30)
            print(f'Starting wait {rand} seconds.')
            time.sleep(rand)
            temp_page_source = driver.page_source
            temp_soup = BeautifulSoup(temp_page_source)
            filename = page_name_list[link_index]
            filename = replace_illegal_chars(filename)
            with open(os.path.join(save_dir, (filename + '.txt')),
                      "wb+") as file:
                file.write(temp_soup.encode('utf-8'))
            assert file.closed
            rand = randint(15, 60)
            print(f'Starting wait {rand} second wait.')
            time.sleep(rand)
            print(f"Completed scraping document {link_index+1}" +
                  f" of {len(link_list)} - {page_name_list[link_index]}")
        return
    elif download_type == 'pdf':
        for link_index in range(len(link_list)):
            link = get_full_doc_view_link(link_list[link_index])
            driver.get(link)
            rand = randint(3, 30)
            print(f'Page loaded, starting warmup wait {rand} seconds.')
            time.sleep(rand)
            try:
                full_document_button = (driver.
                                        find_element_by_xpath(
                                            xpath_lib['full_document_button']
                                            ))
                full_document_button.click()
                time.sleep(randint(0, 2))
                page_download_button = (driver.
                                        find_element_by_xpath(
                                            xpath_lib[
                                                'download_attachments_button']
                                            ))
                page_download_button.click()
            except Exception:
                pass
            try:
                select_downloads_btn_list = (driver.
                                             find_elements_by_xpath(
                                                 xpath_lib[
                                                     'select_downloads_button']
                                                 ))
                downloads_count = len(select_downloads_btn_list)
                if downloads_count > 4:
                    print(f'Many downloads for {page_name_list[link_index]}, '
                          f'index {link_index}. Skipping download for now.')
                else:
                    for button_count in range(downloads_count):
                        button = select_downloads_btn_list[button_count]
                        button.click()
                        time.sleep(randint(0, 7))
                        print(f"Completed scraping document {link_index+1}" +
                              f" of {len(link_list)} - " +
                              f"{page_name_list[link_index]}, attachment " +
                              f"{button_count+1} of {downloads_count}.")
                    rand = randint(15, 60)
                    print(f'Done downloading, starting cooldown '
                          f'wait {rand} seconds.')
                    time.sleep(rand)
            except Exception:
                print(f'Unable to download {page_name_list[link_index]}. '
                      'Passing.')
        return
    else:
        raise ValueError("download_type should be 'pdf' or 'source',"
                         "please try again.")
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
    url = input('Please enter your target url for webscraping: ')
    save_dir = input('Please enter the directory where you would'
                     ' like to save your files: ')
    save_type = prompt_for_save_type()
    page_source = collect_doc_links(driver, url)
    soup = BeautifulSoup(page_source)
    link_list, page_name_list = extract_link_list(soup)
    download_docs(driver, link_list, page_name_list, save_type,
                  save_dir)
    if save_type == 'pdf':
        pdf_file_list = gather_file_names(save_dir, 'pdf')
        extract_text_from_pdf_files(pdf_file_list, save_dir)


#if __name__ == "__main__":
#    main()
