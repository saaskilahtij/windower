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
# pylint: disable=unused-argument
def json_to_csv(json_data: dict, csv_filename: str):
    """
    This function converts a 2D dictionary to CSV format using the pandas library.

    Args:
        json_data (dict): The 2D dictionary to convert.
        csv_filename (str): The name of the output CSV file.
    """

    # Houston, we have a problem here
    # CSV is being dumped 2D style
    # This is not the way to do it
    flattened_data = []
    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(flattened_data)

    # Save the DataFrame to a CSV file
    df.to_csv(csv_filename, index=False, sep=";", encoding="utf-8-sig")

def parse_ecu_names(data: dict):
    """
    Extract ECU names from JSON data.
    Args:
        data : List of dictionaries containing ECU information.

    Returns:
        list: A list of ECU names found in the data.
    """
    logging.debug("Extracting ECU names from JSON data")
    ecu_names = set()

    for row in data:
        name = row.get("name")  # Extract name field
        if name and name != "Unknown":  # Ignore "Unknown" names
            ecu_names.add(name)

    logging.debug("ECU names extracted")
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
    logging.debug("Reading JSON file: %s", file_name)
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
    parser.add_argument('-e', '--ecu', type=str, help='Filter data by specific ECU name')
    parser.add_argument('-l', '--length', type=float, help='Window length in seconds')
    parser.add_argument('-s', '--step', type=float, default=None,
                        help='How many seconds the window moves forward '
                             '(default: same as window length)')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')

    return parser.parse_args(args=None if sys.argv[1:] else ['--help'])

def log_setup(debug: bool):
    """
    Setup for logger. Logs errors to stderr by default, and everything if debug is enabled.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.ERROR)

    # Format of logs and date
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%d.%m.%Y %H:%M:%S"

    # Handler for console logging
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    console_handler.setLevel(logging.DEBUG if debug else logging.ERROR)

    # Add the handler if logger is empty (no handlers added already)
    if not logger.hasHandlers():
        logger.addHandler(console_handler)

def create_windows(
        data: List[Dict],
        window_length: int,
        step: int = None,
        ecu_name: str = None
    ) -> Dict[int, Dict[int, Dict]]:
    """
    Creates time-based windows from sorted data based on the given window length.

    :param data: A list of dictionaries containing timestamped data.
    :param window_length: Length of each window in seconds.
    :param step: How many seconds the window moves forward (default: same as window length).
    :param ecu_name: Filter data by specific ECU name.
    :return: A 2D dictionary where windows[window_index][entry_index] contains data entries.
    """
    if not data:
        return {}

    # Initialize the windows dictionary
    # defaultdict makes sure that missing keys do not raise errors
    windows = defaultdict(dict)

    # Determine the starting and ending timestamps
    min_time = data[0]['timestamp']
    max_time = data[-1]['timestamp']

    if step is None:
        step = window_length

    if step <= 0:
        logging.error("Step size must be greater than zero.")
        return {}

    window_index = 0  # Track the current window index
    entry_index = 0  # Track the index within a window
    start_time = min_time # Set the start time to the minimum timestamp
    data_index = 0 # Marks the start of each new window, avoiding revisiting data from the start.

    logging.debug(
        "Creating windows with length %f seconds and step %f seconds",
        window_length,
        step
    )

    while start_time <= max_time:
        # Reset entry index for each window
        entry_index = 0

        # Move data_index to the start of the current window
        while data_index < len(data) and data[data_index]['timestamp'] < start_time:
            data_index += 1

        # Iterate only through entries belonging to the current window
        i = data_index
        while i < len(data) and data[i]['timestamp'] < (start_time + window_length):
            entry = data[i]

            # If filtering by ECU name, skip other ECUs
            if ecu_name and entry.get("name", "").lower() != ecu_name.lower():
                i += 1
                continue

            # Assign the entry to the current window
            windows[window_index][entry_index] = entry
            entry_index += 1
            i += 1

        # Move to the next window by step size
        start_time += step
        window_index += 1

    logging.debug("Windows created")
    return dict(windows)

def main():
    """
        Entrypoint
    """
    args = handle_args()
    log_setup(args.debug)

    data = read_file(args.file)

    if args.ecu_names:
        if data:
            ecu_names = parse_ecu_names(data)
            print(f"ECU names found in the data: {', '.join(ecu_names)}")
        return

    # If the length argument is provided, create windows
    if args.length:
        windows = create_windows(data, args.length, args.step, args.ecu)
        if not windows:
            logging.error("No windows created. Exiting.")
            return
        if args.output_json:
            # pylint: disable=fixme
            # TODO: Dump data to JSON
            pass
        elif args.output_csv:
            json_to_csv(windows, args.output_csv)
            logging.debug("Windows saved to CSV file: %s", args.output_csv)
        else:
            logging.error("No output format specified. Exiting.")
        return

if __name__ == '__main__':
    main()
