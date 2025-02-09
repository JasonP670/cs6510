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
            # cmd, *args = input("shell > ").split()
            cmd, *args = input("\nshell > ").split()
            verbose = False

            if '-v' in args:
                verbose = True
                args.remove('-v')

            if verbose:
                self.System.verbose = True

            if cmd == 'bash':
                return 'bash'
            if cmd == 'exit':
                return None
            if cmd == 'osx':
                self.execute_terimal_command(args)
                continue
            else:
                self.handle_command(cmd, args)
            

    def handle_command(self, cmd, args):
        self.System.call(cmd, *args)

    def execute_terimal_command(self, args):
        try:
            args.insert(0, 'osx')
            result = subprocess.run(args, text=True, capture_output=True)
            if result.returncode != 0:
                pass
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            print(e.stderr)

if __name__ == '__main__':
    shell = ShellMode()
    shell.run()