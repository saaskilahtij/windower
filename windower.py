#!/usr/bin/env python3
"""
File: windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: This tool was designed to create windows from preprocessed JSON data
"""

import sys
import argparse
import logging
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


def clean_data(data: list) -> list[Dict]:
    """
    This function removes all the 'unknown' ECU data from the data set.

    Args:
        data : List of dictionaries containing ECU information.

    Returns:
        list: A cleaned dict which contains only data of known ECUs.
    """
    cleaned_data = []
    for row in data:
        name = row.get("name")
        if name != "Unknown":
            cleaned_data.append(row)
    return cleaned_data

def parse_ecu_names(data: list) -> list:
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
            data = orjson.loads(file.read())
            logging.info("%s read successfully!", file_name)
            logging.debug("Cleaning data...")
            cleaned_data = clean_data(data)
            logging.info("Data cleaned!")
            return cleaned_data
    except FileNotFoundError:
        logging.error("Error: The file '%s' was not found.", file_name)
    except ValueError as e:
        logging.error(e)
    return None

def handle_args() -> tuple[argparse.ArgumentParser, argparse.Namespace]:
    """
    This function parses the arguments
    Returns:
        Argument parser object
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
    parser.add_argument('-json', '--output-json', type=str, help='Output file name')
    parser.add_argument('-list', '--list-ecus', action='store_true', help='List ECU names')
    parser.add_argument('-e', '--ecu', nargs='+', help='Filter data by specific ECU name(s)')
    parser.add_argument('-l', '--length', type=float, help='Window length in seconds')
    parser.add_argument('-s', '--step', type=float, default=None,
                        help='How many seconds the window moves forward '
                             '(default: same as window length)')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')

    return parser, parser.parse_args(args=None if sys.argv[1:] else ['--help'])

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

def filter_and_process_data(data: List[Dict], ecu_name: List[str] = None) -> List[Dict]:
    """
    Filter and process data based on ECU name and convert data fields to numeric values.

    Args:
        data: List of dictionaries containing the data.
        ecu_name: Filter data by specific ECU name.

    Returns:
        List of filtered and processed data entries with numeric values.
    """
    filtered_data = []

    for entry in data:
        timestamp = entry.get("timestamp")
        # Skip the row if timestamp is missing or invalid (not an int or float)
        if timestamp is None or not isinstance(timestamp, (int, float)):
            logging.debug("Row skipped. Missing or invalid timestamp")
            continue
        # If ecu_name(s) is not specified (no filter, prints everything)
        if ecu_name is None:

            raw_data = entry.get("data", "{}").strip()
            try:
                # Fix quotes and parse JSON data
                raw_data = raw_data.replace("'", "\"")
                parsed_data = orjson.loads(raw_data)
            except orjson.JSONDecodeError:
                logging.debug("Skipping malformed 'data' field in entry: %s", entry)
                continue

            # Skip entries with non-numeric values
            if any(isinstance(v, str) for v in parsed_data.values()):
                continue

            # Convert values to float
            numeric_values = {
                k: float(v) if isinstance(v, (int, float)) else v
                for k, v in parsed_data.items()
            }

            # Add entry to filtered data
            timestamp = entry.get("timestamp", 0.0)
            filtered_data.append({
                "timestamp": float(timestamp),
                **numeric_values
            })

        # If ecu_name(s) is specified, filter by that name
        elif (ecu_name is not None and entry.get("name", "").lower() in ecu_name):

            raw_data = entry.get("data", "{}").strip()
            try:
                # Fix quotes and parse JSON data
                raw_data = raw_data.replace("'", "\"")
                parsed_data = orjson.loads(raw_data)
            except orjson.JSONDecodeError:
                logging.debug("Skipping malformed 'data' field in entry: %s", entry)
                continue

            # Skip entries with non-numeric values
            if any(isinstance(v, str) for v in parsed_data.values()):
                continue

            # Convert values to float
            numeric_values = {
                k: float(v) if isinstance(v, (int, float)) else v
                for k, v in parsed_data.items()
            }

            # Add entry to filtered data
            timestamp = entry.get("timestamp", 0.0)
            filtered_data.append({
                "timestamp": float(timestamp),
                **numeric_values
            })

    return filtered_data

def create_windows(
    data: List[Dict],
    window_length: float,
    step: float = None) -> pd.DataFrame:
    """
    Creates time-based windows from sorted data and calculates statistics for each window.

    Args:
        data: List of dictionaries containing the data.
        window_length: Length of each window in seconds.
        step: How many seconds the window moves forward (default: same as window length).

    Returns:
        DataFrame containing statistics for each window.
    """
    if not data:
        logging.debug("No valid entries to process")
        return pd.DataFrame()

    # Convert to DataFrame and sort by timestamp
    df = pd.DataFrame(data)
    df = df.sort_values("timestamp")

    if step is None:
        step = window_length

    results = []
    # TODO add error handling here if no 'timestamp' // Can the rows without a timestamp be filtered out earlier?
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
            flat_stats = {f"{stat}_{key}": value
                          for key, values in stats.items()
                          for stat, value in values.items()}

            # Append results with window index and window start + window end
            results.append({
                "window_index": window_index,
                "window_start": start_time,
                "window_end": end_time,
                **flat_stats
            })

            # Increase window index for next window
            window_index += 1

        start_time += step

    return pd.DataFrame(results)

def dict_to_csv(
        data: List[Dict],
        window_length: float,
        csv_filename: str,
        step: float = None,
        ecu_name: List[str] = None):
    """
    Process JSON data, create windows, and save results to CSV.

    Args:
        data: List of dictionaries containing the data.
        window_length: Length of each window in seconds.
        csv_filename: Output CSV filename.
        step: How many seconds the window moves forward (default: same as window length).
        ecu_name: Filter data by specific ECU name.
    """
    if not data:
        logging.error("No data found from JSON")
        return

    if step is not None and step <= 0:
        logging.error("Step size must be greater than zero.")
        return

    # Filter and process the data
    filtered_data = filter_and_process_data(data, ecu_name)

    if not filtered_data:
        logging.debug("No valid entries to process after filtering")
        return

    # Create windows and calculate statistics
    results_df = create_windows(filtered_data, window_length, step)

    if results_df.empty:
        min_time = min(entry["timestamp"] for entry in filtered_data)
        max_time = max(entry["timestamp"] for entry in filtered_data)
        logging.info("No data found in window between %s and %s", min_time, max_time)
        return

    # Write CSV using Pandas
    results_df.to_csv(csv_filename, sep=";", index=False, encoding="utf-8-sig")
    logging.info("CSV file saved: %s", csv_filename)

def dict_to_json(data: dict, json_filename: str):
    """
    This function converts a 2D dictionary to JSON format using the orjson library.

    Args:
        data (dict): The 2D dictionary to convert.
        json_filename (str): The name of the output JSON file.
    """
    # Flatten the 2D dictionary into a list of dictionaries
    flattened_data = []
    for window_index, entries in data.items():
        for entry_index, entry in entries.items():
            # Add window_index and entry_index to the entry dictionary
            flattened_entry = {'window_index': window_index, 'entry_index': entry_index}
            # Update the entry dictionary with the data from the original entry
            flattened_entry.update(entry)
            # Append the flattened entry to the list
            flattened_data.append(flattened_entry)

    # Ensure filename ends with .json
    if not json_filename.endswith(".json"):
        json_filename += ".json"

    try:
        with open(json_filename, "w", encoding="utf-8") as f:
            logging.debug("Saving to %s...", json_filename)
            f.write("[\n")
            for i, row in enumerate(flattened_data):
                f.write(orjson.dumps(row, option=orjson.OPT_NON_STR_KEYS).decode("utf-8"))
                if i < len(flattened_data) - 1:
                    f.write(",\n")
                else:
                    f.write("\n]")
        logging.info("%s saved successfully", json_filename)

    except (orjson.JSONEncodeError, ValueError, TypeError) as e:
        logging.error("Error in JSON conversion: %s", e, exc_info=True)
    except Exception as e:
        logging.critical("Unexpected error: %s", e, exc_info=True)

def main():
    """
        Entrypoint
    """
    argparser, args = handle_args()
    log_setup(args.debug)

    data = read_file(args.file)
    ecu_filter = args.ecu

    if args.list_ecus:
        if data:
            ecu_names = parse_ecu_names(data)
            print(f"ECU names found in the data: {', '.join(ecu_names)}")
        return

    # If the length argument is provided, create windows
    if args.length and args.output_csv:
        dict_to_csv(data, args.length, args.output_csv, args.step, ecu_filter)
    elif args.length and args.output_json:
        # pylint: disable=fixme
        # TODO: Dump data to JSON
        pass
    else:
        argparser.print_help()
    return

if __name__ == '__main__':
    main()
