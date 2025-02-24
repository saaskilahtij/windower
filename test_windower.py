"""
File: test_windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: This file contains the windower unit tests
"""

import unittest
import logging
from unittest.mock import patch, mock_open
from windower import handle_args, main,log_setup

class TestWindower(unittest.TestCase):

    @patch('builtins.open', new_callable=mock_open, read_data='{"test":"value"}')
    def test_read_json_file_and_output(self, mock_file):
        """
          Test reading a JSON file and then outputting it to the specified output file
        """
        with patch('sys.argv', ['windower.py', '-f', 'test.json', '-o', 'output.json']):
            main()
        mock_file.assert_any_call('test.json', 'r', encoding='UTF-8')
        mock_file.assert_any_call('output.json', 'w', encoding='UTF-8')
        written_content = ''
        for call in mock_file().write.call_args_list:
            written_content += call[0][0]
        self.assertIn('"test":"value"', written_content)
        
class TestLogger(unittest.TestCase):        
    def test_logsetup(self):
        """
        Fast and simple test for logger setup and messages (can be improved)
        Windower.log should have all 4 messages and console only error-> messages
        """
        
        log_setup()
        logger = logging.getLogger()
        
        self.assertEqual(len(logger.handlers), 2)
        
        logging.debug("Debug message for testing")
        logging.info("Info message for testing")
        logging.error("Error message for testing")
        logging.critical("Critical message for testing")
                
if __name__ == "__main__":
    unittest.main()
