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
import time
import os
import signal
import json
from datetime import datetime


DESC = r"""
     _     _     _   O             ___        __     _     _     _   ____
     \    | \    |  /|\  __    _  | ___\    /    \    \    | \    |  |   \
      \   |  \   |   |   | \   |  | ^ ^ \  / 0  0 \    \   |  \   |  |____\
       \  |   \  |   |   |  \  |  |   _ /  \   \  /     \  |   \  |  |   \
        \ |    \ |   |   |   \ |  | ___/    \ __ /       \ |    \ |  |    \
         \|     \|   |   |    \|  |___/      \__/         \|     \|  |     \
                         windows made quick and easy
"""


def clean_data(data: List[Dict]) -> List[Dict]:
    """
    This  function filters out
    entries where the name field is 'Unknown', 'unknown', or any other
    case-insensitive variation of the word 'unknown'.

    Args:
        data : List of dictionaries containing ECU information.

    Returns:
        list: A cleaned dict which contains only data of known ECUs.
    """
    cleaned_data = []
    for row in data:
        name = row.get("name")
        if not name:
            continue
        # Ensure name is a string
        name = name.lower() if isinstance(name, str) else str(name).lower()
        if "unknown" not in name:
            cleaned_data.append(row)
    return cleaned_data

def parse_ecu_names(data: List[Dict]) -> list:
    """
    clean_data function has been executed before this.
    This function is used to extract the names of ECUs from the JSON data.
    Args:
        data : List of dictionaries containing ECU information.

    Returns:
        list: A list of ECU names found in the data.
    """
    logging.debug("Extracting ECU names from JSON data")
    ecu_names = set()

    for row in data:
        name = row.get("name")  # Extract name field
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
    logging.info("Reading JSON file: %s", file_name)
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            data = orjson.loads(file.read())
            logging.debug("%s read successfully!", file_name)
            logging.debug("Cleaning data...")
            cleaned_data = clean_data(data)
            logging.debug("Data cleaned!")
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
    parser.add_argument('-list', '--list-ecus', action='store_true', help='List ECU names, can only be used with file and optional logging argument')
    parser.add_argument('-e', '--ecu', nargs='+', help='Filter data by specific ECU name(s)')
    parser.add_argument('-l', '--length', type=float, help='Window length in seconds')
    parser.add_argument('-s', '--step', type=float, default=None,
                        help='How many seconds the window moves forward '
                             '(default: same as window length)')
    parser.add_argument('-b', '--buffered', action='store_true', 
                        help='Enable buffered writing for output files')
    parser.add_argument('--buffer-size', type=int, default=1000,
                        help='Number of entries to buffer before flushing (default: 1000)')
    parser.add_argument('-w', '--watch', action='store_true',
                        help='Watch for updates to the input file and process them as they come in')
    parser.add_argument('--watch-interval', type=float, default=1.0,
                        help='Interval in seconds to check for file updates (default: 1.0)')

    #Mutually exclusive logging (only one argument can be used)
    log_level = parser.add_mutually_exclusive_group()
    log_level.add_argument('-d', '--debug', action='store_true',
                           help='Enable DEBUG logging, default: INFO logging')
    log_level.add_argument('-q', '--quiet', action= 'store_true',
                           help='Show only ERRORs, default: INFO logging')

    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])

    return parser, args

