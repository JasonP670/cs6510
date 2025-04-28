import unittest
from unittest.mock import patch, MagicMock
from Bash import BashMode

class TestBashMode(unittest.TestCase):
    def setUp(self):
        self.mock_system = MagicMock()
        self.bash_mode = BashMode(self.mock_system)

    @patch('builtins.input', side_effect=['exit'])
    @patch('builtins.print')
    def test_run_exit(self, mock_print, mock_input):
        result = self.bash_mode.run()
        self.assertIsNone(result)
        mock_print.assert_any_call("Welcome to bash mode. Type 'switch shell' to switch to shell mode. Type 'exit' to exit the shell.")

    @patch('builtins.input', side_effect=['switch shell'])
    @patch('builtins.print')
    def test_run_switch_shell(self, mock_print, mock_input):
        result = self.bash_mode.run()
        self.assertEqual(result, 'shell')
        mock_print.assert_any_call("Welcome to bash mode. Type 'switch shell' to switch to shell mode. Type 'exit' to exit the shell.")

    @patch('builtins.input', side_effect=['say hello', 'exit'])
    @patch('builtins.print')
    def test_run_say_hello(self, mock_print, mock_input):
        result = self.bash_mode.run()
        self.assertIsNone(result)
        mock_print.assert_any_call("I am a more advanced version, I don't say hello to the likes of you")

    @patch('builtins.input', side_effect=['unknown command', 'exit'])
    @patch('builtins.print')
    def test_run_unknown_command(self, mock_print, mock_input):
        result = self.bash_mode.run()
        self.assertIsNone(result)
        mock_print.assert_any_call("Command not recognized")

if __name__ == '__main__':
    unittest.main()