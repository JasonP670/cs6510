import os
import sys
from struct import unpack

try:
    from hardware.Memory import Memory
    from hardware.CPU import CPU
    from hardware.Clock import Clock
    from .PCB import PCB
    from .Scheduler import Scheduler
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from hardware.Memory import Memory
    from hardware.CPU import CPU
    from hardware.Clock import Clock
    from PCB import PCB
    from Scheduler import Scheduler

from constants import USER_MODE, KERNEL_MODE, SYSTEM_CODES, instructions

class System:
    def __init__(self):
        self.memory = Memory('200B')
        self.CPU = CPU(self.memory, self)
        self.clock = Clock()
        self.scheduler = Scheduler()
        self.mode = USER_MODE 
        self.loader = None
        self.verbose = False
        self.programs = {}
        self.errors = []
        self.system_codes = SYSTEM_CODES
        # self.PCBs = {}
        self.pid = 0

        # Process management queues
        self.ready_queue = []
        self.job_queue = []
        self.io_queue = []
        self.terminated_queue = []

        self.commands = {
            'load': self.load_file,
            'coredump': self.coredump,
            'errordump': self.errordump,
            "run": self.run_program, 
            "registers": lambda: print(self.CPU),
            "execute": self.execute,
            "clock": lambda: print(self.clock),
        }

    def switch_mode(self):
        new_mode = USER_MODE if self.mode == KERNEL_MODE else KERNEL_MODE
        if self.verbose: self.print(f"Switching user_mode from {self.mode} to {new_mode}")
        self.mode = new_mode

    def call(self, cmd, *args):
        if cmd in self.commands:
            try:
                self.switch_mode() # switch to kernel mode to execute the command
                print()
                self.print(f"Executing command: {cmd}")
                self.commands[cmd](*args) # look up the command in the dictionary and execute it
                self.switch_mode() # switch back to user mode after executing the command
                self.verbose = False # verbose is set to true in the shell, after running the cmd reset it
            except TypeError as e:
                self.system_code(103)
                print(e)
                print(f"Invalid arguments for command: {cmd}")
            except Exception as e:
                print(e)
                self.system_code(100)

        else:
            print(f"Unknown command: {cmd}")
            self.system_code(103)
        
    def execute(self, *args):
        if len(args) < 2 or len(args)%2 != 0:
            self.system_code(103)
            print("Please specify the programs to execute and their arrival times in pairs.")
            return None

        for i in range(0, len(args), 2):
            filepath = args[i]
            arrival_time = int(args[i+1])

            pcb = self.load_file(filepath)
            if pcb:
                pcb.set_arrival_time(arrival_time)
                self.job_queue.append(pcb)


        self.schedule_jobs()
        if (self.verbose):
            self.print_PCBs()

    def print_PCBs(self):
        for pcb in self.ready_queue + self.job_queue + self.io_queue + self.terminated_queue:
            print(f"PCB: {pcb['file']}")
            print(f"  Arrival time: {pcb['arrival_time']}")
            print(f"  Start time: {pcb['start_time']}")
            print(f"  End time: {pcb['end_time']}")
            print(f"  Waiting time: {pcb['waiting_time']}")
            print(f"  Execution time: {pcb['execution_time']}")
            print(f"  State: {pcb['state']}")
            print(f"  Registers: {pcb['registers']}")
            print(f"  Memory: {pcb['loader']} - {pcb['loader'] + pcb['byte_size']}")
            print()

    def schedule_jobs(self):
        self.job_queue.sort(key=lambda x: x.arrival_time)

        while self.job_queue or self.ready_queue:
            # Move jobs from job queue to ready queue
            while self.job_queue and self.clock.time >= self.job_queue[0].arrival_time:
                job = self.job_queue.pop(0)
                self.ready_queue.append(job)
                job.ready()
                self.print('')
                self.print(f"Scheduling job: {job}")

            # Run the next job in the ready queue
            if self.ready_queue:
                job = self.ready_queue.pop(0)
                job['start_time'] = self.clock.time
                job['waiting_time'] = job['start_time'] - job['arrival_time']
                self._load_to_memory(job)
                self.run_pcb(job)
            else:
                # If no job is ready increment clock
                self.clock += 1

    def load_file(self, filepath, *args):
        """ Load file into memory """
        if not filepath:
            return self.system_code(103, "Please specify the file path.")
        
        if len(args) > 0:
            return self.system_code(103, "load command only takes one argument, the file path.")
                
        try:
            with open(filepath, 'rb') as f:
                # Unpack header, which consists of 3 integers (12 bytes)
                byte_size, pc, loader = self._read_header(f)
                
                if not self._is_valid_loader(loader, byte_size, filepath):
                    return None
                
                pcb = self.createPCB(pc, filepath)
                pcb['byte_size'] = byte_size
                pcb['loader'] = loader
                pcb['code_start'] = pc
                pcb['code_end'] = loader + byte_size - 1
                pcb['data_start'] = loader
                pcb['data_end'] = pc - 1

                self.system_code(1)
                return pcb

        except FileNotFoundError:
            print("File not found")
            self.system_code(109)
            return None
        except Exception as e:
            self.system_code(100)
            print("An error occurred while loading the file.")
            print(e)
            return None
        
    def createPCB(self, pc, filepath):
        pid = self.pid + 1
        self.pid += 1
        pcb = PCB(pid, pc)
        pcb['file'] = filepath 
        return pcb
    
    def _read_header(self, f):
        header = f.read(12)
        byte_size, pc, loader = unpack('III', header) 
        pc += loader
        self.print(f" - Loading program with {byte_size} bytes, PC at {pc}, loader at {loader}")
        return byte_size, pc, loader
    
    def _is_valid_loader(self, loader, byte_size, filepath):
        if loader > self.memory.size:
            self.system_code(110, f"Loader address {loader} is out of bounds.", filepath)
            return False
        
        if loader + byte_size > self.memory.size:
            self.system_code(102, f"Not enough memory to store program at location {loader}.\nProgram requires {byte_size} bytes.\nMemory has {self.memory.size - loader} bytes available.", filepath)
            return False
                
        return True
    
    def _load_to_memory(self, pcb):

        # Check if another pcb is already loaded at the loader address and not terminated
        for other_pcb in self.ready_queue:
            if ((other_pcb != pcb and other_pcb['file'] != pcb['file']) and # Make sure it's not the same program
               (other_pcb['state'] not in ['TERMINATED', 'NEW'])): # Make sure it's not terminated or new
                if ((pcb['loader'] < other_pcb['code_end'] and pcb['loader'] > other_pcb['code_start']) or 
                   (pcb['code_end'] > other_pcb['loader'] and pcb['code_end'] < other_pcb['code_end'])):
                    self.system_code(102, pcb['file'])
                    return None
    
        with open(pcb['file'], 'rb') as f:
            f.seek(12) # Skip header
            self.memory[pcb['loader'] : pcb['loader'] + pcb['byte_size']] = f.read(pcb['byte_size'])

        if (self.verbose):
            print(self.memory)

    def run_pcb(self, pcb):
        pcb.running()
        self.print(f"Running program: {pcb}")

        while pcb['state'] != 'TERMINATED':
            self.CPU.run_program(pcb, self.verbose)
            if pcb['state'] == 'TERMINATED' and len(pcb.get_children()) == 0:
                self.release_resources(pcb)
            elif pcb['state'] == 'WAITING':
                self.io_queue.append(pcb)
                break
            elif pcb['state'] == 'READY':
                self.ready_queue.append(pcb)
                break
        
        self.schedule_jobs()

        if pcb['state'] == 'TERMINATED' and pcb.has_children():
            self.wait(pcb)

    def release_resources(self, pcb):
        loader = pcb['loader']
        code_end = pcb['code_end']
        self.memory[loader:code_end+1] = [0] * (code_end - loader + 1)
        self.print(f"Released resources for {pcb}")

    def run_program(self, *args):
        if len(self.PCBs) == 0:
            self.system_code(101)
            print("No program loaded.")
            return None
        
        if len(args) == 0:
            self.system_code(103)
            print("Please specify the program to run.")
            return None
        
        program = args[0]
        
        if program not in self.PCBs:
            self.system_code(101)
            print(f"Program {program} not found.")
            return None
        
        pcb = self.PCBs[program]

        self._load_to_memory(pcb)

        self.CPU.run_program(pcb, self.verbose)
        # self.loader = None
        # self.release_resources(pcb)

    def coredump(self):
        if self.verbose:
            print("Coredump:")
            print(self.memory)

        else:
            with open('memory.txt', 'w') as f:
                f.write(str(self.memory))
            print("Memory dumped to memory.txt")
    
    def errordump(self):
        if self.verbose:
            print('Errors:')
            for error in self.errors:
                print(error)

        else:
            with open('errors.txt', 'w') as f:
                for error in self.errors:
                    f.write(str(error) + '\n')
            print("Errors dumped to errors.txt")    

    def print(self, txt):
        """ 
            Checks if system is in verbose mode,
            if so, print the message. 
        """
        if (self.verbose):
            print(txt)

    def log_error(self, code, program=None):
        if code not in self.system_codes:
            print(self.system_codes[100])
        
        if code >= 100:
            self.errors.append({
                'program': program,
                'code': code, 
                'message': self.system_codes[code]},
                )
        print(self.system_codes[code])

    def system_code(self, code, message = None, program=None):
        if code == 0 or code == 1:
            if (message): print(message)
            return None
        
        self.log_error(code, program)

    def fork(self, parent_pcb):
        new_pid = self.pid + 1
        self.pid += 1

        # Copy parent PCB
        child_pcb = parent_pcb.make_child(new_pid, parent_pcb.get_pc())

        child_pcb['arrival_time'] = self.clock.time
        child_pcb.ready()

        parent_pcb.registers[0] = new_pid
        child_pcb.registers[0] = 0

        self.ready_queue.append(child_pcb)

        self.print(f"Forked child process: {child_pcb}")

        return child_pcb

def wait(self, parent_pcb):
        for child_pcb in parent_pcb.get_children():
            while child_pcb['state'] != 'TERMINATED':
                self.run_pcb(child_pcb)
        self.print(f"Parent process {parent_pcb} has waited for all child processes to terminate")

if __name__ == '__main__':
    system = System()
    system.verbose = True
    system.call('execute', 'test.osx', 0)