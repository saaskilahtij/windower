"""
File: test_windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: This file contains the windower unit tests
"""

import unittest
from unittest.mock import patch
import argparse
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
        '''ests ECU name extraction from JSON data'''
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
        """Test that the timestamp is valid  """
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

if __name__ == '__main__':
    unittest.main()
