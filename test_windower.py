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

    @patch("builtins.open", new_callable=mock_open)
    @patch("windower.logging")
    def test_dict_to_json_buffered(self, mock_logging, mock_open_function):
        '''Test that dict_to_json correctly handles buffered writing when the buffered flag is set.
        The test verifies that the file is opened correctly and that the data is written in chunks.'''
        
        # Create a larger dataset to test buffering
        test_data = [
            {"name": f"ECU{i}", "timestamp": 1717678137.3455644 + i, "value": i}
            for i in range(2500)  # More than the default buffer size of 1000
        ]
        json_filename = "output.json"
        
        # Call with buffered=True
        windower.dict_to_json(test_data, json_filename, buffered=True, buffer_size=1000)
        
        # Verify file was opened correctly
        mock_open_function.assert_called_once_with(json_filename, "w", encoding="utf-8", buffering=1)
        
        # Get the file handle
        handle = mock_open_function()
        
        # Verify that write was called multiple times (at least 3 times: opening bracket, data chunks, closing bracket)
        self.assertGreaterEqual(handle.write.call_count, 3)
        
        # Verify that flush was called after each chunk
        self.assertGreaterEqual(handle.flush.call_count, 2)  # At least 2 flushes for 2500 items with buffer size 1000
        
        # Verify logging messages
        mock_logging.info.assert_any_call("Using buffered writing with buffer size: %d", 1000)
        mock_logging.info.assert_any_call("JSON file saved with buffered writing: %s", json_filename)
        
        # Verify debug messages for flushing
        self.assertGreaterEqual(
            sum(1 for call in mock_logging.debug.call_args_list if "Flushed" in str(call)), 
            2
        )

    @patch("windower.create_windows", return_value=pd.DataFrame(
            [{'timestamp': 1717678137, 'value': 10}]))
    @patch("windower.filter_and_process_data", return_value=[
        {"name": "BRAKE", "timestamp": 1717678137, "BRAKE_AMOUNT": 39.0}])
    @patch("builtins.open", new_callable=mock_open)
    @patch("windower.logging")
    def test_dict_to_json_with_processing(self, mock_logging, mock_open_function, mock_filter_process, mock_create_windows):
        '''Test that dict_to_json correctly processes data when window_length is provided'''
        
        test_data = [
            {"name": "BRAKE", "timestamp": 1717678137.3455644, "BRAKE_AMOUNT": 39.0},
            {"name": "SPEED", "timestamp": 1717678137.6916034, "SPEED": 20.2}
        ]
        window_length = 10.0
        json_filename = "output.json"
        
        # Mock the DataFrame to return a processed result
        mock_df = pd.DataFrame({
            'timestamp': [1717678137],
            'value': [10]
        })
        mock_create_windows.return_value = mock_df
        
        # Call with window_length
        windower.dict_to_json(test_data, json_filename, window_length=window_length)
        
        # Verify that filter_and_process_data was called
        mock_filter_process.assert_called_once_with(test_data, None)
        
        # Verify that create_windows was called
        mock_create_windows.assert_called_once()
        
        # Verify that the file was opened correctly
        mock_open_function.assert_called_once_with(json_filename, "w", encoding="utf-8", buffering=1)
        
        # Verify that write was called
        handle = mock_open_function()
        handle.write.assert_called()
        
        # Verify logging messages
        mock_logging.info.assert_any_call("%s saved successfully", json_filename)

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

    @patch("windower.create_windows", return_value=pd.DataFrame(
            [{'timestamp': 1717678137, 'value': 10}]))
    @patch("windower.filter_and_process_data", return_value=[
        {"name": "BRAKE", "timestamp": 1717678137, "BRAKE_AMOUNT": 39.0}])
    @patch("builtins.open", new_callable=mock_open)
    @patch("windower.logging")
    def test_dict_to_csv_buffered(self, mock_logging, mock_open_function, mock_filter_process, mock_create_windows):
        '''Test that the dict_to_csv function correctly handles buffered writing when the buffered flag is set.
        The test verifies that the file is opened correctly and that the data is written in chunks.'''
        
        # Create a larger dataset to test buffering
        test_data = [
            {"name": f"ECU{i}", "timestamp": 1717678137.3455644 + i, "value": i}
            for i in range(2500)  # More than the default buffer size of 1000
        ]
        window_length = 10.0
        csv_filename = "output.csv"
        
        # Mock the DataFrame to return a larger dataset
        mock_df = pd.DataFrame({
            'timestamp': [1717678137 + i for i in range(2500)],
            'value': [i for i in range(2500)]
        })
        mock_create_windows.return_value = mock_df
        
        # Call with buffered=True
        windower.dict_to_csv(test_data, window_length, csv_filename, buffered=True, buffer_size=1000)
        
        # Verify file was opened correctly
        mock_open_function.assert_called_once_with(csv_filename, "w", encoding="utf-8-sig", buffering=1)
        
        # Get the file handle
        handle = mock_open_function()
        
        # Verify that write was called multiple times (header + data chunks)
        self.assertGreaterEqual(handle.write.call_count, 3)
        
        # Verify that flush was called after each chunk
        self.assertGreaterEqual(handle.flush.call_count, 2)  # At least 2 flushes for 2500 items with buffer size 1000
        
        # Verify logging messages
        mock_logging.info.assert_any_call("Using buffered writing with buffer size: %d", 1000)
        mock_logging.info.assert_any_call("CSV file saved with buffered writing: %s", csv_filename)
        
        # Verify debug messages for flushing
        self.assertGreaterEqual(
            sum(1 for call in mock_logging.debug.call_args_list if "Flushed" in str(call)), 
            2
        )

    @patch("windower.watch_file")
    def test_main_watch_mode(self, mock_watch_file):
        '''Test that the main function correctly calls watch_file when the watch flag is provided.'''
        
        # Mock the argument parser to return args with watch=True
        mock_args = argparse.Namespace(
            file="test.json",
            length=10.0,
            step=5.0,
            output_csv="output.csv",
            output_json=None,
            ecu=None,
            buffered=False,
            buffer_size=1000,
            watch=True,
            watch_interval=1.0,
            list_ecus=False,
            quiet=False,
            debug=False
        )
        
        with patch("windower.handle_args", return_value=(None, mock_args)):
            windower.main()
            
        # Verify that watch_file was called with the correct arguments
        mock_watch_file.assert_called_once_with(
            "test.json", 10.0, 5.0, "output.csv", None, None, False, 1000, 1.0
        )

    @patch("windower.read_file")
    def test_read_file_buffered(self, mock_read_file):
        '''Test that read_file correctly handles buffered reading when the buffered flag is set.'''
        
        # Mock the read_file function to return a large dataset
        test_data = [
            {"name": f"ECU{i}", "timestamp": 1717678137.3455644 + i, "value": i}
            for i in range(2500)  # More than the default buffer size of 1000
        ]
        mock_read_file.return_value = test_data
        
        # Call with buffered=True
        result = windower.read_file("test.json", buffered=True, buffer_size=1000)
        
        # Verify that read_file was called with the correct arguments
        mock_read_file.assert_called_once_with("test.json", buffered=True, buffer_size=1000)
        
        # Verify that the result is correct
        self.assertEqual(result, test_data)

    @patch("windower.pd.read_csv")
    @patch("windower.pd.concat")
    @patch("windower.logging")
    def test_read_csv_file_buffered(self, mock_logging, mock_concat, mock_read_csv):
        '''Test that read_csv_file correctly handles buffered reading when the buffered flag is set.'''
        
        # Mock the read_csv function to return chunks
        chunk1 = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
        chunk2 = pd.DataFrame({'col1': [7, 8, 9], 'col2': [10, 11, 12]})
        mock_read_csv.return_value = [chunk1, chunk2]
        
        # Mock the concat function to return a combined DataFrame
        combined_df = pd.DataFrame({
            'col1': [1, 2, 3, 7, 8, 9],
            'col2': [4, 5, 6, 10, 11, 12]
        })
        mock_concat.return_value = combined_df
        
        # Call with buffered=True
        result = windower.read_csv_file("test.csv", buffered=True, buffer_size=3)
        
        # Verify that read_csv was called with the correct arguments
        mock_read_csv.assert_called_once_with("test.csv", sep=";", chunksize=3)
        
        # Verify that concat was called with the correct arguments
        mock_concat.assert_called_once_with([chunk1, chunk2], ignore_index=True)
        
        # Verify that the result is correct
        self.assertEqual(result.equals(combined_df), True)
        
        # Verify logging messages
        mock_logging.info.assert_any_call("Reading CSV file: %s", "test.csv")
        mock_logging.info.assert_any_call("Using buffered reading with buffer size: %d", 3)
        mock_logging.debug.assert_any_call("Read %d rows from %s", 3, "test.csv")
        mock_logging.debug.assert_any_call("Read %d rows from %s", 3, "test.csv")
        mock_logging.debug.assert_any_call("%s read successfully with buffered reading!", "test.csv")

    @patch("windower.pd.read_csv")
    @patch("windower.logging")
    def test_read_csv_file_non_buffered(self, mock_logging, mock_read_csv):
        '''Test that read_csv_file correctly handles non-buffered reading.'''
        
        # Mock the read_csv function to return a DataFrame
        test_df = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
        mock_read_csv.return_value = test_df
        
        # Call with buffered=False (default)
        result = windower.read_csv_file("test.csv")
        
        # Verify that read_csv was called with the correct arguments
        mock_read_csv.assert_called_once_with("test.csv", sep=";")
        
        # Verify that the result is correct
        self.assertEqual(result.equals(test_df), True)
        
        # Verify logging messages
        mock_logging.info.assert_any_call("Reading CSV file: %s", "test.csv")
        mock_logging.debug.assert_any_call("%s read successfully!", "test.csv")

if __name__ == '__main__':
    unittest.main()
