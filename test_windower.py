import unittest
from unittest.mock import patch, mock_open
from windower import handle_args, main

class TestWindower(unittest.TestCase):
    def test_file_argument_is_required(self):
        with patch('sys.argv', ['windower.py', '-f', 'sample.json']):
            parsed_args = handle_args()
            self.assertEqual(parsed_args.file, 'sample.json')

    def test_no_arguments_shows_help(self):
        with patch('sys.argv', ['windower.py']):
            with self.assertRaises(SystemExit):
                handle_args()

    @patch('builtins.open', new_callable=mock_open, read_data='{"test":"value"}')
    def test_read_json_file_and_output(self, mock_file):
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
