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
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
try:
    from project_utilities import launch_webdriver, \
        gather_file_names, replace_illegal_chars, \
        extract_text_from_pdf_files
    from proprietary_loader import get_xpath_lib, get_login_info
except ModuleNotFoundError:
    sys.path.append(os.getcwd())
    from project_utilities import launch_webdriver, \
        gather_file_names, replace_illegal_chars, \
        extract_text_from_pdf_files
    from proprietary_loader import get_xpath_lib, get_login_info


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
    xpath_lib = get_xpath_lib()
    if download_type == 'source':
        for index, link in enumerate(link_list):
            link = get_full_doc_view_link(link)
            driver.get(link)
            rand = randint(3, 10)
            print(f'Page loaded, starting warmup wait {rand} seconds.')
            time.sleep(rand)
            wait = WebDriverWait(driver, 10)
            try:
                full_doc_condition = (EC.
                                      element_to_be_clickable(
                                          (By.XPATH,
                                           xpath_lib['full_document_button'])))
                full_document_button = wait.until(full_doc_condition)
                full_document_button.click()
                time.sleep(randint(0, 2))
            except Exception as error:
                print(error)
            temp_page_source = driver.page_source
            temp_soup = BeautifulSoup(temp_page_source, features='lxml')
            filename = page_name_list[index]
            filename = replace_illegal_chars(filename)
            with open(os.path.join(save_dir, (filename + '.txt')),
                      "wb+") as file:
                file.write(temp_soup.encode('utf-8'))
            assert file.closed
            rand = randint(15, 30)
            print(f'Starting wait {rand} second wait.')
            time.sleep(rand)
            print(f"Completed scraping document {index+1}" +
                  f" of {len(link_list)} - {page_name_list[index]}")
        return None
    if download_type == 'pdf':
        for index, link in enumerate(link_list):
            link = get_full_doc_view_link(link)
            driver.get(link)
            rand = randint(3, 15)
            print(f'Page loaded, starting warmup wait {rand} seconds.')
            time.sleep(rand)
            wait = WebDriverWait(driver, 10)
            try:
                full_doc_condition = (EC.
                                      element_to_be_clickable(
                                          (By.XPATH,
                                           xpath_lib['full_document_button'])))
                full_document_button = wait.until(full_doc_condition)
                full_document_button.click()
                time.sleep(randint(0, 2))
            except NoSuchElementException:
                print(f'Unable to find Full Document button. Continuing.')
            try:
                down_attach_condition = (EC.
                                         element_to_be_clickable(
                                             (By.XPATH,
                                              xpath_lib[
                                                  'download_attachments'
                                                  '_button'])))
                page_download_button = wait.until(down_attach_condition)
                page_download_button.click()
            except NoSuchElementException:
                print(f'Unable to find page download button for {page_name_list[index]}.')
            try:
                select_down_condition = (EC.
                                         presence_of_all_elements_located(
                                             (By.XPATH,
                                              xpath_lib['select_downloads'
                                                        '_button'])))
                select_downloads_btn_list = wait.until(select_down_condition)
                downloads_count = len(select_downloads_btn_list)
                if downloads_count > 4:
                    print(f'Many downloads for {page_name_list[index]}, '
                          f'index {index}. Skipping download for now.')
                else:
                    for button_count in range(downloads_count):
                        button = select_downloads_btn_list[button_count]
                        button.click()
                        time.sleep(randint(0, 7))
                        print(f"Completed scraping document {index+1}" +
                              f" of {len(link_list)} - " +
                              f"{page_name_list[index]}, attachment " +
                              f"{button_count+1} of {downloads_count}.")
                    rand = randint(12, 20)
                    print(f'Done downloading, starting cooldown '
                          f'wait {rand} seconds.')
                    time.sleep(rand)
            except Exception:
                print(f'Unable to download {page_name_list[index]}. '
                      'Passing.')
        return None
    raise ValueError("download_type should be 'pdf' or 'source',"
                     "please try again.")


def prompt_for_save_type():
    """Prompt user to input doc type."""
    save_type = None
    while save_type != 'pdf' and save_type != 'source':
        save_type = input("Please enter 'source' or 'pdf' to " +
                          "indicate whether: ")
    return save_type


def login(driver):
    xpath_lib = get_xpath_lib()
    username_field = driver.find_element(By.XPATH,
                                         xpath_lib.get('form_username'))
    username_field.send_keys(get_login_info('username'))
    password_field = driver.find_element(By.XPATH,
                                         xpath_lib.get('form_password'))
    password_field.send_keys(get_login_info('password'))
    login_button = driver.find_element(By.XPATH,
                                       xpath_lib.get('form_login_button'))
    login_button.click()


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


if __name__ == "__main__":
    main()
