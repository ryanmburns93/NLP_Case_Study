# -*- coding: utf-8 -*-
"""
Created on Tue Sep 14 13:12:03 2021

@author: Ryan Burns
"""

from pprint import pprint
import os
import time
import sys
import ctypes
from ctypes import windll, wintypes
from uuid import UUID
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from glob import glob
import subprocess
from subprocess import TimeoutExpired
import tika
from tika import parser


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
                pprint(f'{i} ({len(sentence_list[i])} chars):'
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
#   split_doc = []
    while i < sentence_count:
        if 'By ' in sentence_list[i]:
            print(sentence_list[i])
            input_val = input("Beginning of document? Enter 'y' or 'n': ")
            if input_val == 'y':
                sentence_list = sentence_list.append('') + sentence_list[i+1:]
            sentence_count = len(sentence_list)
    return sentence_list


def scroll(driver, timeout):
    """
    Scroll down webpage with infinite scroll.

    This function is a slightly modified version of the code from
    artjomb at https://gist.github.com/artjomb/07209e859f9bf0206f76.

    Parameters
    ----------
    driver : webdriver Object
        Initialized webdriver for retrieving and manipulating web pages.
    timeout : int
        The number of seconds to put the driver to sleep before continuing
        to scroll. This can be modified depending on connectivity and webpage
        update speeds, so long as the page is given time to load before
        scrolling further.

    Returns
    -------
    None.

    """
    scroll_pause_time = timeout

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        (driver.
         execute_script("window.scrollTo(0, document.body.scrollHeight);"))

        # Wait to load page
        time.sleep(scroll_pause_time)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # If heights are the same it will exit the function
            break
        last_height = new_height
    return


def launch_webdriver(webdriver_path=None):
    """
    Instantiate the webdriver application.

    Need to save updated webdriver application to downloads folder or
    hardcode path to webdriver. Options can also be set to run a
    headless webdriver, but this is not the given state due to login
    requirements.

    Parameters
    ----------
    webdriver_path : string, optional
        Alternate filepath to directory containing chromedriver.exe.
        The default is None.

    Returns
    -------
    driver : webdriver
        Initialized webdriver for retrieving and manipulating web pages.
    """
    options = Options()
    if webdriver_path is None:
        go_to_downloads()
    driver_filepath = (os.path.join(os.getcwd(), 'chromedriver.exe'))
    sys.path.append(driver_filepath)
    driver = webdriver.Chrome(driver_filepath,
                              options=options)
    return driver


def go_to_downloads():
    """
    Navigate to downloads folder regardless of OS.

    This function is a modified version of the code from
    Michael Kropat at https://gist.github.com/mkropat/7550097.

    Returns
    -------
    new_wd : string
        Path to the new working directory (which should be the
        Downloads folder).

    """
    if os.name == 'nt':

        # ctypes GUID copied from MSDN sample code
        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", wintypes.BYTE * 8)
            ]

            def __init__(self, uuidstr):
                uuid = UUID(uuidstr)
                ctypes.Structure.__init__(self)
                self.Data1, self.Data2, self.Data3, \
                    self.Data4[0], self.Data4[1], rest = uuid.fields
                for i in range(2, 8):
                    self.Data4[i] = rest >> (8-i-1)*8 & 0xff

        SHGetKnownFolderPath = windll.shell32.SHGetKnownFolderPath
        SHGetKnownFolderPath.argtypes = [
            ctypes.POINTER(GUID), wintypes.DWORD,
            wintypes.HANDLE, ctypes.POINTER(ctypes.c_wchar_p)
        ]

        def _get_known_folder_path(uuidstr):
            pathptr = ctypes.c_wchar_p()
            guid = GUID(uuidstr)
            if SHGetKnownFolderPath(ctypes.byref(guid),
                                    0,
                                    0,
                                    ctypes.byref(pathptr)):
                raise ctypes.WinError()
            return pathptr.value

        FOLDERID_Download = '{374DE290-123F-4565-9164-39C4925E467B}'

        def get_download_folder():
            new_wd = _get_known_folder_path(FOLDERID_Download)
            os.chdir(new_wd)
            return new_wd
    else:
        def get_download_folder():
            home = os.path.expanduser("~")
            new_wd = os.path.join(home, "Downloads")
            os.chdir(new_wd)
            return new_wd
    get_download_folder()
    return None


def gather_file_names(file_loc, file_type):
    """Gather list of file names of single type."""
    dir_temp = os.getcwd()
    os.chdir(file_loc)
    filename_list = glob("*."+file_type)
    os.chdir(dir_temp)
    return filename_list


def replace_illegal_chars(filename):
    """
    Remove illegal characters from filename.

    Parameters
    ----------
    filename : string
        String of file name (not including full file path).

    Returns
    -------
    new_filename : string
        String of file name without illegal characters which
        would raise an error or prevent OS from saving (validated against
        Windows system only).

    """
    illegal_char_string = ("\\#" + "\\%" + "\\&" + "\\{" + "\\}" + "\\$" +
                           "\\!" + "\\'" + "\\@" + "\\+" + "\\`" + "\\=" +
                           "\\<" + "\\>" + "\\:" + '\\"' + "\\/" + "\\|" +
                           "\\?" + "\\*" + "' '")
    new_filename = ''
    for char in list(filename):
        if char in list(illegal_char_string):
            pass
        else:
            new_filename = new_filename + char
    if len(new_filename) < 2:
        new_filename = 'RENAME-NEEDED'
    return new_filename


def extract_text_from_pdf_files(file_location_list, save_dir):
    """
    Extract text from pdf document. Save to .txt file.

    Parameters
    ----------
    file_location_list : list
        List of .pdf files by full file path and name.

    Returns
    -------
    None.

    """
    # https://stackoverflow.com/questions/33073972/how-can-i-use-tika-packagehttps-github-com-chrismattmann-tika-python-in-pyth/36628583#36628583
    # Tika appears to run without the setup, but if it poses issues see the
    # above StackOverflow thread. To set up Tika, run in cmd:
    # java -jar <full path to downloaded tika-server-standard-2.1.0.jar file>
    # this sets server output address which is used in parser call below
    # after this is called in cmd, run in python:
    # tika.TikaClientOnly = True
    go_to_downloads()
    try:
        subprocess.run(["java",
                        "-jar",
                        os.path.join(os.getcwd(),
                                     'tika-server-standard-2.1.0.jar')],
                       timeout=5,
                       check=True)
    except TimeoutExpired:
        pass
    finally:
        tika.TikaClientOnly = True
    for index, file_loc in enumerate(file_location_list):
        assert file_loc[-4:] == '.pdf'
        parsed = parser.from_file(file_loc, 'http://localhost:9998/')
        with open(os.path.join(save_dir, f'{file_loc[:-4]}.txt'),
                  'w', encoding='utf-8') as txt_file:
            txt_file.write(parsed['content'])
        print(f'Completed parsing pdf file {index+1} of ' +
              f'{len(file_location_list)} - ' +
              f'({round((index+1)/len(file_location_list), 2)}%)')
    return None
