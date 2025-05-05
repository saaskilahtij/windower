"""
File: test_windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: This file contains the windower unit tests
"""

import unittest
from unittest.mock import patch, mock_open
import argparse
import orjson
import pandas as pd
import windower
import io
import sys
import logging

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

    @patch("builtins.open", new_callable=mock_open, read_data='[{"name": "TEST", "timestamp": 123, "data": "{\"value\": 42}"}]')
    @patch("windower.orjson.loads")
    def test_read_file_success(self, mock_loads, mock_file):
        """Test successful file reading."""
        mock_loads.return_value = [{"name": "TEST", "timestamp": 123, "data": "{\"value\": 42}"}]
        result = windower.read_file("test.json")
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "TEST")
        mock_file.assert_called_once_with("test.json", "r", encoding="utf-8", buffering=1)
        mock_loads.assert_called_once()

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_read_file_not_found(self, mock_file):
        """Test handling of file not found."""
        result = windower.read_file("nonexistent.json")
        self.assertIsNone(result)

    @patch("builtins.open", new_callable=mock_open, read_data='invalid json')
    @patch("windower.orjson.loads", side_effect=ValueError("Invalid JSON"))
    def test_read_file_invalid_json(self, mock_loads, mock_file):
        """Test handling of invalid JSON."""
        result = windower.read_file("invalid.json")
        self.assertIsNone(result)

    def test_safe_parse_json_valid(self):
        """Test parsing valid JSON."""
        json_data = '{"key": "value", "number": 42}'
        result = windower.safe_parse_json(json_data)
        self.assertEqual(result, {"key": "value", "number": 42})

    def test_safe_parse_json_invalid(self):
        """Test parsing invalid JSON."""
        json_data = 'not a json'
        result = windower.safe_parse_json(json_data)
        self.assertIsNone(result)

    def test_safe_parse_json_empty(self):
        """Test parsing empty input."""
        result = windower.safe_parse_json("")
        self.assertIsNone(result)
        result = windower.safe_parse_json(None)
        self.assertIsNone(result)
        
    def test_safe_parse_json_with_single_quotes(self):
        """Test parsing JSON with single quotes."""
        json_data = "{'key': 'value', 'number': 42}"
        result = windower.safe_parse_json(json_data)
        self.assertEqual(result, {"key": "value", "number": 42})

    def test_create_windows_basic(self):
        """Test creating windows with basic data."""
        test_data = [
            {"timestamp": 1000.0, "value": 10},
            {"timestamp": 1001.0, "value": 20},
            {"timestamp": 1003.0, "value": 30},
            {"timestamp": 1005.0, "value": 40},
        ]
        result = windower.create_windows(test_data, window_length=2.0, step=2.0)
        self.assertEqual(len(result), 3)  # Should create 3 windows
        self.assertEqual(result.iloc[0]["window_start"], 1000.0)
        self.assertEqual(result.iloc[1]["window_start"], 1002.0)
        self.assertEqual(result.iloc[2]["window_start"], 1004.0)

    def test_create_windows_empty(self):
        """Test creating windows with empty data."""
        result = windower.create_windows([], window_length=1.0)
        self.assertTrue(result.empty)

    def test_create_windows_different_step(self):
        """Test creating windows with a step different from window length."""
        test_data = [
            {"timestamp": 1000.0, "value": 10},
            {"timestamp": 1001.0, "value": 20},
            {"timestamp": 1002.0, "value": 30},
            {"timestamp": 1003.0, "value": 40},
            {"timestamp": 1004.0, "value": 50},
        ]
        result = windower.create_windows(test_data, window_length=2.0, step=1.0)
        self.assertEqual(len(result), 5)  # Should create 5 windows with overlap
        self.assertEqual(result.iloc[0]["window_start"], 1000.0)
        self.assertEqual(result.iloc[1]["window_start"], 1001.0)

    def test_create_windows_with_no_timestamp_column(self):
        """Test creating windows with data that has no timestamp column."""
        test_data = [
            {"no_timestamp": 1000.0, "value": 10},
            {"no_timestamp": 1001.0, "value": 20},
        ]
        result = windower.create_windows(test_data, window_length=2.0)
        self.assertTrue(result.empty)
    
    def test_create_windows_with_no_numeric_columns(self):
        """Test creating windows with data that has no numeric columns except timestamp."""
        test_data = [
            {"timestamp": 1000.0, "value": "not_numeric"},
            {"timestamp": 1001.0, "value": "still_not_numeric"},
        ]
        result = windower.create_windows(test_data, window_length=2.0)
        # The result should be empty since there are no numeric columns to calculate stats for
        self.assertTrue(result.empty)

    def test_check_output_options_true(self):
        """Test check_output_options returns True when output options are specified."""
        mock_args = argparse.Namespace(output_csv="output.csv", output_json=None)
        self.assertTrue(windower.check_output_options(mock_args))
        
        mock_args = argparse.Namespace(output_csv=None, output_json="output.json")
        self.assertTrue(windower.check_output_options(mock_args))
        
        mock_args = argparse.Namespace(output_csv="output.csv", output_json="output.json")
        self.assertTrue(windower.check_output_options(mock_args))

    def test_check_output_options_false(self):
        """Test check_output_options returns False when no output options are specified."""
        mock_args = argparse.Namespace(output_csv=None, output_json=None)
        self.assertFalse(windower.check_output_options(mock_args))

    @patch("logging.Logger.setLevel")
    @patch("logging.Logger.addHandler")
    @patch("logging.Logger.hasHandlers", return_value=False)
    def test_log_setup(self, mock_has_handlers, mock_add_handler, mock_set_level):
        """Test log setup with different logging levels."""
        # Test debug level
        windower.log_setup('debug')
        mock_set_level.assert_called_with(logging.DEBUG)
        
        # Test info level
        windower.log_setup('info')
        mock_set_level.assert_called_with(logging.INFO)
        
        # Test quiet level
        windower.log_setup('quiet')
        mock_set_level.assert_called_with(logging.ERROR)
        
        # Test default (should be INFO)
        windower.log_setup('invalid_level')
        mock_set_level.assert_called_with(logging.INFO)
        
        self.assertEqual(mock_add_handler.call_count, 4)

    @patch("windower.dict_to_csv")
    @patch("windower.dict_to_json")
    @patch("windower.read_file")
    @patch("sys.argv", ["windower.py", "-f", "test.json", "-l", "10", "--output-csv", "out.csv"])
    def test_main_with_csv_output(self, mock_read_file, mock_dict_to_json, mock_dict_to_csv):
        """Test main function with CSV output option."""
        mock_read_file.return_value = [{"name": "ECU1"}]
        
        with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
            windower.main()
            mock_dict_to_csv.assert_called_once()
            mock_dict_to_json.assert_not_called()

    @patch("windower.dict_to_csv")
    @patch("windower.dict_to_json")
    @patch("windower.read_file")
    @patch("sys.argv", ["windower.py", "-f", "test.json", "-l", "10", "--output-json", "out.json"])
    def test_main_with_json_output(self, mock_read_file, mock_dict_to_json, mock_dict_to_csv):
        """Test main function with JSON output option."""
        mock_read_file.return_value = [{"name": "ECU1"}]
        
        with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
            windower.main()
            mock_dict_to_csv.assert_not_called()
            mock_dict_to_json.assert_called_once()

    @patch("windower.parse_ecu_names")
    @patch("windower.read_file")
    @patch("sys.argv", ["windower.py", "-f", "test.json", "-list"])
    @patch("builtins.print")
    def test_main_list_ecus(self, mock_print, mock_read_file, mock_parse_ecu_names):
        """Test main function with list ECUs option."""
        mock_read_file.return_value = [{"name": "ECU1"}, {"name": "ECU2"}]
        mock_parse_ecu_names.return_value = ["ECU1", "ECU2"]
        
        windower.main()
        mock_parse_ecu_names.assert_called_once()
        mock_print.assert_called_once()
        self.assertTrue("ECU1" in mock_print.call_args[0][0])
        self.assertTrue("ECU2" in mock_print.call_args[0][0])

    @patch("windower.read_file")
    @patch("sys.argv", ["windower.py", "-f", "test.json", "-l", "10"])
    @patch("builtins.print")
    def test_main_no_output_format(self, mock_print, mock_read_file):
        """Test main function with length but no output format."""
        mock_read_file.return_value = [{"name": "ECU1"}]
        
        windower.main()
        mock_print.assert_called_once()
        output_message = mock_print.call_args[0][0]
        self.assertTrue("Error: No output format specified" in output_message)
        
    @patch("windower.filter_and_process_data")
    def test_dict_to_json_empty_filtered_data(self, mock_filter):
        """Test dict_to_json with window processing but empty filtered data."""
        mock_filter.return_value = []
        test_data = [{"name": "ECU1", "timestamp": 1000.0}]
        windower.dict_to_json(test_data, "output.json", window_length=2.0)
        mock_filter.assert_called_once()
        
    @patch("windower.filter_and_process_data", return_value=[
        {"timestamp": 1000.0, "value": 10},
        {"timestamp": 1001.0, "value": 20}
    ])
    @patch("windower.create_windows", return_value=pd.DataFrame())
    def test_dict_to_json_empty_windows(self, mock_windows, mock_filter):
        """Test dict_to_json with window processing but empty window results."""
        test_data = [{"name": "ECU1", "timestamp": 1000.0}]
        windower.dict_to_json(test_data, "output.json", window_length=2.0)
        mock_filter.assert_called_once()
        mock_windows.assert_called_once()
        
    @patch("windower.filter_and_process_data", return_value=[])
    def test_dict_to_csv_empty_filtered_data(self, mock_filter):
        """Test dict_to_csv with empty filtered data."""
        test_data = [{"name": "ECU1", "timestamp": 1000.0}]
        windower.dict_to_csv(test_data, 2.0, "output.csv")
        mock_filter.assert_called_once()
        
    @patch("windower.filter_and_process_data", return_value=[
        {"timestamp": 1000.0, "value": 10}
    ])
    @patch("windower.create_windows", return_value=pd.DataFrame())
    @patch("windower.pd.DataFrame.to_csv")
    def test_dict_to_csv_empty_windows(self, mock_to_csv, mock_windows, mock_filter):
        """Test dict_to_csv with empty window results."""
        test_data = [{"name": "ECU1", "timestamp": 1000.0}]
        windower.dict_to_csv(test_data, 2.0, "output.csv")
        mock_filter.assert_called_once()
        mock_windows.assert_called_once()
        mock_to_csv.assert_not_called()
        
    def test_filter_and_process_data_with_non_numeric_values(self):
        """Test filter_and_process_data with non-numeric values in the data field."""
        input_data = [
            {"name": "BRAKE", "timestamp": 1000.0, "data": "{\"text\": \"not_numeric\"}"}
        ]
        result = windower.filter_and_process_data(input_data)
        self.assertEqual(result, [])
        
    def test_filter_and_process_data_with_invalid_json(self):
        """Test filter_and_process_data with invalid JSON in the data field."""
        input_data = [
            {"name": "BRAKE", "timestamp": 1000.0, "data": "not valid json"}
        ]
        result = windower.filter_and_process_data(input_data)
        self.assertEqual(result, [])
        
    def test_filter_and_process_data_without_data_field(self):
        """Test filter_and_process_data with missing data field."""
        input_data = [
            {"name": "BRAKE", "timestamp": 1000.0}
        ]
        result = windower.filter_and_process_data(input_data)
        self.assertEqual(result, [])
        
    @patch("sys.argv", ["windower.py", "-f", "test.json", "-list", "--output-csv", "out.csv"])
    def test_handle_args_with_incompatible_options(self):
        """Test handle_args with incompatible options (list-ecus with output options)."""
        with self.assertRaises(SystemExit):
            windower.handle_args()
            
    @patch("windower.dict_to_csv")
    @patch("windower.read_file", return_value=None)
    @patch("sys.argv", ["windower.py", "-f", "nonexistent.json", "-l", "10", "--output-csv", "out.csv"])
    def test_main_with_file_error(self, mock_read_file, mock_dict_to_csv):
        """Test main function with file read error."""
        windower.main()
        mock_dict_to_csv.assert_not_called()

if __name__ == '__main__':
    unittest.main()

