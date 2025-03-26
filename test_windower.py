"""
File: test_windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: This file contains the windower unit tests
"""

import unittest
from unittest.mock import patch
import sys
import windower

class TestWindower(unittest.TestCase):
    """
    Test suite for the Windower module.
    This class contains unit tests for the Windower module, specifically testing
    the functionality related to extracting and printing ECU names from JSON data.
    Tests:
        - test_ecu_names_flow: Verifies that the main function correctly prints the
          ECU names by mocking the read_file and parse_ecu_names functions.
    """
    @patch("windower.parse_ecu_names", return_value=["ECU1", "ECU2"])
    @patch("windower.read_file", return_value=[{"name": "ECU1"}, {"name": "ECU2"}])
    def test_ecu_names_flow(self, _mock_read, mock_load):
        """
        Test the flow for extracting and printing ECU names from the JSON data.
        
        This test mocks the read_file and parse_ecu_names functions to simulate
        reading a JSON file and extracting ECU names. It then verifies that the
        main function correctly prints the ECU names.
        """
        test_args = ["windower.py", "--file", "dummy.json", "--ecu-names"]
        with patch.object(sys, 'argv', test_args):
            with patch('builtins.print') as mock_print:
                windower.main()
                mock_load.assert_called_once()
                mock_print.assert_called_with("ECU names found in the data: ECU1, ECU2")

    def test_clean_data_removes_unknowns(self):
        """Test that clean_data removes entries with name 'Unknown'."""
        input_data = [
            {"name": "ECU1"},
            {"name": "Unknown"},
            {"name": "ECU2"},
        ]
        expected_output = [
            {"name": "ECU1"},
            {"name": "ECU2"},
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

if __name__ == '__main__':
    unittest.main()
