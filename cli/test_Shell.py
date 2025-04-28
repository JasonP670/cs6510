import unittest
from unittest.mock import patch, MagicMock
from Shell import ShellMode

class TestShellMode(unittest.TestCase):
    def setUp(self):
        # Mocking the System object
        self.mock_system = MagicMock()
        self.shell = ShellMode(self.mock_system)

    @patch('builtins.input', side_effect=['exit'])
    def test_run_exit(self, mock_input):
        result = self.shell.run()
        self.assertIsNone(result)

    @patch('builtins.input', side_effect=['bash'])
    def test_run_bash(self, mock_input):
        result = self.shell.run()
        self.assertEqual(result, 'bash')

    @patch('builtins.input', side_effect=['cmd1 arg1', 'exit'])
    def test_run_handle_command(self, mock_input):
        self.shell.run()
        self.mock_system.call.assert_called_with('cmd1', 'arg1')

    @patch('builtins.input', side_effect=['osx -l', 'exit'])
    @patch('subprocess.run')
    def test_execute_terminal_command(self, mock_subprocess, mock_input):
        mock_subprocess.return_value = MagicMock(stdout="Command executed successfully")
        self.shell.run()
        mock_subprocess.assert_called_with(['osx', '-l'], text=True, capture_output=True)

    @patch('builtins.input', side_effect=['cmd1 -v', 'exit'])
    def test_run_verbose_mode(self, mock_input):
        self.shell.run()
        self.assertTrue(self.mock_system.verbose)

    @patch('builtins.input', side_effect=['invalidcmd', 'exit'])
    def test_run_invalid_command(self, mock_input):
        self.mock_system.call.side_effect = Exception("Invalid command")
        with self.assertRaises(Exception):
            self.shell.run()

if __name__ == '__main__':
    unittest.main()