def log_setup(level: str):
    """
    Setup for logger.
    Logging levels:
    info = default, show everything above INFO level
    debug = log everything
    quiet = only print errors
    """

    logger = logging.getLogger()

    logging_levels = {
        'info': logging.INFO,
        'debug': logging.DEBUG,
        'quiet': logging.ERROR
    }

    log_level = logging_levels.get(level, logging.INFO)
    logger.setLevel(log_level)

    # Format of logs and date
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%d.%m.%Y %H:%M:%S"

    # Handler for console logging
    console_handler = logging.StreamHandler()
    
    # Custom formatter to add symbols based on log level
    class CustomFormatter(logging.Formatter):
        def format(self, record):
            # Add symbols based on log level
            if record.levelno == logging.INFO:
                record.msg = f"[*] {record.msg}"
            elif record.levelno == logging.WARNING:
                record.msg = f"[+] {record.msg}"
            elif record.levelno >= logging.ERROR:
                record.msg = f"[-] {record.msg}"
            return super().format(record)
    
    console_handler.setFormatter(CustomFormatter(log_format, datefmt=date_format))
    console_handler.setLevel(log_level)

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

        # Filter non-numeric values, keep only numeric values
        numeric_values = {
            k: float(v)
            for k, v in parsed_data.items()
            if isinstance(v,(int, float))
        }
        # Skip if nothing numeric
        if not numeric_values:
            logging.debug("Skipping entry with no numeric values: %s",
                 str(parsed_data)[:50] + "..." if len(str(parsed_data)) > 50 else str(parsed_data))
            skipped_entries += 1
            continue

        # Add numeric values to filtered data
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
    # Return empty DataFrame if no data provided
    if not data:
        logging.debug("No valid entries to process")
        return pd.DataFrame()

    # Convert list of dicts to DataFrame and sort chronologically
    try:
        df = pd.DataFrame(data)

        # Validate timestamp column exists
        if "timestamp" not in df.columns:
            logging.error("No timestamp column found in data")
            return pd.DataFrame()

        df = df.sort_values("timestamp")
    except Exception as e:
        logging.error("Error creating DataFrame: %s", e)
        return pd.DataFrame()

    # If no step size provided, use window length
    if step is None:
        step = window_length

    results = []

    # Get time range of data
    try:
        min_time = df["timestamp"].min()
        max_time = df["timestamp"].max()
    except Exception as e:
        logging.error("Error calculating time range: %s", e)
        return pd.DataFrame()

    start_time = min_time
    window_index = 0

    # Create windows by sliding over time range
    while start_time <= max_time:
        end_time = start_time + window_length
        try:
            # Get data points within current window
            window_df = df[(df["timestamp"] >= start_time) & (df["timestamp"] < end_time)]

            if not window_df.empty:
                # Get numeric columns except timestamp
                numeric_columns = window_df.select_dtypes(include=["number"]).columns
                numeric_columns = [col for col in numeric_columns if col != "timestamp"]

                # Skip window if no numeric data found
                if not numeric_columns:
                    logging.debug("No numeric columns found in window %d", window_index)
                    start_time += step
                    window_index += 1
                    continue

                # Calculate statistics for numeric columns
                stats = window_df[numeric_columns].agg(["min", "max", "mean", "std"]).to_dict()

                # Flatten stats dict into format: stat_column: value
                flat_stats = {f"{stat}_{key}": value
                              for key, values in stats.items()
                              for stat, value in values.items()}

                # Store window results with metadata
                results.append({
                    "window_index": window_index,
                    "window_start": start_time,
                    "window_end": end_time,
                    **flat_stats
                })

                window_index += 1
        except Exception as e:
            logging.error("Error processing window at %f: %s", start_time, e)

        # Move window forward by step size
        start_time += step

    # Convert results to DataFrame
    return pd.DataFrame(results)

