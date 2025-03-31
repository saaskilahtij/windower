#!/usr/bin/env python3
"""
File: windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: This tool was designed to create windows from preprocessed JSON data
"""

import sys
import argparse
import logging
from typing import List, Dict, Optional, Union, Any
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

def read_file(file_name: str) -> Optional[List[Dict]]:
    """
    This function reads a JSON file and converts it into a Python object using orjson.
    Args:
        file_name (str): Path to the JSON file.
    Returns:
        Optional[List[Dict]]: Parsed JSON data as a Python object or None if an error occurs.
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
    except orjson.JSONDecodeError as e:
        logging.error("Error: Invalid JSON in file '%s': %s", file_name, e)
    except Exception as e:
        logging.error("Unexpected error reading file '%s': %s", file_name, e)
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

def safe_parse_json(raw_data: str) -> Optional[Dict]:
    """
    Safely parse JSON data with error handling.
    
    Args:
        raw_data (str): Raw JSON string to parse.
        
    Returns:
        Optional[Dict]: Parsed JSON data as a dictionary or None if parsing fails.
    """
    if not raw_data or not isinstance(raw_data, str):
        return None
    
    # Try to clean up the data before parsing
    cleaned_data = raw_data.strip()
    
    try:
        # Handle both JSON formats: with single quotes and with double quotes
        if cleaned_data.startswith("'") or cleaned_data.startswith("{"):
            # Replace single quotes with double quotes for JSON parsing
            cleaned_data = cleaned_data.replace("'", "\"")
        
        # Try to parse the cleaned data
        return orjson.loads(cleaned_data)
    except orjson.JSONDecodeError:
        logging.debug("Failed to parse JSON data: %s", raw_data[:50] + "..." if len(raw_data) > 50 else raw_data)
        return None
    except Exception as e:
        logging.debug("Unexpected error parsing JSON data: %s", e)
        return None

def is_valid_timestamp(timestamp: Any) -> bool:
    """
    Check if a timestamp is valid.
    
    Args:
        timestamp: The timestamp value to check.
        
    Returns:
        bool: True if the timestamp is valid, False otherwise.
    """
    if timestamp is None:
        return False
    
    if not isinstance(timestamp, (int, float)):
        return False
    
    # Check if timestamp is within a reasonable range
    # Unix timestamp should be positive and not too far in the future
    if timestamp <= 0 or timestamp > 9999999999:  # Approx year 2286
        return False
    
    return True

def filter_and_process_data(data: List[Dict], ecu_name: List[str] = None) -> List[Dict]:
    """
    Filter and process data based on ECU name and convert data fields to numeric values.
    Handles errors gracefully and skips invalid entries.

    Args:
        data: List of dictionaries containing the data.
        ecu_name: Filter data by specific ECU name(s).

    Returns:
        List of filtered and processed data entries with numeric values.
    """
    filtered_data = []
    total_entries = len(data)
    skipped_entries = 0
    
    # Convert ecu_name to lowercase for case-insensitive matching if provided
    ecu_filters = [name.lower() for name in ecu_name] if ecu_name else None

    for entry in data:
        # Skip entries with invalid timestamp
        timestamp = entry.get("timestamp")
        if not is_valid_timestamp(timestamp):
            logging.debug("Skipping entry with invalid timestamp: %s", 
                         str(entry)[:50] + "..." if len(str(entry)) > 50 else str(entry))
            skipped_entries += 1
            continue
        
        # Skip entries that don't match the ECU filter (if provided)
        if ecu_filters and entry.get("name", "").lower() not in ecu_filters:
            continue

        # Process data field
        raw_data = entry.get("data")
        if not raw_data:
            logging.debug("Skipping entry with empty data field")
            skipped_entries += 1
            continue

        # Parse the data field
        parsed_data = safe_parse_json(raw_data)
        if not parsed_data:
            logging.debug("Skipping entry with invalid data format: %s", 
                         raw_data[:50] + "..." if len(raw_data) > 50 else raw_data)
            skipped_entries += 1
            continue

        # Skip entries with non-numeric values
        if any(not isinstance(v, (int, float)) for v in parsed_data.values()):
            logging.debug("Skipping entry with non-numeric values: %s", 
                         str(parsed_data)[:50] + "..." if len(str(parsed_data)) > 50 else str(parsed_data))
            skipped_entries += 1
            continue

        # Convert values to float
        try:
            numeric_values = {
                k: float(v) if isinstance(v, (int, float)) else 0.0
                for k, v in parsed_data.items()
            }

            # Add entry to filtered data
            filtered_data.append({
                "timestamp": float(timestamp),
                **numeric_values
            })
        except (ValueError, TypeError) as e:
            logging.debug("Error converting values to numeric: %s", e)
            skipped_entries += 1
            continue

    if skipped_entries > 0:
        logging.info("Skipped %d out of %d entries due to invalid data", 
                     skipped_entries, total_entries)

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
    try:
        df = pd.DataFrame(data)
        
        # Ensure timestamp column exists
        if "timestamp" not in df.columns:
            logging.error("No timestamp column found in data")
            return pd.DataFrame()
            
        df = df.sort_values("timestamp")
    except Exception as e:
        logging.error("Error creating DataFrame: %s", e)
        return pd.DataFrame()

    if step is None:
        step = window_length

    results = []
    try:
        min_time = df["timestamp"].min()
        max_time = df["timestamp"].max()
    except Exception as e:
        logging.error("Error calculating time range: %s", e)
        return pd.DataFrame()

    start_time = min_time
    window_index = 0

    while start_time <= max_time:
        end_time = start_time + window_length
        try:
            window_df = df[(df["timestamp"] >= start_time) & (df["timestamp"] < end_time)]

            if not window_df.empty:
                numeric_columns = window_df.select_dtypes(include=["number"]).columns
                numeric_columns = [col for col in numeric_columns if col != "timestamp"]

                if not numeric_columns:
                    logging.debug("No numeric columns found in window %d", window_index)
                    start_time += step
                    window_index += 1
                    continue

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
        except Exception as e:
            logging.error("Error processing window at %f: %s", start_time, e)
            
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
        logging.info("No data found in specified windows")
        return

    # Ensure output filename has .csv extension
    if not csv_filename.endswith(".csv"):
        csv_filename += ".csv"

    try:
        # Write CSV using Pandas
        results_df.to_csv(csv_filename, sep=";", index=False, encoding="utf-8-sig")
        logging.info("CSV file saved: %s", csv_filename)
    except Exception as e:
        logging.error("Error saving CSV file: %s", e)

def dict_to_json(data: List[Dict], json_filename: str):
    """
    This function converts a list of dictionaries to JSON format using the orjson library.

    Args:
        data (List[Dict]): The list of dictionaries to convert.
        json_filename (str): The name of the output JSON file.
    """
    if not data:
        logging.error("No data to convert to JSON")
        return
        
    # Ensure filename ends with .json
    if not json_filename.endswith(".json"):
        json_filename += ".json"

    try:
        with open(json_filename, "w", encoding="utf-8") as f:
            logging.debug("Saving to %s...", json_filename)
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS).decode("utf-8"))
        logging.info("%s saved successfully", json_filename)
    except (orjson.JSONEncodeError, ValueError, TypeError) as e:
        logging.error("Error in JSON conversion: %s", e)
    except Exception as e:
        logging.critical("Unexpected error: %s", e)

def process_json_data(
        data: List[Dict],
        window_length: float,
        json_filename: str,
        step: float = None,
        ecu_name: List[str] = None):
    """
    Process JSON data, create windows, and save results to JSON.

    Args:
        data: List of dictionaries containing the data.
        window_length: Length of each window in seconds.
        json_filename: Output JSON filename.
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
        logging.info("No data found in specified windows")
        return

    # Convert DataFrame to list of dictionaries
    results_list = results_df.to_dict('records')
    
    # Save to JSON
    dict_to_json(results_list, json_filename)

