#!/usr/bin/env python3
"""
File: windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: This tool was designed to create windows from preprocessed JSON data
"""

import sys
import argparse
import logging
from collections import defaultdict
from typing import List, Dict
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

def json_to_csv(json_data: dict, csv_filename: str):
    """
    This function converts a 2D dictionary to CSV format using the pandas library.
    
    Args:
        json_data (dict): The 2D dictionary to convert.
        csv_filename (str): The name of the output CSV file.
    """
    # Flatten the 2D dictionary into a list of dictionaries for pandas
    flattened_data = []
    for window_index, entries in json_data.items():
        for entry_index, entry in entries.items():
            # Add window_index and entry_index to the entry dictionary
            flattened_entry = {'window_index': window_index, 'entry_index': entry_index}
            # Update the entry dictionary with the data from the original entry
            flattened_entry.update(entry)
            # Append the flattened entry to the list
            flattened_data.append(flattened_entry)

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(flattened_data)

    # Save the DataFrame to a CSV file
    df.to_csv(csv_filename, index=False, sep=";", encoding="utf-8-sig")
    # Logger does not work in this function, so print is used as a workaround
    print(f"Saved to {csv_filename}")
    #logging.info(f"Saved to {csv_filename}")

def parse_ecu_names(data: dict):
    """
    Extract ECU names from JSON data.

    Args:
        data : List of dictionaries containing ECU information.

    Returns:
        list: A list of ECU names found in the data.
    """
    ecu_names = set()

    for row in data:
        name = row.get("name")  # Extract name field
        if name and name != "Unknown":  # Ignore "Unknown" names
            ecu_names.add(name)

    return list(ecu_names)

def read_file(file_name: str):
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
        logging.error("Error: The file '%s' was not found.", file_name)
    except ValueError as e:
        logging.error(e)
    return None

def handle_args() -> argparse.Namespace:
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
    parser.add_argument('-json', '--output-json', action='store_true', help='Output as JSON')
    parser.add_argument('-ecu', '--ecu-names', action='store_true', help='List ECU names')
    parser.add_argument('-l', '--length', type=float, help='Window length in seconds')

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

def create_windows(data: List[Dict], window_length: int) -> Dict[int, Dict[int, Dict]]:
    """
    Creates time-based windows from sorted data based on the given window length.
    
    :param data: A list of dictionaries containing timestamped data.
    :param window_length: Length of each window in seconds.
    :return: A 2D dictionary where windows[window_index][entry_index] contains data entries.
    """
    if not data:
        return {}

    # Initialize the windows dictionary
    # defaultdict makes sure that missing keys do not raise errors
    windows = defaultdict(dict)

    # Determine the starting timestamp for the first window
    start_time = data[0]['timestamp']

    window_index = 0  # Track the current window index
    entry_index = 0  # Track the index within a window

    for entry in data:
        current_time = entry['timestamp']

        # Check if the current entry still belongs to the current window
        if current_time - start_time >= window_length:
            # Move to the next window
            start_time += window_length * ((current_time - start_time) // window_length)
            window_index += 1
            entry_index = 0

        # Assign the entry to the current window
        windows[window_index][entry_index] = entry
        entry_index += 1

    return dict(windows)

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

    # If the length argument is provided, create windows
    if args.length:
        windows = create_windows(data, args.length)
        if args.output_json:
            # pylint: disable=fixme
            # TODO: Dump data to JSON
            pass
        elif args.output_csv:
            json_to_csv(windows, args.output_csv)
        else:
            logging.error("No output format specified. Exiting.")
        return

if __name__ == '__main__':
    main()