def dict_to_csv(
        data: List[Dict],
        window_length: float,
        csv_filename: str,
        step: float = None,
        ecu_name: List[str] = None,
        buffered: bool = False,
        buffer_size: int = 1000):
    """
    Process JSON data, create windows, and save results to CSV.

    Args:
        data: List of dictionaries containing the data.
        window_length: Length of each window in seconds.
        csv_filename: Output CSV filename.
        step: How many seconds the window moves forward (default: same as window length).
        ecu_name: Filter data by specific ECU name.
        buffered: Whether to use buffered writing (default: False).
        buffer_size: Number of entries to buffer before flushing (default: 1000).
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
        logging.error("No valid entries to process after filtering")
        return

    # Create windows and calculate statistics
    results_df = create_windows(filtered_data, window_length, step)

    if results_df.empty:
        logging.error("No data found in specified windows")
        return

    try:
        if buffered:
            # Buffered writing
            logging.info("Using buffered writing with buffer size: %d", buffer_size)
            
            # Open file in write mode
            with open(csv_filename, "w", encoding="utf-8-sig") as f:
                # Write header
                header = ";".join(results_df.columns) + "\n"
                f.write(header)
                
                # Write data in chunks
                for i in range(0, len(results_df), buffer_size):
                    chunk = results_df.iloc[i:i+buffer_size]
                    chunk_str = chunk.to_csv(sep=";", index=False, header=False)
                    f.write(chunk_str)
                    f.flush()  # Flush after each chunk
                    
                    if i + buffer_size < len(results_df):
                        logging.debug("Flushed %d entries to %s", min(buffer_size, len(results_df) - i), csv_filename)
            
            logging.info("CSV file saved with buffered writing: %s", csv_filename)
        else:
            # Non-buffered writing (original behavior)
            results_df.to_csv(csv_filename, sep=";", index=False, encoding="utf-8-sig")
            logging.info("CSV file saved: %s", csv_filename)
    except Exception as e:
        logging.error("Error saving CSV file: %s", e)

def dict_to_json(
        data: List[Dict],
        json_filename: str,
        window_length: Optional[float] = None,
        step: Optional[float] = None,
        ecu_name: Optional[List[str]] = None,
        buffered: bool = False,
        buffer_size: int = 1000):
    """
    This function converts a list of dictionaries to JSON format using the orjson library.
    If window_length is provided, it will process the data by filtering, creating windows,
    and calculating statistics before converting to JSON.

    Args:
        data (List[Dict]): The list of dictionaries to convert.
        json_filename (str): The name of the output JSON file.
        window_length (Optional[float]): Length of each window in seconds. If provided, data will be processed.
        step (Optional[float]): How many seconds the window moves forward (default: same as window length).
        ecu_name (Optional[List[str]]): Filter data by specific ECU name(s).
        buffered (bool): Whether to use buffered writing (default: False).
        buffer_size (int): Number of entries to buffer before flushing (default: 1000).
    """
    if not data:
        logging.error("No data to convert to JSON")
        return

    # Process data if window_length is provided
    if window_length is not None:
        if step is not None and step <= 0:
            logging.error("Step size must be greater than zero.")
            return

        # Filter and process the data
        filtered_data = filter_and_process_data(data, ecu_name)

        if not filtered_data:
            logging.error("No valid entries to process after filtering")
            return

        # Create windows and calculate statistics
        results_df = create_windows(filtered_data, window_length, step)

        if results_df.empty:
            logging.error("No data found in specified windows")
            return

        # Convert DataFrame to list of dictionaries
        data = results_df.to_dict('records')

    # Ensure filename ends with .json
    if not json_filename.endswith(".json"):
        json_filename += ".json"

    try:
        if buffered:
            # Buffered writing
            logging.info("Using buffered writing with buffer size: %d", buffer_size)
            
            # Open file in write mode
            with open(json_filename, "w", encoding="utf-8") as f:
                # Write opening bracket
                f.write("[\n")
                
                # Write data in chunks
                for i in range(0, len(data), buffer_size):
                    chunk = data[i:i+buffer_size]
                    chunk_json = orjson.dumps(chunk, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS).decode("utf-8")
                    
                    # Remove the outer brackets from the chunk
                    chunk_json = chunk_json.strip("[]")
                    
                    # Add commas between chunks
                    if i > 0:
                        f.write(",\n")
                    
                    f.write(chunk_json)
                    f.flush()  # Flush after each chunk
                    
                    if i + buffer_size < len(data):
                        logging.debug("Flushed %d entries to %s", min(buffer_size, len(data) - i), json_filename)
                
                # Write closing bracket
                f.write("\n]")
            
            logging.info("JSON file saved with buffered writing: %s", json_filename)
        else:
            # Non-buffered writing (original behavior)
            with open(json_filename, "w", encoding="utf-8") as f:
                logging.debug("Saving to %s...", json_filename)
                f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS).decode("utf-8"))
            logging.info("%s saved successfully", json_filename)
    except (orjson.JSONEncodeError, ValueError, TypeError) as e:
        logging.error("Error in JSON conversion: %s", e)
    except Exception as e:
        logging.critical("Unexpected error: %s", e)

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

def watch_file(
        file_path: str,
        window_length: float,
        step: float,
        output_csv: Optional[str] = None,
        output_json: Optional[str] = None,
        ecu_filter: Optional[List[str]] = None,
        buffered: bool = False,
        buffer_size: int = 1000,
        watch_interval: float = 1.0):
    """
    Watch a JSON file for updates and process them as they come in.
    
    Args:
        file_path: Path to the JSON file to watch.
        window_length: Length of each window in seconds.
        step: How many seconds the window moves forward.
        output_csv: Output CSV filename (optional).
        output_json: Output JSON filename (optional).
        ecu_filter: Filter data by specific ECU name(s) (optional).
        buffered: Whether to use buffered writing (default: False).
        buffer_size: Number of entries to buffer before flushing (default: 1000).
        watch_interval: Interval in seconds to check for file updates (default: 1.0).
    """
    if not output_csv and not output_json:
        logging.error("No output format specified for watch mode")
        return
    
    # Initialize variables
    last_position = 0
    last_modified_time = 0
    last_processed_time = 0
    accumulated_data = []
    
    # Set up signal handler for graceful exit
    def signal_handler(sig, frame):
        logging.info("Stopping file watch...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logging.info("Starting to watch file: %s", file_path)
    logging.info("Press Ctrl+C to stop watching")
    
    try:
        while True:
            # Check if file exists
            if not os.path.exists(file_path):
                logging.warning("File %s does not exist, waiting...", file_path)
                time.sleep(watch_interval)
                continue
            
            # Get file modification time
            current_modified_time = os.path.getmtime(file_path)
            
            # Check if file has been modified
            if current_modified_time > last_modified_time:
                logging.debug("File has been modified, reading new data")
                
                # Read the file from the last position
                with open(file_path, "r", encoding="utf-8") as f:
                    f.seek(last_position)
                    new_data = f.read()
                    last_position = f.tell()
                
                # Parse the new data
                if new_data.strip():
                    try:
                        # Try to parse as a complete JSON array
                        new_json_data = orjson.loads(new_data)
                        if isinstance(new_json_data, list):
                            accumulated_data.extend(new_json_data)
                        else:
                            logging.warning("New data is not a JSON array, skipping")
                    except orjson.JSONDecodeError:
                        # Try to parse as a stream of JSON objects
                        try:
                            # Split by newlines and parse each line
                            lines = new_data.strip().split("\n")
                            for line in lines:
                                if line.strip():
                                    try:
                                        obj = orjson.loads(line)
                                        accumulated_data.append(obj)
                                    except orjson.JSONDecodeError:
                                        logging.warning("Invalid JSON line: %s", line[:50] + "..." if len(line) > 50 else line)
                        except Exception as e:
                            logging.error("Error parsing new data: %s", e)
                
                last_modified_time = current_modified_time
                
                # Process accumulated data if we have enough
                current_time = time.time()
                if accumulated_data and (current_time - last_processed_time) >= window_length:
                    logging.info("Processing %d accumulated entries", len(accumulated_data))
                    
                    # Filter and process the data
                    filtered_data = filter_and_process_data(accumulated_data, ecu_filter)
                    
                    if filtered_data:
                        # Create windows and calculate statistics
                        results_df = create_windows(filtered_data, window_length, step)
                        
                        if not results_df.empty:
                            # Convert DataFrame to list of dictionaries
                            results_list = results_df.to_dict('records')
                            
                            # Save to output files with timestamp
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            
                            if output_csv:
                                csv_filename = f"{output_csv}_{timestamp}.csv"
                                # Use the existing dict_to_csv function
                                dict_to_csv(filtered_data, window_length, csv_filename, step, ecu_filter, buffered, buffer_size)
                            
                            if output_json:
                                json_filename = f"{output_json}_{timestamp}.json"
                                # Use the existing dict_to_json function
                                dict_to_json(results_list, json_filename, window_length, step, ecu_filter, buffered, buffer_size)
                            
                            logging.info("Processed and saved %d entries", len(accumulated_data))
                        else:
                            logging.warning("No data found in specified windows")
                    else:
                        logging.warning("No valid entries to process after filtering")
                    
                    # Clear accumulated data
                    accumulated_data = []
                    last_processed_time = current_time
            
            # Sleep for the specified interval
            time.sleep(watch_interval)
    
    except KeyboardInterrupt:
        logging.info("Watch stopped by user")
    except Exception as e:
        logging.critical("Unexpected error in watch mode: %s", e, exc_info=True)

def main():
    """
        Entrypoint
    """
    argparser, args = handle_args()
    
    #-list/--list-ecus can only be used with file and optional logging level (only -f/--file, -list/--list-ecus and log loglevel)
    if args.list_ecus:
        other_args = any([
            args.output_csv, args.output_json,
            args.ecu, args.length, args.step
        ])
        if other_args:
            argparser.error("-list / --list-ecus can be only used with file and logging argument, no other arguments")
    
    if args.quiet:
        log_setup('quiet')
    elif args.debug:
        log_setup('debug')
    else:
        log_setup('info')

    try:
        # Check if watch mode is enabled
        if args.watch:
            # Validate arguments for watch mode
            if not args.length or not args.step:
                argparser.error("Both -l/--length and -s/--step must be provided for watch mode")
            
            if not check_output_options(args):
                # Get available output options for error message
                options = get_available_output_options()
                # Format options for display (e.g., "-csv, --output-csv, -json, --output-json")
                formatted_options = ", ".join(options)
                # Display error message
                print(f"Error: No output format specified. Please use one of the following options: {formatted_options}")
                return
            
            # Start watching the file
            ecu_filter = args.ecu
            if ecu_filter:
                ecu_filter = [name.lower() for name in ecu_filter]
                logging.debug("Filtering by ECU names: %s", ", ".join(ecu_filter))
            
            watch_file(
                args.file,
                args.length,
                args.step,
                args.output_csv,
                args.output_json,
                ecu_filter,
                args.buffered,
                args.buffer_size,
                args.watch_interval
            )
            return
        
        # Normal mode (not watching)
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
                dict_to_csv(data, args.length, args.output_csv, args.step, ecu_filter, args.buffered, args.buffer_size)
            if args.output_json:
                dict_to_json(data, args.output_json, args.length, args.step, ecu_filter, args.buffered, args.buffer_size)
        else:
            argparser.print_help()
    except Exception as e:
        logging.critical("Unexpected error in main function: %s", e, exc_info=True)

if __name__ == '__main__':
    main()
