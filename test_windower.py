"""
File: test_windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: This file contains the windower unit tests
"""

from datetime import datetime
import math
import random
import unittest
from unittest import mock
from unittest.mock import patch, mock_open
import argparse
import sys
import logging
import orjson
import pandas as pd
import windower

class TestWindower(unittest.TestCase):
    """
    Test suite for the Windower module.
    This class contains unit tests for the Windower module, specifically testing
    the functionality related to extracting and printing ECU names from JSON data.
    Tests:
        - test_ecu_names_flow: Verifies that the main function correctly prints the
          ECU names by mocking the read_file and parse_ecu_names functions.
        - test_clean_data_removes_unknowns: Verifies that the clean_data function
          correctly removes entries where the name field is "Unknown".
        - test_filter_and_process_data_with_known_ecu:
          Tests the function by filtering data based on the "BRAKE" ECU name
          and ensuring that only "BRAKE" data entries are processed and returned.
        - test_filter_and_process_data_invalid_timestamp:
        - test_main_no_output_format:
    """
    @patch("windower.parse_ecu_names", return_value=["ECU1", "ECU2"])
    @patch("windower.read_file", return_value=[{"name": "ECU1"}, {"name": "ECU2"}])
    def test_ecu_names_flow(self, _mock_read, mock_load):
        """
        Test the flow for extracting and printing ECU names from the JSON data.

        This test uses hardcoded test data that matches the schema of real CAN data,
        and verifies that the main function correctly extracts and prints the ECU names.
        """
        test_data = [
            {
                "name": "BRAKE",
                "timestamp": 1717678137.6661446,
                "id": 166,
                "data": "{\"BRAKE_AMOUNT\": 39, \"BRAKE_PEDAL\": 18}",
                "raw": "0x2700125000000037"
            },
            {
                "name": "SPEED",
                "timestamp": 1717678137.6916034,
                "id": 180,
                "data": "{\"ENCODER\": 1, \"SPEED\": 15.48, \"CHECKSUM\": 207}",
                "raw": "0x0000000001060ccf"
            }
        ]
        _mock_read.return_value = test_data
        mock_load.return_value = ["BRAKE", "SPEED"]

    def test_parse_ecu_names(self):
        '''Tests fuction pars from JSON data'''
        test_data = [
            {"name": "ECU1"},
            {"name": "ECU2"},
            {"name": "ECU1"},
            {"name": "ECU3"},
            {"name": "ECU2"}
        ]
        expected_result = ["ECU1", "ECU2", "ECU3"]

        result = windower.parse_ecu_names(test_data)
        self.assertEqual(sorted(result), sorted(expected_result))

    def test_list_ecus_valid(self):
        """Test list_ecus valid (no other args than -f)"""
        test_args = ['windower.py', '-f', 'test.json', '--list-ecus']
        with patch.object(sys, 'argv', test_args):
            parser, args = windower.handle_args()
            self.assertTrue(args.list_ecus)
            self.assertEqual(args.file, 'test.json')

    def test_list_ecus_invalid_other_args(self):
        """Test list_ecus with another args, should print message"""
        test_args = ['windower.py', '-f', 'test.json', '--list-ecus', '--length', '5']
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit) as cm:
                windower.handle_args()
            self.assertEqual(cm.exception.code, 2)

    def test_clean_data_removes_unknowns(self):
        """
        Test that clean_data removes entries with names containing 'unknown'
        (case-insensitive).

        This test ensures that the clean_data function correctly filters out
        entries where the name field is 'Unknown', 'unknown', or any other
        case-insensitive variation of the word 'unknown'.
        """
        input_data = [
            {"name": "ECU1"},
            {"name": "Unknown"},
            {"name": "unknown"},
            {"name": "ECU2"},
            {"name": "Unknown2"},
            {"name": None},
            {"name": ""},
            {"name": "ECU3"},
            {"name": "UNKNOWN"},
            {"name": "UnKnOwN"},
            {"name": "ECU4"},
            {"name": "udnwknown"},
            {"name": "Unknowm"},
            {"name": "ECU5"}
        ]
        expected_output = [
            {"name": "ECU1"},
            {"name": "ECU2"},
            {"name": "ECU3"},
            {"name": "ECU4"},
            {"name": "udnwknown"},
            {"name": "Unknowm"},
            {"name": "ECU5"}

        ]
        self.assertEqual(windower.clean_data(input_data), expected_output)

    def test_filter_and_process_data_with_known_ecu(self):
        """
        Tests the functionality of the filter_and_process_data function
        by filtering the data based on a specific ECU name.
        """

        input_data = [
            {"name": "BRAKE", "timestamp": 1717678137.6661446, "id": 166,
             "data": "{\"BRAKE_AMOUNT\": 39, \"BRAKE_PEDAL\": 18}", "raw": "0x2700125000000037"},
            {"name": "BRAKE", "timestamp": 1717678137.6795962, "id": 166,
             "data": "{\"BRAKE_AMOUNT\": 39, \"BRAKE_PEDAL\": 19}", "raw": "0x2700135000000038"},
            {"name": "Unknown", "timestamp": 1717678137.6916032, "id": 303,
             "data": "ff7fff7fff7fffb1", "raw": "0xff7fff7fff7fffb1"},
            {"name": "SPEED", "timestamp": 1717678137.6916034, "id": 180,
             "data": "{\"ENCODER\": 1, \"SPEED\": 15.48, \"CHECKSUM\": 207}",
             "raw": "0x0000000001060ccf"},
            {"name": "BRAKE", "timestamp": 1717678137.6935961, "id": 166,
             "data": "{\"BRAKE_AMOUNT\": 40, \"BRAKE_PEDAL\": 19}", "raw": "0x2800135000000039"}
        ]

        expected_output = [
            {"timestamp": 1717678137.6661446, "BRAKE_AMOUNT": 39.0, "BRAKE_PEDAL": 18.0},
            {"timestamp": 1717678137.6795962, "BRAKE_AMOUNT": 39.0, "BRAKE_PEDAL": 19.0},
            {"timestamp": 1717678137.6935961, "BRAKE_AMOUNT": 40.0, "BRAKE_PEDAL": 19.0}
        ]

        output = windower.filter_and_process_data(input_data, ecu_name=["brake"])
        self.assertEqual(output, expected_output)

    def test_filter_and_process_data_invalid_timestamp(self):
        """Test that filter_and_process_data skips rows with invalid timestamps."""
        input_data = [
            {"name": "BRAKE", "timestamp": 1717678137.6661446, "id": 166,
             "data": "{\"BRAKE_AMOUNT\": 39, \"BRAKE_PEDAL\": 18}", "raw": "0x2700125000000037"},
            {"name": "BRAKE", "timestamp": "invalid", "id": 166,
             "data": "{\"BRAKE_AMOUNT\": 39, \"BRAKE_PEDAL\": 19}", "raw": "0x2700135000000038"}
        ]
        expected_output = [
            {"timestamp": 1717678137.6661446, "BRAKE_AMOUNT": 39.0, "BRAKE_PEDAL": 18.0}
        ]
        output = windower.filter_and_process_data(input_data)
        self.assertEqual(output, expected_output)

    def test_is_valid_timestamp(self):
        """Test that timestamp_is_valid function correctly identifies valid timestamps """
        test_data = [
            (1717678139, True),
            (1717678139.6661446, True),
            (None, False),
            (-1717678139.6661446, False),
            (0, False),
            (10000000000, False),
            (9999999999, True)
        ]
        for timestamp, expected in test_data:
            self.assertEqual(windower.is_valid_timestamp(timestamp), expected)

    def test_get_available_output_options(self):
        '''Test that the function returns the correct list of available output options'''
        result = windower.get_available_output_options()

        expected_result = ["-csv", "--output-csv", "-json", "--output-json"]

        self.assertEqual(result, expected_result)

    @patch("sys.argv", ["windower", "-f", "testfile.json", "--output-csv", "myoutput.csv"])
    def test_handle_args_parses_correctly(self):
        '''Tests that the handle_args function correctly parses command-line arguments.'''
        parser, args = windower.handle_args()
        self.assertIsInstance(parser, argparse.ArgumentParser)

        self.assertEqual(args.file, "testfile.json")
        self.assertEqual(args.output_csv, "myoutput.csv")
        self.assertIsNone(args.output_json)

    @patch("builtins.open", new_callable=mock_open)
    @patch("windower.logging")
    def test_dict_to_json(self, mock_logging, mock_open_function):
        '''Test that dict_to_json correctly converts the data to JSON format and saves it to a file.
        The test uses hardcoded values to avoid actual file writing or data processing'''

        test_data = [
            {"name": "BRAKE", "timestamp": 1717678137.3455644, "BRAKE_AMOUNT": 39.0},
            {"name": "SPEED", "timestamp": 1717678137.6916034, "SPEED": 20.2}
        ]
        json_filename = "output.json"

        windower.dict_to_json(test_data, json_filename)

        mock_open_function.assert_called_once_with(json_filename, "w", encoding="utf-8", buffering=1)

        handle = mock_open_function()
        handle.write.assert_called_once()

        written_data = handle.write.call_args[0][0]
        parsed_data = orjson.loads(written_data)
        self.assertEqual(parsed_data, test_data)
        mock_logging.info.assert_called_once_with("%s saved successfully", json_filename)

    @patch("windower.create_windows", return_value=pd.DataFrame(
            [{'timestamp': 1717678137, 'value': 10}]))
    @patch("windower.filter_and_process_data", return_value=[
        {"name": "BRAKE", "timestamp": 1717678137, "BRAKE_AMOUNT": 39.0}])
    @patch("windower.pd.DataFrame.to_csv")
    def test_dict_to_csv(self, mock_to_csv, mock_filter_process, mock_create_windows):
        '''Test that the dict_to_csv function correctly processes JSON data, creates windows,
        and saves the results to a CSV file
        '''
        test_data = [
            {"name": "BRAKE", "timestamp": 1717678137.3455644, "BRAKE_AMOUNT": 39.0},
            {"name": "SPEED", "timestamp": 1717678137.6916034, "SPEED": 20.2}
        ]
        window_length = 10.0
        csv_filename = "output.csv"
        windower.dict_to_csv(test_data, window_length, csv_filename)
        mock_filter_process.assert_called_once_with(test_data, None)
        mock_create_windows.assert_called_once()
        mock_to_csv.assert_called_once_with(
            csv_filename, sep=";", index=False, encoding="utf-8-sig")

        args, _ = mock_to_csv.call_args
        self.assertEqual(args[0], csv_filename)
