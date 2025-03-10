"""
File: test_windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: This file contains the windower unit tests
"""

import unittest
from unittest.mock import patch
import sys
from windower import main

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
                main()
                mock_load.assert_called_once()
                mock_print.assert_called_with("ECU names found in the data: ECU1, ECU2")

if __name__ == '__main__':
    unittest.main()
