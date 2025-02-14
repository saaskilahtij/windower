"""
File: test_windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: This file contains the windower unit tests
"""
import unittest
from unittest.mock import patch, mock_open
from windower import handle_args, main

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

if __name__ == "__main__":
    unittest.main()