def get_available_output_options() -> List[str]:
    """
    Returns a list of available output options.
    This function is used to provide a list of available output options
    in error messages. Add new output options here when they are implemented.
    
    Returns:
        List[str]: List of available output option flags.
    """
    # Add new output options here as they are implemented
    return ["-csv", "--output-csv", "-json", "--output-json"]

def check_output_options(args: argparse.Namespace) -> bool:
    """
    Checks if any output option is specified in the arguments.
    
    Args:
        args: Parsed command line arguments.
        
    Returns:
        bool: True if any output option is specified, False otherwise.
    """
    # Check if any output option is specified
    # Add new output options here as they are implemented
    return bool(args.output_csv or args.output_json)

def main():
    """
        Entrypoint
    """
    argparser, args = handle_args()
    log_setup(args.debug)

    try:
        data = read_file(args.file)
        if data is None:
            logging.error("Failed to read or parse the input file.")
            return
            
        ecu_filter = args.ecu
        if ecu_filter:
            ecu_filter = [name.lower() for name in ecu_filter]
            logging.debug("Filtering by ECU names: %s", ", ".join(ecu_filter))

        if args.list_ecus:
            if data:
                ecu_names = parse_ecu_names(data)
                if ecu_names:
                    print(f"ECU names found in the data: {', '.join(ecu_names)}")
                else:
                    print("No ECU names found in the data.")
            return

        # If the length argument is provided, check if output options are specified
        if args.length:
            if not check_output_options(args):
                # Get available output options for error message
                options = get_available_output_options()
                # Format options for display (e.g., "-csv, --output-csv, -json, --output-json")
                formatted_options = ", ".join(options)
                # Display error message
                print(f"Error: No output format specified. Please use one of the following options: {formatted_options}")
                return
                
            if args.output_csv:
                dict_to_csv(data, args.length, args.output_csv, args.step, ecu_filter)
            elif args.output_json:
                process_json_data(data, args.length, args.output_json, args.step, ecu_filter)
        else:
            argparser.print_help()
    except Exception as e:
        logging.critical("Unexpected error in main function: %s", e, exc_info=True)

if __name__ == '__main__':
    main()
