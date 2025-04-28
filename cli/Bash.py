try:
    from cli.Modes import Modes
except ImportError:
    from Modes import Modes

class BashMode(Modes):
    def __init__(self, system):
        self.system = system
        
    def run(self):
        print("Welcome to bash mode. Type 'switch shell' to switch to shell mode. Type 'exit' to exit the shell.")
        while True:
            cmd = input("bash > ").strip()
            if (cmd == 'switch shell'):
                return 'shell'
            if (cmd == 'exit'):
                return None
            if (cmd == "say hello"):
                self.say_hello()
            else:
                print("Command not recognized")
            
    def say_hello(self):
        print("I am a more advanced version, I don't say hello to the likes of you")