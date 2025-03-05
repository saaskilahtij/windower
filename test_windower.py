"""
File: test_windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: This file contains the windower unit tests
"""

import unittest
import logging
from unittest.mock import patch, mock_open, MagicMock
import sys
from windower import handle_args, main, log_setup

class TestWindower(unittest.TestCase):
    @patch("windower.load_ecu_names", return_value=["ECU1", "ECU2"])
    @patch("windower.read_file", return_value=[{"name": "ECU1"}, {"name": "ECU2"}])
    def test_ecu_names_flow(self, mock_read, mock_load):
        test_args = ["windower.py", "--file", "dummy.json", "--ecu-names"]
        with patch.object(sys, 'argv', test_args):
            from windower import main
            with patch('builtins.print') as mock_print:
                main()
                mock_load.assert_called_once()
                mock_print.assert_called_with("ECU names found in the data: ECU1, ECU2")

if __name__ == '__main__':
    unittest.main()

