import subprocess

try:
    from .Modes import Modes
except ImportError:
    from Modes import Modes

class ShellMode(Modes):
    """
    A class representing a shell mode for interacting with the system.
    Attributes:
        System (object): The system object that provides functionality for handling commands.
    Methods:
        __init__(System):
            Initializes the ShellMode with the given system object.
        run():
            Starts the shell mode, allowing the user to input commands. 
            Supports switching to bash mode, exiting the shell, and executing commands.
        handle_command(cmd, args):
            Handles a specific command by delegating it to the system object.
        execute_terimal_command(args):
            Executes a terminal command using the subprocess module and prints the output.
    """
    def __init__(self, System):
        self.System = System

    def run(self):
        """
        Runs the shell mode, allowing the user to input and execute commands interactively.
        The shell provides the following functionalities:
        - Displays a welcome message with instructions for usage.
        - Accepts user input in the form of commands.
        - Supports verbose mode by including the '-v' flag in the command.
        - Processes piped commands separated by the '|' character.
        - Handles specific commands:
            - 'bash': Switches to bash mode and exits the shell.
            - 'exit': Exits the shell.
            - 'osx': Executes terminal commands using the `execute_terimal_command` method.
            - Other commands are handled by the `handle_command` method.
        Returns:
            str: 'bash' if the user switches to bash mode.
            None: If the user exits the shell.
        """
        print("Welcome to shell mode. Type 'bash' to switch to bash mode. Type 'exit' to exit the shell.")
        while True:
            cmd_line = input("\nshell > ").strip()
            verbose = False

            if '-v' in cmd_line:
                verbose = True
                cmd_line = cmd_line.replace('-v', '').strip()

            if verbose:
                self.System.verbose = True

            commands = cmd_line.split('|')
            for command in commands:
                command = command.strip()
                if not command:
                    continue

                cmd, *args = command.split()

                if cmd == 'bash':
                    return 'bash'
                if cmd == 'exit':
                    return None
                if cmd == 'osx':
                    self.execute_terimal_command(args)
                else:
                    self.handle_command(cmd, args)
            

    def handle_command(self, cmd, args):
        """
        Handles the execution of a command by delegating it to the system.

        Args:
            cmd (str): The command to be executed.
            args (list): A list of arguments to be passed to the command.     
        """
        self.System.call(cmd, *args)

    def execute_terimal_command(self, args):
        """
        Compiles asm code
        Args:
            args (str): file name to compile
        Behavior:
            - Calls compiler with the provided file name
        """
        try:
            args.insert(0, 'osx')
            result = subprocess.run(args, text=True, capture_output=True)
            print(result.stdout)
            
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            print(e.stderr)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    shell = ShellMode()
    shell.run()