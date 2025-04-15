import subprocess

try:
    from .Modes import Modes
except ImportError:
    from Modes import Modes

class ShellMode(Modes):
    def __init__(self, System):
        self.System = System

    def run(self):
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
        self.System.call(cmd, *args)

    def execute_terimal_command(self, args):
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