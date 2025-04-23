# Windower - Usage Guide

## Overview

Windower is a tool designed to create time-based windows from preprocessed JSON data containing ECU (Electronic Control Unit) information. It processes raw data by:

1. Filtering by ECU name (optional)
2. Creating time-based windows of specified length
3. Calculating statistics for each window (min, max, mean, standard deviation)
4. Outputting results in CSV or JSON format

It comes along with unit testing and benchmarking utilities `test_windower.py` (unit tests), `perftester_windower.py` (benchmarking), and `visualize_benchmarks.py` (visualizing benchmarks).

## Dependency Installation

```bash
pip install -r requirements.txt
```

Or if needing to run or develop tests and benchmarks:
```bash
pip install -r dev-requirements.txt
```

## Command-Line Arguments

Can be invoked by running `python3 windower.py -h`.

```
     _     _     _   O             ___        __     _     _     _   ____
     \    | \    |  /|\  __    _  | ___\    /    \    \    | \    |  |   \
      \   |  \   |   |   | \   |  | ^ ^ \  / 0  0 \    \   |  \   |  |____\
       \  |   \  |   |   |  \  |  |   _ /  \   \  /     \  |   \  |  |   \
        \ |    \ |   |   |   \ |  | ___/    \ __ /       \ |    \ |  |    \
         \|     \|   |   |    \|  |___/      \__/         \|     \|  |     \
                         windows made quick and easy
```

### Examples

To view all ECU names in the data file:
```bash
python windower.py -f data.json --list-ecus
```

Process data with 1-second window, default 1-second step, and save as CSV:
```bash
python windower.py -f data.json -l 1 -csv output.csv
```

Create 5-second windows with 2-second steps:

```bash
python windower.py -f data.json -l 5 -s 2 -csv output.csv
```

Process only data from specific ECUs:

```bash
python windower.py -f data.json -l 1 -e BRAKE GAS_PEDAL -csv output.csv
```

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

If the schema changes, the tool will break.

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

# Pytest - Usage Guide

Pytest is easy to use. Just run: `pytest`.

# Performance Testing Tools - Usage Guide

## Overview

The Windower performance testing tool is designed to measure and analyze the performance characteristics (execution time and memory usage) of the `filter_and_process_data` and `create_windows` functions across different data sizes and configurations. 

The performance testing tool consists of two main scripts:
1. **perftester_windower.py**: Measures execution time and memory usage of windower functions
2. **visualize_benchmarks.py**: Creates visualizations and tables from benchmark results

Key metrics to produce:
- **Time Stats**: Execution time in seconds (min, max, mean, median)
- **Memory Stats**: Memory usage in MB (mean, max, peak)
- **Windows Generated**: Number of windows created from the data

## Command-Line Arguments perftester_windower.py

Can be invoked by running:
```bash
python3 perftester_windower.py -h
or
python3 visualize_benchmarks.py -h
```

### Examples
Benchmark sets of 1000, 10000, and 1000000 with three iterations, creating windows lengths of 1 second, and save the output to results.json:
```bash
python3 perftester_windower.py -s 1000 10000 100000 -i 3 -w 1.0 -o results.json
```

Similar, but with 10000 entries, five iterations and tweaked window and step lengths while saving the output to custom_results.json:
```bash
python3 perftester_windower.py -s 10000 -i 5 -w 2.0 -t 0.5 -o custom_results.json
```

If you then wish to visualize the results in results.json case:
```bash
python3 visualize_benchmarks.py -f results.json
```

To save the output images to a custom folder:
```bash
python3 visualize_benchmarks.py -f results.json -o my_visualization_folder
```

## Output

`perftester_windower-py` produces text output, and it can save JSON output if specified with `-o` flag.

`visualize_benchmarks.py` produces three visualization files:
1. `time_comparison.png`: Bar chart comparing execution times
The time comparison chart shows execution time (in seconds, milliseconds, or microseconds) for each function across different data sizes. Vertical labels on each bar show the exact time values.
2. `memory_comparison.png`: Bar chart comparing memory usage
The memory chart shows memory usage (in MB) for each function across different data sizes. Vertical labels on each bar show the exact memory values.
3. `scaling.png`: Log-log plot showing scaling behavior
The scaling plot uses logarithmic scales on both axes to reveal how execution time and memory usage scale with data size. This helps identify if performance follows expected complexity (e.g., O(n), O(n log n), O(n²))
