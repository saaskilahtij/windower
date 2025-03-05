#!/usr/bin/env python3
"""
File: windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: This tool was designed to create windows from preprocessed JSON data
"""

import sys
import argparse
import logging
from logging.handlers import RotatingFileHandler
import pandas as pd
import orjson


DESC = r"""
     _     _     _   O             ___        __     _     _     _   ____
     \    | \    |  /|\  __    _  | ___\    /    \    \    | \    |  |   \
      \   |  \   |   |   | \   |  | ^ ^ \  / 0  0 \    \   |  \   |  |____\
       \  |   \  |   |   |  \  |  |   _ /  \   \  /     \  |   \  |  |   \
        \ |    \ |   |   |   \ |  | ___/    \ __ /       \ |    \ |  |    \
         \|     \|   |   |    \|  |___/      \__/         \|     \|  |     \
                         windows made quick and easy
"""

def json_to_csv(json_data, csv_filename):
    """
    This function converts json to csv format with pandas library
    """
    df = pd.DataFrame(json_data)
    df.to_csv(csv_filename, index=False, sep=";", encoding="utf-8-sig")
    logging.info(f"Saved to {csv_filename}")

def parse_ecu_names(data):
    """
    Extract ECU names from JSON data.

    Args:
        data : List of dictionaries containing ECU information.

    Returns:
        list: A list of ECU names found in the data.
    """
    ecu_names = set()

    for row in data:
        # This hardcoded "name" field might run in to problems if JSON schema changes
        # Let's ask about this
        name = row.get("name")  # Extract name field
        if name and name != "Unknown":  # Ignore "Unknown" names
            ecu_names.add(name)

    return list(ecu_names)

def read_file(file_name):
    """ 
    This function reads a JSON file and converts it into a Python object using orjson.
    Args:
        file_name (str): Path to the JSON file.
    Returns:
        dict or list: Parsed JSON data as a Python object.
    Note:
        - The file must be a valid JSON.
        - orjson is used instead of the built-in json module due to its 
          performance benefits, especially for large files.
    """
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            return orjson.loads(file.read())
    except FileNotFoundError:
        logging.error(f"Error: The file '{file_name}' was not found.")
    except ValueError as e:
        logging.error(e)
    return None

def handle_args():
    """
    This function parses the arguments
    Returns:
        Parsed args
    Note:
        The return can seem a bit funny. However, it makes sure that
        if the tool is ran without args, it will print the help message.
        This is because argparse does not support this out of the box.
    """
    parser = argparse.ArgumentParser(description=DESC, prog='windower.py',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-f', '--file', type=str, help='Path to the JSON file',
                        required=True)
    parser.add_argument('-csv', '--output-csv', type=str, help='Output file name')
    parser.add_argument('-ecu', '--ecu-names', action='store_true', help='List ECU names')
    parser.add_argument('-l', '--length', type=int, help='Window length in seconds')

    return parser.parse_args(args=None if sys.argv[1:] else ['--help'])

def log_setup():
    """
    Setup for logger. Handlers for both file and console logging. 
    
    File logging uses rotation so file won't get too big and it keeps one backup.
    
    Console logging for real-time feedback (if needed)
    
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    #Format of logs and date
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%d.%m.%Y %H:%M:%S"

    #Create handler for file logging with rotation,
    # makes new file when closing maxBytes and keeps one backup, set level of messages to log
    file_handler = RotatingFileHandler("Windower.log", maxBytes = 1024*1024, backupCount = 1)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    file_handler.setLevel(logging.DEBUG)

    #Handler for console logging, set level of messages to log
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    console_handler.setLevel(logging.ERROR)

    #Add both handlers if logger is empty (no handlers added already)
    if not logger.hasHandlers():
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

def main():
    """
        Entrypoint
    """
    log_setup()
    args = handle_args()
    data = read_file(args.file)

    if args.ecu_names:
        if data:
            ecu_names = parse_ecu_names(data)
            print(f"ECU names found in the data: {', '.join(ecu_names)}")
        return

    windows = []
    num_list = [0,1,2,3,4,5,6,7,8,9]

    # Täytyy jotenkin selvittää montako numeroa loppuun jää, josta ei saada ikkunaa    
    start_index = 0
    length = 3
    end_index = length - 1
    window_count = 0
    while end_index <= len(num_list):
        windows.append([])
        # Luo ehto jos:
        # if rest_of_the_elements % window_length != 0
        while start_index <= end_index:
            windows[window_count].append(num_list[start_index])
            start_index += 1
        end_index += length
        window_count += 1 
    print(windows)
    

    """if args.output_csv and args.length:
        if data:
            windows = create_windows(data, 9)
            json_to_csv(windows, args.output_csv)
        return
    else: 
        logging.error("Please provide both output file name and window length")
        return"""

if __name__ == '__main__':
    main()