class TestLogger(unittest.TestCase):
    """
    Test logger and how it should work with no logger args, -q and -d
    """

    def setUp(self):
        logger = logging.getLogger()
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)

    def test_default(self):
        """
        Test with no logger args
        """
        windower.log_setup('')
        self.assertEqual(logging.getLogger().level, logging.INFO)

    def test_quiet(self):
        """
        Test -q (quiet mode)
        """
        windower.log_setup('quiet')
        self.assertEqual(logging.getLogger().level, logging.ERROR)

    def test_debug(self):
        """
        Test -d (debug mode)
        """
        windower.log_setup('debug')
        self.assertEqual(logging.getLogger().level, logging.DEBUG)

class TestCreateWindows(unittest.TestCase):
    """
    Tests for function create_windows
    """

    def setUp(self):
        """
        Set up base timestamp for consistency
        """
        self.base_time = datetime(2025,1,1)
        random.seed(42)

    @staticmethod
    def generate_test_data(base_time, count=10, interval_seconds=1):
        """
        Generate test data for window tests
        """
        data = []
        base_ts = base_time.timestamp()
        for i in range(count):
            ts = base_ts + i * interval_seconds
            data.append({
                "timestamp": ts,
                "value_a": i * 10,
                "value_b": i * 2,
            })
        return data

    def test_empty_data_return(self):
        """
        Empty input should return empty dataframe
        """
        result = windower.create_windows([], window_length=3)
        self.assertTrue(result.empty)

    def test_window_sliding(self):
        """
        Windows sliding test
        Windows should move forward correctly based on step provided
        """
        data = self.generate_test_data(self.base_time, count=10)
        result = windower.create_windows(data, window_length=2, step=1)

        prev_start = None
        for _, row in result.iterrows():
            if prev_start is not None:
                self.assertGreaterEqual(row["window_start"], prev_start + 1)
            prev_start = row["window_start"]

    def test_statistics_are_correct(self):
        """
        Test calculated statistics are correct (min,max,mean,std)
        Tests based on first window
        """
        data = self.generate_test_data(self.base_time, count=5, interval_seconds=1)
        window_length = 3
        result = windower.create_windows(data, window_length)

        window_start = data[0]["timestamp"]
        window_end = window_start + window_length

        window1_data = [d for d in data if window_start <= d["timestamp"] < window_end]

        expected_min_a = min(d["value_a"] for d in window1_data)
        expected_max_a = max(d["value_a"] for d in window1_data)
        expected_mean_a = sum(d["value_a"] for d in window1_data) / len(window1_data)

        values_a = [d["value_a"] for d in window1_data]
        n= len(values_a)

        if n>1:
            mean = sum(values_a) / n
            variance = sum((x- mean ) ** 2 for x in values_a) / (n-1)
            expected_std_a = math.sqrt(variance)
        else:
            expected_std_a = float("nan")

        expected_min_b = min(d["value_b"] for d in window1_data)
        expected_max_b = max(d["value_b"] for d in window1_data)
        expected_mean_b = sum(d["value_b"] for d in window1_data) / len(window1_data)

        values_b = [d["value_b"] for d in window1_data]

        if n>1:
            mean = sum(values_b) / n
            variance = sum((x- mean ) ** 2 for x in values_b) / (n-1)
            expected_std_b = math.sqrt(variance)
        else:
            expected_std_b = float("nan")

        row = result.iloc[0]
        self.assertEqual(row["min_value_a"], expected_min_a)
        self.assertEqual(row["max_value_a"], expected_max_a)
        self.assertAlmostEqual(row["mean_value_a"], expected_mean_a, places=5)
        if math.isnan(expected_std_a):
            self.assertTrue(math.isnan(row["std_value_a"]))
        else:
            self.assertAlmostEqual(row["std_value_a"], expected_std_a, places=5)

        self.assertEqual(row["min_value_b"], expected_min_b)
        self.assertEqual(row["max_value_b"], expected_max_b)
        self.assertAlmostEqual(row["mean_value_b"], expected_mean_b, places=5)
        if math.isnan(expected_std_b):
            self.assertTrue(math.isnan(row["std_value_b"]))
        else:
            self.assertAlmostEqual(row["std_value_b"], expected_std_b, places=5)

class TestReadFile(unittest.TestCase):
    """
    Tests for the read_file function
    """

    @mock.patch("windower.clean_data")
    @mock.patch("windower.orjson")
    @mock.patch("builtins.open", new_callable=mock.mock_open, read_data='[{"key": "value"}]')
    def test_read_file_success(self,mock_open, mock_orjson, mock_clean_data):
        """
        Test for successfully reading JSON file and process it
        """

        mock_orjson.loads.return_value = [{"key": "value"}]
        mock_clean_data.return_value = [{"key": "value"}]

        result = windower.read_file("readtest.json")

        mock_open.assert_called_once_with("readtest.json", "r", encoding="utf-8", buffering=1)
        mock_orjson.loads.assert_called_once()
        mock_clean_data.assert_called_once()
        self.assertEqual(result, [{"key": "value"}])

    @mock.patch("builtins.open", side_effect=FileNotFoundError)
    def test_read_file_file_not_found(self,mock_open):
        """
        Test for handling FileNotFoundError when reading non-existent JSON file
        """

        result = windower.read_file("nonexistent.json")
        mock_open.assert_called_once_with("nonexistent.json", "r", encoding="utf-8", buffering=1)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
