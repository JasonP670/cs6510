import os
import sys
from tabulate import tabulate
import random

try:
    from hardware.CPU import CPU
    from hardware.Clock import Clock
    from .PCB import PCB
    from .Scheduler import Scheduler
    from .MemoryManager import MemoryManager
    from .Queue import Queue
except ImportError:
    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    )
    from hardware.CPU import CPU
    from hardware.Clock import Clock
    from PCB import PCB
    from Scheduler import Scheduler
    from MemoryManager import MemoryManager
    from Queue import Queue

from constants import USER_MODE, KERNEL_MODE, SYSTEM_CODES, PCBState, CHILD_EXEC_PROGRAM


class System:
    def __init__(self):
        self.clock = Clock()
        self.scheduler = Scheduler(self)
        self.memory_manager = MemoryManager(self, '1K')
        self.memory = self.memory_manager.memory
        self.CPU = CPU(self.memory, self)
        self.mode = USER_MODE
        self.verbose = False
        self.errors = []
        self.system_codes = SYSTEM_CODES
        self.pid = 0
        self.execution_history = []  # List to store process execution history

        # Process management queues
        self.ready_queue = []
        self.job_queue = []
        self.io_queue = []
        self.terminated_queue = []

        self.Q1 = Queue()
        self.Q2 = Queue()
        self.Q3 = Queue()

        self.shared_memory = {}
        self.mutex = 0

        self.commands = {
            'load': self.handle_load,
            'coredump': self.coredump,
            'errordump': self.errordump,
            "run": self.run_program,
            "registers": lambda: print(self.CPU),
            "execute": self.execute,
            "clock": lambda: print(self.clock),
            "job_queue": lambda: print(self.job_queue),
            "ready_queue": lambda: print(self.ready_queue),
            "io_queue": lambda: print(self.io_queue),
            "terminated_queue": lambda: print(self.terminated_queue),
            'setSched': self.scheduler.set_strategy,
            'setRR': self.setRR,
            'quantums': lambda: print(f"Q1: {self.Q1.get_quantum()}, Q2: {self.Q2.get_quantum()}"),
            'gantt_graph': lambda: self.scheduler.plot_gantt_chart(True),
            'reset': self.reset,
            'gantt': self.display_gantt_chart,
            'shm_open': self.smh_open,
            'shared_memory': self.print_shared_memory,
            'shm_unlink': self.shm_unlink,
            'ps': self.ps_command,
            'getpagenumber': lambda: print(self.memory_manager.get_page_limit()),
            'setpagenumber': self.set_page_number,
            'getpagesize': lambda: print(self.memory_manager.get_page_size()),
            'setpagesize': self.set_page_size,
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
                self.print(f"\nExecuting command: {cmd}")
                # Look up the command in the dictionary and execute it
                self.commands[cmd](*args)
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
            filepath = os.path.join('programs', filepath)

            self.prepare_program(filepath, arrival_time)

        self.print("Programs added to job queue.")
        if self.verbose:
            self.display_state_table()

        self.scheduler.schedule_jobs()
            

    def prepare_program(self, filepath, arrival_time):
        program_info = self.memory_manager.prepare_program(filepath)

        if program_info:
            pcb = self.create_pcb(program_info, arrival_time)
            self.job_queue.append(pcb)
        else:
            return None

    def create_pcb(self, program_info, arrival_time):
        pid = self.pid + 1
        self.pid += 1

        pcb = PCB(pid, program_info['pc'])
        pcb.file = program_info['filepath']
        pcb.loader = program_info['loader']
        pcb.byte_size = program_info['byte_size']
        pcb.data_start = program_info['data_start']
        pcb.data_end = program_info['data_end']
        pcb.code_start = program_info['code_start']
        pcb.code_end = program_info['code_end']
        pcb.arrival_time = arrival_time

        return pcb

    def run_pcb(self, pcb, quantum):
        pcb.running()
        self.print(f"Running program: {pcb}")

        # Record execution start
        start_time = self.clock.time

        self.CPU.run_program(pcb, quantum, self.verbose)

        # Record execution history
        self.execution_history.append({
            'pid': pcb.pid,
            'start_time': start_time,
            'end_time': self.clock.time,
            'quantum': quantum
        })

    def handle_load(self, *args):
        for filepath in args:
            filepath = os.path.join('programs', filepath)

            program_info = self.memory_manager.prepare_program(filepath)
            if program_info:
                pcb = self.create_pcb(program_info, self.clock.time)
                self.memory_manager.load_to_memory(pcb)
                self.job_queue.append(pcb)
            # Display state table after command execution
            if self.verbose:
                self.display_state_table()

    def handle_check_memory_available(self, pcb):
        try:
            if self.memory_manager.check_memory_available(pcb):
                return True
        except Exception as e:
            print(e)

        return False

    def handle_load_to_memory(self, pcb):
        try:
            if self.memory_manager.load_to_memory(pcb):
                return True
        except Exception as e:
            print(e)

        return False

    def handle_free_memory(self, pcb):
        if self.memory_manager.free_memory(pcb):
            self.print(f"Memory freed for {pcb}")
            return True
        else:
            print(f"Error freeing memory for {pcb}")
        return False

    def run_program(self, *args):
        if len(self.job_queue) == 0 and len(self.ready_queue) == 0:
            self.system_code(101)
            print("No program loaded.")
            return None

        if len(args) == 0:
            self.system_code(103)
            print("Please specify the program to run.")
            return None

        for arg in args:

            program = 'programs\\' + arg

            pcb = None
            for job in self.job_queue + self.ready_queue:
                if job.file == program:
                    pcb = job
                    break
            self.job_queue.remove(pcb)
            self.print(f"Running program: {pcb}")

            pcb.start_time = self.clock.time
            self.CPU.run_program(pcb, 1_000_000, self.memory_manager, self.verbose)

            if pcb.state == PCBState.TERMINATED:
                # self.memory_manager.free_memory(pcb)
                self.terminated_queue.append(pcb)
                pcb.end_time = self.clock.time

            if self.verbose:
                self.display_state_table()

            # return pcb.registers[0]

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

    def log_error(self, code, message=None, program=None):
        if code not in self.system_codes:
            print(self.system_codes[100])

        if code >= 100:
            self.errors.append({
                'program': program,
                'code': code,
                'message': message,
                'code_error': self.system_codes[code]},
            )
        print(self.system_codes[code])

    def system_code(self, code, message=None, program=None):
        if message:
            print(message)
        if code in (0, 1):
            return

        self.log_error(code, message, program)

    def fork(self, parent_pcb):
        new_pid = self.pid + 1
        self.pid += 1

        # Copy parent PCB
        child_pcb = parent_pcb.make_child(new_pid, parent_pcb.pc)

        child_pcb.arrival_time = self.clock.time
        # child_pcb.ready(self.clock.time)

        parent_pcb.registers[0] = new_pid
        child_pcb.registers[0] = 0

        parent_pcb.state = PCBState.READY
        child_pcb.state = PCBState.READY

        self.print(f"Forked child process: {child_pcb}")

        self.ready_queue.append(child_pcb)
        # self.ready_queue.append(parent_pcb) This will be done by the scheduler

        # self.run_pcb(child_pcb)

    def exec(self, pcb):
        filepath = CHILD_EXEC_PROGRAM
        # arrival_time = self.clock.time

        program_info = self.memory_manager.prepare_program(filepath)

        if program_info:
            pcb.file = program_info['filepath']
            pcb.loader = program_info['loader']
            pcb.byte_size = program_info['byte_size']
            pcb.data_start = program_info['data_start']
            pcb.data_end = program_info['data_end']
            pcb.code_start = program_info['code_start']
            pcb.code_end = program_info['code_end']
            pcb.pc = program_info['pc']
            # pcb.arrival_time = arrival_time

            self.memory_manager.load_to_memory(pcb)
            self.run_pcb(pcb)
        else:
            return None

    def wait(self, pcb):
        if any([child_pcb.state != PCBState.TERMINATED for child_pcb in pcb.get_children()]):
            self.print(
                f"Parent process {pcb} is waiting for children to terminate")
            pcb.ready(self.clock.time)
            return
        msg = f"Parent process {pcb} has waited for all children to terminate"
        self.print(msg)

    def display_state_table(self):
        """
        Display a tabulated view of all processes in different queues
        """
        headers = ["PID", "Program", "State",
                   "Queue", "Arrival", "Start", "End", "Turnaround", "Waiting", "Response"]
        table_data = []

        # Helper function to add queue entries to table data
        def add_queue_entries(queue_name, queue):
            for pcb in queue:
                table_data.append([
                    pcb.pid,
                    pcb.file,
                    pcb.state.name,
                    queue_name,
                    pcb.arrival_time,
                    pcb.start_time,
                    pcb.end_time,
                    pcb.turnaround_time,
                    pcb.waiting_time,
                    pcb.response_time

                ])

        # Add entries from all queues
        add_queue_entries("Job Queue", self.job_queue)
        add_queue_entries("Ready Queue", self.ready_queue)
        add_queue_entries("I/O Queue", self.io_queue)
        add_queue_entries("Terminated", self.terminated_queue)
        add_queue_entries("Q1", self.Q1.processes)
        add_queue_entries("Q2", self.Q2.processes)
        add_queue_entries("Q3", self.Q3.processes)

        # Sort by PID for consistent display
        table_data.sort(key=lambda x: x[0])

        print("\nSystem State Table:")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        print()

    def setRR(self, *args):
        quantum1 = int(args[0])
        quantum2 = int(args[1])
        self.Q1.set_quantum(quantum1)
        self.Q2.set_quantum(quantum2)

    def smh_open(self, *args):
        if len(args) != 1:
            print("Please specify the shared memory name. 'smh_open <name>'")
            return None
        self.shared_memory[args[0]] = [] # Unbounded buffer

    def shm_unlink(self, *args):
        if len(args) != 1:
            print("Please specify the shared memory name. 'shm_unlink <name>'")
            return None
        if args[0] in self.shared_memory:
            del self.shared_memory[args[0]]
            print(f"Shared memory {args[0]} unlinked.")
        else:
            print(f"Shared memory {args[0]} not found.")

    def print_shared_memory(self, *args):
        if len(args) == 0:
            print("Please specify the shared memory to print. 'shared_memory <name>'")
            return None
        

        if args[0] in self.shared_memory:
            print(self.shared_memory[args[0]])
        else:
            print(f"Shared memory {args[0]} not found.")

    def reset(self):
        self.clock.reset()
        self.scheduler.reset()
        self.memory_manager.reset()
        self.CPU.reset()
        self.Q1.reset()
        self.Q2.reset()
        self.Q3.reset()
        self.job_queue = []
        self.ready_queue = []
        self.io_queue = []
        self.terminated_queue = []
        self.pid = 0
        self.errors = []
        self.execution_history = []  # List to store process execution history
        self.verbose = False
        self.print("System reset.")

    def process_table(self):
        all_pcb_lists = [self.job_queue, self.ready_queue, self.io_queue, self.terminated_queue]
        table = {}
        for queue in all_pcb_lists:
            for pcb in queue:
                table[pcb.pid] = pcb
        return table
    
    def set_page_number(self, *args):
        """
        Sets the page number limit for the memory manager.

        Args:
            *args: A variable-length argument list. Expects a single argument
                   which is the page number as an integer.

        Returns:
            None

        Behavior:
            - If no arguments or more than one argument are provided, prints an
              error message prompting the user to specify a single page number.
            - If the provided argument cannot be converted to an integer, prints
              an error message indicating an invalid page number.
            - If a valid integer is provided, sets the page limit in the memory
              manager.

        Example:
            set_page_number("10")  # Sets the page limit to 10.
            set_page_number()      # Prints an error message.
            set_page_number("abc") # Prints an error message.
        """
        if len(args) != 1:
            print("Please specify the number of pages. 'setpagenumber <number>'")
            return None
        try:
            self.memory_manager.set_page_limit(int(args[0]))
        except ValueError:
            print("Invalid page number. Please enter a valid integer.")
            return None
        
        
        
    def set_page_size(self, *args):
        """
        Sets the page size for the memory manager.
        Args:
            *args: A single argument specifying the page size as an integer.
        Returns:
            None
        Behavior:
            - Lines of code that are in a page, will by mutiplied by 6 to get bytes
            - If no arguments or more than one argument are provided, prints an error message
              prompting the user to specify the page size in the correct format.
            - If the provided argument cannot be converted to an integer, prints an error
              message indicating that the page size must be a valid integer.
            - If a valid integer is provided, sets the page size in the memory manager.
        Example:
            set_page_size(1)
        """
        if len(args) != 1:
            print("Please specify the page size. 'setpagesize <size>'")
            return None
        try:
            self.memory_manager.set_page_size(int(args[0]))
        except ValueError:
            print("Invalid page size. Please enter a valid integer.")
            return None
    
    def display_memory_frames(self):
        print("\n=== Physical Memory Map ===")
        print("Frame | PID | Page # | Dirty | Ref")
        print("------+-----+--------+-------+-----")

        frame_usage = ['-'] * self.memory_manager.num_frames
        for pid, pcb in self.process_table().items():
            for vp, entry in pcb.page_table.items():
                if entry.valid:
                    frame_usage[entry.frame] = (pid, vp, entry.dirty, entry.reference)

        for frame in range(self.memory_manager.num_frames):
            entry = frame_usage[frame]
            if entry == '-':
                print(f"{frame:5} |  -  |   -    |       |")
            else:
                pid, vp, dirty, ref = entry
                print(f"{frame:5} | {pid:3} | {vp:6} |   {'✔' if dirty else '✘'}   |  {'✔' if ref else '✘'}")


    def ps_command(self, *args):
        print("\n=== Memory Status Report ===")

        page_size = self.memory_manager.page_size
        total_pages = self.memory_manager.num_frames
        free_frames = len(self.memory_manager.free_frames)
        used_frames = total_pages - free_frames

        print(f"Page Size: {page_size} bytes")
        print(f"Total Pages: {total_pages}")
        print(f"Used Pages: {used_frames}")
        print(f"Free Pages: {free_frames}")
        print(f"Total Memory: {self.memory.size} bytes")
        print(f"Free Memory: {free_frames * page_size} bytes")
        print(f"Used Memory: {used_frames * page_size} bytes")
        # self.display_memory_frames()

        print("\n=== Process Page Tables ===")

        for pid, pcb in self.process_table().items():
            print(f"\nPID {pid} - {pcb.file} - State: {pcb.state.name}")
            print(f"  Page Count: {pcb.num_pages}")
            print("  Page Table:")
            for vp, entry in pcb.page_table.items():
                frame_str = f"{entry.frame:2}" if entry.frame is not None else " - "
                status = "Valid" if entry.valid else "Invalid"
                print(f"    Page {vp:2} → Frame {frame_str} [{status}, R={entry.reference}, D={entry.dirty}]")
            print(f"  Registers: {pcb.registers}")


    def display_gantt_chart(self):
        """
        Display a horizontal Gantt chart showing process execution over time
        """
        if not self.execution_history:
            print("No execution history available.")
            return

        # Find the maximum time to determine chart width
        max_time = max(entry['end_time'] for entry in self.execution_history)

        # Sort processes by start time
        sorted_history = sorted(self.execution_history,
                                key=lambda x: x['start_time'])

        # Get unique PIDs to determine chart height
        pids = sorted(set(entry['pid'] for entry in self.execution_history))

        # Create the header with time markers
        print("\nGantt Chart:")
        print("PID |", end="")
        for t in range(max_time + 1):
            print(f"{t:2}", end="")
        print("\n----|" + "-" * (2 * (max_time + 1)))

        # Create timeline for each process
        for pid in pids:
            print(f"P{pid:2} |", end="")

            # Fill the timeline
            current_time = 0
            while current_time <= max_time:
                # Find if process was running at this time
                running = False
                quantum = None

                for entry in sorted_history:
                    if (entry['pid'] == pid and
                            entry['start_time'] <= current_time < entry['end_time']):
                        running = True
                        quantum = entry['quantum']
                        break

                if running:
                    print(f"{quantum}", end="")
                else:
                    print(" .", end="")
                current_time += 1
            print()  # New line after each process

        # Print legend
        print("\nLegend:")
        print("  . = Idle")
        print("  # = Number shown is quantum value used")


if __name__ == '__main__':
    system = System()
    system.verbose = True
    system.call('execute', 'programs/fork.osx', 0)
