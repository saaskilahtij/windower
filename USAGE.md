# Windower - Usage Guide

## Overview

Windower is a tool designed to create time-based windows from preprocessed JSON data containing ECU (Electronic Control Unit) information. It processes raw data by:

1. Filtering by ECU name (optional)
2. Creating time-based windows of specified length
3. Calculating statistics for each window (min, max, mean, standard deviation)
4. Outputting results in CSV or JSON format

## Installation

### Prerequisites

- Python 3.6+
- Required packages:
  - pandas
  - orjson

### Dependencies Installation

```bash
pip install -r requirements.txt
```

## Command-Line Arguments

```
     _     _     _   O             ___        __     _     _     _   ____
     \    | \    |  /|\  __    _  | ___\    /    \    \    | \    |  |   \
      \   |  \   |   |   | \   |  | ^ ^ \  / 0  0 \    \   |  \   |  |____\
       \  |   \  |   |   |  \  |  |   _ /  \   \  /     \  |   \  |  |   \
        \ |    \ |   |   |   \ |  | ___/    \ __ /       \ |    \ |  |    \
         \|     \|   |   |    \|  |___/      \__/         \|     \|  |     \
                         windows made quick and easy
```

### Required Arguments

- `-f, --file` - Path to the input JSON file containing ECU data

### Output Options

- `-csv, --output-csv` - Path to save the output CSV file
- `-json, --output-json` - Path to save the output JSON file

### Window Parameters

- `-l, --length` - Window length in seconds (required for processing)
- `-s, --step` - How many seconds the window moves forward (default: same as window length)

### Filtering

- `-e, --ecu` - Filter data by specific ECU name(s). Can provide multiple names.

### Utility Options

- `-list, --list-ecus` - List all ECU names found in the data file (can only be used with file and logging arguments)

### Logging Options

- `-d, --debug` - Enable detailed DEBUG logging
- `-q, --quiet` - Show only ERROR level messages

## Basic Usage

### List Available ECUs

To view all ECU names in the data file:

```bash
python windower.py -f data.json --list-ecus
```

### Process Data with Default Settings

Process data with 1-second windows and save as CSV:

```bash
python windower.py -f data.json -l 1 -csv output.csv
```

### Customize Window Size and Step

Create 5-second windows with 2-second steps:

```bash
python windower.py -f data.json -l 5 -s 2 -csv output.csv
```

### Filter by ECU

Process only data from specific ECUs:

```bash
python windower.py -f data.json -l 1 -e BRAKE ENGINE -csv output.csv
```

### Multiple Output Formats

Generate both CSV and JSON outputs:

```bash
python windower.py -f data.json -l 1 -csv output.csv -json output.json
```

## Data Processing Details

### Input Data Format

The tool expects a JSON file containing an array of objects with the following structure:

```json
[
  {
    "name": "BRAKE",
    "timestamp": 1717678137.6661446,
    "id": 166,
    "data": "{\"BRAKE_AMOUNT\": 39, \"BRAKE_PEDAL\": 18}",
    "raw": "0x2700125000000037"
  },
  ...
]
```

Notes:
- The `name` field identifies the ECU
- The `timestamp` field must be a valid timestamp
- The `data` field must be parseable as JSON and contain numeric values

### Output Format

#### CSV Output

The CSV output file contains the following columns:
- `window_index` - Sequential index of the window
- `window_start` - Start timestamp of the window
- `window_end` - End timestamp of the window
- Statistics columns for each numeric value:
  - `min_<value>` - Minimum value within the window
  - `max_<value>` - Maximum value within the window
  - `mean_<value>` - Mean value within the window
  - `std_<value>` - Standard deviation within the window

#### JSON Output

The JSON output has the same structure as the CSV output, formatted as an array of objects.

## Error Handling

Windower includes extensive error handling:
- Invalid JSON files will be reported
- Missing files will be detected
- Invalid timestamps are filtered out
- Empty data or windows will be reported
- Invalid command-line arguments will display helpful error messages

## Examples with Expected Output

### Example 1: List ECUs in data file

```bash
python windower.py -f can_dump.json --list-ecus
```

Output:
```
ECU names found in the data: BRAKE, ENGINE, TRANSMISSION, SPEED
```

### Example 2: Create 2-second windows with 1-second step

```bash
python windower.py -f can_dump.json -l 2 -s 1 -csv output.csv
```

Output:
```
2023-06-12 14:30:45 - INFO - Reading JSON file: can_dump.json
2023-06-12 14:30:46 - INFO - CSV file saved: output.csv
```

The CSV file will contain statistics for each window, with columns like `window_index`, `window_start`, `window_end`, `min_BRAKE_AMOUNT`, `max_BRAKE_AMOUNT`, `mean_BRAKE_AMOUNT`, `std_BRAKE_AMOUNT`.
