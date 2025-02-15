import os
import sys
from tabulate import tabulate

try:
    from hardware.CPU import CPU
    from hardware.Clock import Clock
    from .PCB import PCB
    from .Scheduler import Scheduler
    from .MemoryManager import MemoryManager
except ImportError:
    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    )
    from hardware.CPU import CPU
    from hardware.Clock import Clock
    from PCB import PCB
    from Scheduler import Scheduler
    from MemoryManager import MemoryManager

from constants import USER_MODE, KERNEL_MODE, SYSTEM_CODES


class System:
    def __init__(self):
        self.clock = Clock()
        self.scheduler = Scheduler(self)
        self.memoryManager = MemoryManager(self, '1K')
        self.memory = self.memoryManager.memory
        self.CPU = CPU(self.memory, self)
        self.mode = USER_MODE
        self.loader = None
        self.verbose = False
        self.programs = {}
        self.errors = []
        self.system_codes = SYSTEM_CODES
        self.pid = 0

        # Process management queues
        self.ready_queue = []
        self.job_queue = []
        self.io_queue = []
        self.terminated_queue = []

        self.commands = {
            'load': self.handle_load,
            'coredump': self.coredump,
            'errordump': self.errordump,
            "run": self.run_program,
            "registers": lambda: print(self.CPU),
            "execute": self.execute,
            "clock": lambda: print(self.clock),
        }

    def switch_mode(self):
        new_mode = USER_MODE if self.mode == KERNEL_MODE else KERNEL_MODE
        if self.verbose:
            self.print(f"Switching user_mode from {self.mode} to {new_mode}")
        self.mode = new_mode

    def call(self, cmd, *args):
        if cmd in self.commands:
            try:
                # Switch to kernel mode to execute the command
                self.switch_mode()
                print()
                self.print(f"Executing command: {cmd}")
                # Look up the command in the dictionary and execute it
                self.commands[cmd](*args)
                # Display state table after command execution
                self.display_state_table()
                # Switch back to user mode after executing the command
                self.switch_mode()
                # Verbose is set to true in the shell, after running reset it
                self.verbose = False
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
        if len(args) < 2 or len(args) % 2 != 0:
            self.system_code(103)
            print(
                "Please specify the programs to execute and their arrival times in pairs.")
            return None

        for i in range(0, len(args), 2):
            filepath = args[i]
            arrival_time = int(args[i+1])

            pcb = self.memoryManager.load_file(filepath)
            if pcb:
                pcb.set_arrival_time(arrival_time)
                self.job_queue.append(pcb)

        self.scheduler.schedule_jobs()
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
            print(
                f"  Memory: {pcb['loader']} - {pcb['loader'] + pcb['byte_size']}")
            print()

    def createPCB(self, pc, filepath):
        pid = self.pid + 1
        self.pid += 1
        pcb = PCB(pid, pc)
        pcb['file'] = filepath
        return pcb

    def run_pcb(self, pcb):
        pcb.running()
        self.print(f"Running program: {pcb}")

        while pcb['state'] != 'TERMINATED':
            self.CPU.run_program(pcb, self.verbose)
            if pcb['state'] == 'TERMINATED' and len(pcb.get_children()) == 0:
                self.memoryManager.release_resources(pcb)
                self.terminated_queue.append(pcb)
            elif pcb['state'] == 'WAITING':
                self.io_queue.append(pcb)
                break
            elif pcb['state'] == 'READY':
                self.ready_queue.append(pcb)
                break

        self.scheduler.schedule_jobs()

        if pcb['state'] == 'TERMINATED' and pcb.has_children():
            self.wait(pcb)

    def handle_load(self, filepath):
        pcb = self.memoryManager.load_file(filepath)
        if pcb:
            self.job_queue.append(pcb)
            self.memoryManager._load_to_memory(pcb)
            self.print(f"Loaded program: {pcb}")

    def run_program(self, *args):
        if len(self.job_queue) == 0 and len(self.ready_queue) == 0:
            self.system_code(101)
            print("No program loaded.")
            return None

        if len(args) == 0:
            self.system_code(103)
            print("Please specify the program to run.")
            return None

        program = args[0]

        pcb = None
        for job in self.job_queue + self.ready_queue:
            if job['file'] == program:
                pcb = job
                break
        self.print(f"Running program: {pcb}")

        self.CPU.run_program(pcb, self.verbose)
        return pcb.registers[0]

    def coredump(self):
        if self.verbose:
            print("Coredump:")
            print(self.memory)
        else:
            with open('memory.txt', 'w', encoding='utf-8') as f:
                f.write(str(self.memory))
            print("Memory dumped to memory.txt")

    def errordump(self):
        if self.verbose:
            print('Errors:')
            for error in self.errors:
                print(error)
        else:
            with open('errors.txt', 'w', encoding='utf-8') as f:
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

    def system_code(self, code, message=None, program=None):
        if code in (0, 1):
            if message:
                print(message)
            return

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
        msg = f"Parent process {parent_pcb} has waited for all children to terminate"
        self.print(msg)

    def display_state_table(self):
        """
        Display a tabulated view of all processes in different queues
        """
        headers = ["PID", "Program", "State",
                   "Queue", "Arrival", "Start", "End"]
        table_data = []

        # Helper function to add queue entries to table data
        def add_queue_entries(queue_name, queue):
            for pcb in queue:
                table_data.append([
                    pcb['pid'],
                    pcb['file'],
                    pcb['state'],
                    queue_name,
                    pcb['arrival_time'],
                    pcb['start_time'],
                    pcb['end_time']
                ])

        # Add entries from all queues
        add_queue_entries("Job Queue", self.job_queue)
        add_queue_entries("Ready Queue", self.ready_queue)
        add_queue_entries("I/O Queue", self.io_queue)
        add_queue_entries("Terminated", self.terminated_queue)

        # Sort by PID for consistent display
        table_data.sort(key=lambda x: x[0])

        print("\nSystem State Table:")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        print()


if __name__ == '__main__':
    system = System()
    system.verbose = True
    # system.call('execute', 'programs/add.osx', 0)
    system.handle_load('programs/add.osx')
    result = system.run_program('programs/add.osx')
    assert result == 2


# SWI to simulate user input, add a random amount of time to the clock, or add a certain amount for each SWI and add multiple SWI
# fork() parent should go to waiting state until all children are terminated
# Given overlapping programs they should all run

# draw gantt chart, generate a string 0 = waiting 1 = running
# be able to track throughput, waiting time, turnaround time, response time
