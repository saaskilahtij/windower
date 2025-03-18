#!/usr/bin/env python3
"""
File: windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: This tool was designed to create windows from preprocessed JSON data
"""

import csv
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

""" def json_to_csv(json_data: dict, csv_filename: str):
    
    This function converts a 2D dictionary to CSV format using the pandas library.

    Args:
        json_data (dict): The 2D dictionary to convert.
        csv_filename (str): The name of the output CSV file.
    
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
    logging.info("Saved to %s", csv_filename)
 """
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
    parser.add_argument('-e', '--ecu', type=str, help='Filter data by specific ECU name')
    parser.add_argument('-l', '--length', type=float, help='Window length in seconds')
    parser.add_argument('-s', '--step', type=float, default=None,
                    help='How many seconds the window moves forward '
                    '(default: same as window length)')
    parser.add_argument('-loglvl', '--log-level', type=lambda s: s.upper(),
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO', help='Set logging level, default: INFO')

    return parser.parse_args(args=None if sys.argv[1:] else ['--help'])

def log_setup(log_level: str):
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
    # makes new file when closing maxBytes and keeps one backup, file always logs everything in code
    file_handler = RotatingFileHandler("Windower.log", maxBytes = 1024*1024, backupCount = 1)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    file_handler.setLevel(logging.DEBUG)

    #Handler for console logging, user set level for console logging
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    #Add both handlers if logger is empty (no handlers added already)
    if not logger.hasHandlers():
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

""" def create_windows(
        data: List[Dict],
        window_length: int,
        step: int = None,
        ecu_name: str = None
    ) -> Dict[int, Dict[int, Dict]]:
    
    Creates time-based windows from sorted data based on the given window length.

    :param data: A list of dictionaries containing timestamped data.
    :param window_length: Length of each window in seconds.
    :param step: How many seconds the window moves forward (default: same as window length).
    :param ecu_name: Filter data by specific ECU name.
    :return: A 2D dictionary where windows[window_index][entry_index] contains data entries.
    
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

    return dict(windows) """

def json_to_csv(data: List[Dict],
                window_length: int,
                csv_filename: str,
                step: int = None,
                ecu_name: str = None):
    if not data:
        logging.error("No data found from JSON")
        return
    if step is None:
        step = window_length
    if step <= 0:
        logging.error("Step size must be greater than zero.")
        return

    #Filter data with given ecu name / names(?)
    filtered_data = []
    if ecu_name is not None:
        for entry in data:
            if entry.get("name","").lower() == ecu_name.lower():
                raw_data = entry.get("data", "{}").strip()
                try:
                    #Quotes fix
                    raw_data = raw_data.replace("'", "\"")
                    parsed_data = orjson.loads(raw_data)
                except orjson.JSONDecodeError:
                    logging.debug(f"Skipping malformed 'data' field in entry: {entry}")
                    continue

                #Only numeric values from data
                if any(isinstance(v, str) for v in parsed_data.values()):
                    continue

                numeric_values = {
                    k: float(v) if isinstance(v, (int, float)) else v
                    for k,v in parsed_data.items()
                }
                #Add entry to filtered data
                timestamp = entry.get("timestamp", 0.0)
                filtered_data.append({
                    "timestamp": float(timestamp),
                    **numeric_values
                })
    #If not filtered with ecu name, filter only Unknowns
    elif ecu_name is None:
        for entry in data:
            #Filter all name "Unknown"
            if entry.get("name", "").lower() != "Unknown".lower():
                raw_data = entry.get("data", "{}").strip()
                try:
                    raw_data = raw_data.replace("'", "\"") #Quotes fix
                    parsed_data = orjson.loads(raw_data)
                except orjson.JSONDecodeError:
                    logging.debug(f"Skipping malformed 'data' field in entry: {entry}")
                    continue

                #Only numeric values
                if any(isinstance(v, str) for v in parsed_data.values()):
                    continue

                numeric_values = {
                    k: float(v) if isinstance(v, (int, float)) else v
                    for k,v in parsed_data.items()
                }
                #Add entry to filtered data
                timestamp = entry.get("timestamp", 0.0)
                filtered_data.append({
                    "timestamp": float(timestamp),
                    **numeric_values
                })
    if not filtered_data:
        logging.debug("No valid entries to process")
        return

    #Process filtered data and calculate the sliding windows
    df = pd.DataFrame(filtered_data)
    df = df.sort_values("timestamp")

    results = []
    min_time = df["timestamp"].min()
    max_time = df["timestamp"].max()

    start_time = min_time
    window_index = 0
    while start_time <= max_time:
        end_time = start_time + window_length
        window_df = df[(df["timestamp"] >= start_time) & (df["timestamp"] < end_time)]

        if not window_df.empty:
            numeric_columns = window_df.select_dtypes(include=["number"]).columns
            numeric_columns = [col for col in numeric_columns if col != "timestamp"]

            stats = window_df[numeric_columns].agg(["min", "max", "mean", "std"]).to_dict()

            flat_stats = {f"{stat}_{key}": value for key, values in stats.items() for stat, value in values.items()}

            #Append results with window index and window start + window end
            results.append({
                "window_index": window_index,
                "window_start": start_time,
                "window_end": end_time,
                **flat_stats
            })

            #Increase window index for next window
            window_index += 1

        start_time += step

    results_df = pd.DataFrame(results)

    if results_df.empty:
        logging.info(f"No data found in window between {min_time} and {max_time}")
        return

    #Write CSV using Pandas
    results_df.to_csv(csv_filename, sep=";", index=False, encoding="utf-8-sig")
    logging.info("CSV file saved: %s", csv_filename)



def main():
    """
        Entrypoint
    """

    args = handle_args()
    log_setup(args.log_level)

    logging.info("Logging level set to %s", args.log_level.upper())

    data = read_file(args.file)

    if args.ecu_names:
        if data:
            ecu_names = parse_ecu_names(data)
            print(f"ECU names found in the data: {', '.join(ecu_names)}")
        return

    # If the length argument is provided, create windows
    if args.length and args.output_csv:
        json_to_csv(data,args.length, args.output_csv, args.step, args.ecu)

    elif args.length and args.output_json:
            # pylint: disable=fixme
            # TODO: Dump data to JSON
            pass
    else:
        logging.error("No output format specified. Exiting.")
    return

if __name__ == '__main__':
    main()
