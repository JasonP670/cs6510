import os
import sys
from tabulate import tabulate
import traceback
from typing import Optional

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

from constants import (
    USER_MODE, KERNEL_MODE, SYSTEM_CODES,
    PCBState, CHILD_EXEC_PROGRAM
)


class System:
    def __init__(self):
        self.clock = Clock()
        self.scheduler = Scheduler(self)
        self.memory_manager = MemoryManager(self, '1M')
        self.memory = self.memory_manager.memory
        self.CPU = CPU(self.memory, self)
        self.mode = USER_MODE
        self.verbose = True  # False is default, True is for testing
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
            "job_queue": lambda: print(self.job_queue),
            "ready_queue": lambda: print(self.ready_queue),
            "io_queue": lambda: print(self.io_queue),
            "terminated_queue": lambda: print(self.terminated_queue),
            "load_process": self.load_process_to_memory,
            "setRR": self.set_quantum,
            "setschd": self.setschd,
            "gantt": self.create_gantt_chart,
            "run_scheduler": self.run_scheduler  # Fixed typo in command name
        }

    def switch_mode(self):
        new_mode = USER_MODE if self.mode == KERNEL_MODE else KERNEL_MODE
        if self.verbose:
            self.print(f"Switching user_mode from {self.mode} to {new_mode}")
        self.mode = new_mode

    def call(self, cmd, *args):
        if cmd in self.commands:
            try:
                # Convert arguments to integers for setRR

                # Switch to kernel mode to execute the command
                self.switch_mode()
                self.print(f"\nExecuting command: {cmd}")

                # Look up the command in the dictionary and execute it
                result = self.commands[cmd](*args)

                # Run scheduler after certain commands if processes exist
                if (cmd in ['setRR', 'setschd'] and
                        self.scheduler.jobs_in_any_queue()):
                    self.run_scheduler()

                # Switch back to user mode after executing the command
                self.switch_mode()
                # Verbose is set to true in the shell, after running reset it
                self.verbose = False

                return result
            except ValueError as e:
                print(f"ValueError: {e}. Invalid arguments for command: {cmd}")
                print(traceback.format_exc())
                return None
            except TypeError as e:
                self.system_code(103)
                print(f"TypeError: {e}. Invalid arguments for command: {cmd}")
                print(traceback.format_exc())
                return None
            except KeyError as e:
                print(f"KeyError: {e}. Command not found: {cmd}")
                print(traceback.format_exc())
                return None
            except Exception as e:
                print(f"Unexpected error: {e}")
                print(traceback.format_exc())
                self.system_code(100)
                return None
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

            program_info = self.memory_manager.prepare_program(filepath)
            
            if program_info:
                pcb = self.create_pcb(program_info, arrival_time)
                self.job_queue.append(pcb)
            else:
                return None
        
        self.print("Programs added to job queue.")
        if self.verbose:
            self.display_state_table()

        self.scheduler.schedule_jobs()

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
        pcb.arrival_time = int(arrival_time)

        return pcb

    def run_pcb(self, pcb):
        pcb.running()
        self.print(f"Running program: {pcb}")

        self.CPU.run_program(pcb, self.verbose)

    def handle_load(self, filepath):
        program_info = self.memory_manager.prepare_program(filepath)
        if program_info:
            pcb = self.create_pcb(program_info, self.clock.time)
            self.memory_manager.load_to_memory(pcb)
            self.job_queue.append(pcb)
        # Display state table after command execution
        if self.verbose:
            self.display_state_table()

    def handle_check_memory_available(self, pcb):
        """Check if memory is available for a process.

        Args:
            pcb: Process Control Block to check memory for

        Returns:
            bool: True if memory is available, False otherwise
        """
        try:
            return self.memory_manager.check_memory_available(pcb)
        except MemoryError as e:
            print(f"Memory error: {e}")
            return False
        except Exception as e:
            print(f"Error checking memory availability: {e}")
            return False

    def handle_load_to_memory(self, pcb):
        """Load a process to memory.

        Args:
            pcb: Process Control Block to load

        Returns:
            bool: True if load was successful, False otherwise
        """
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

        program = args[0]

        pcb = None
        for job in self.job_queue + self.ready_queue:
            if job.file == program:
                pcb = job
                break
        self.job_queue.remove(pcb)
        self.print(f"Running program: {pcb}")
        
        pcb.start_time = self.clock.time
        self.CPU.run_program(pcb, self.verbose)

        if pcb.state == PCBState.TERMINATED:
            self.memory_manager.free_memory(pcb)
            self.terminated_queue.append(pcb)
            pcb.end_time = self.clock.time

        if self.verbose:
            self.display_state_table()

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

            self.memory_manager.load_to_memory(pcb)
            self.run_pcb(pcb)
        else:
            return

    def wait(self, pcb):
        if any(child_pcb.state != PCBState.TERMINATED
               for child_pcb in pcb.get_children()):
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

        # Sort by PID for consistent display
        table_data.sort(key=lambda x: x[0])

        print("\nSystem State Table:")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        print()

    def print_numerical_gantt(self):
        """Print a text-based Gantt chart using numbers in the terminal.
        Legend:
        - '-': Before arrival or after completion
        - '0': Waiting/Ready
        - '1': Running
        - '2': Terminated
        """
        if not self.terminated_queue:
            print("No completed processes to display in Gantt chart.")
            return

        # Find the overall timeline boundaries
        start_time = min(pcb.arrival_time for pcb in self.terminated_queue)
        end_time = max(pcb.end_time for pcb in self.terminated_queue)

        # Print header with time markers
        print("\nNumerical Gantt Chart:")
        print("Legend: '-' = Not started/finished, '0' = Finished")
        print("        '1' = Running, '2' = Waiting")
        print("\nTime:", end=" ")
        for t in range(start_time, end_time + 1):
            print(f"{t:1}", end="")
        print()

        # Print timeline for each process
        for pcb in sorted(self.terminated_queue, key=lambda x: x.pid):
            print(f"P{pcb.pid:2}:", end=" ")

            for t in range(start_time, end_time + 1):
                if t < pcb.arrival_time or t >= pcb.end_time:
                    print("-", end="")
                elif pcb.start_time <= t < pcb.end_time:
                    # Check process state at time t
                    if pcb.state == PCBState.RUNNING:
                        print("1", end="")
                    elif pcb.state == PCBState.WAITING:
                        print("2", end="")
                    else:  # READY, WAITING, or other states
                        print("0", end="")
                else:
                    print("0", end="")
            print()  # New line after each process
        print()

    def create_gantt_chart(self):
        """Create and display a Gantt chart of process execution."""
        try:
            import matplotlib.pyplot as plt

            # Collect process execution data
            processes = {}  # pid -> [(start_time, end_time, queue)]

            # Track execution periods for each process
            for pcb in self.terminated_queue:
                if pcb.pid not in processes:
                    processes[pcb.pid] = []
                processes[pcb.pid].append((
                    pcb.start_time,
                    pcb.end_time,
                    'Ready Queue'
                ))

            # Create the Gantt chart
            _, ax = plt.subplots(figsize=(12, 6))

            # Colors for different queues
            colors = {
                'Ready Queue': '#2ecc71',
                'I/O Queue': '#e74c3c',
                'Waiting': '#3498db'
            }

            # Plot each process
            y_ticks = []
            y_labels = []
            for i, (pid, intervals) in enumerate(sorted(processes.items())):
                y_ticks.append(i)
                y_labels.append(f'Process {pid}')

                for start, end, queue in intervals:
                    duration = end - start
                    ax.barh(
                        i, duration, left=start,
                        color=colors.get(queue, '#95a5a6'),
                        edgecolor='black',
                        alpha=0.7
                    )

            # Customize the chart
            ax.set_yticks(y_ticks)
            ax.set_yticklabels(y_labels)
            ax.set_xlabel('Time')
            ax.set_ylabel('Process ID')
            ax.set_title('Process Execution Gantt Chart')

            # Add legend
            legend_elements = [
                plt.Rectangle(
                    (0, 0), 1, 1,
                    facecolor=color,
                    edgecolor='black',
                    alpha=0.7,
                    label=queue
                )
                for queue, color in colors.items()
            ]
            ax.legend(handles=legend_elements, loc='upper right')

            # Add grid
            ax.grid(True, axis='x', alpha=0.3)

            # Save the chart
            plt.savefig('gantt_chart.png', bbox_inches='tight')
            plt.close()

            print("\nGantt chart saved as 'gantt_chart.png'")

        except ImportError:
            print("matplotlib is required for Gantt chart creation.")
            print("Install it using: pip install matplotlib")
            return
        except Exception as e:
            print(f"Error creating Gantt chart: {e}")
            return

    def load_process_to_memory(self, filepath: str, arrival_time: Optional[int] = None):
        """
        Load a process into memory and add it to the new queue.
        Args:
            filepath (str): Path to the program file
            arrival_time (Optional[int], optional): Arrival time for the process.
                Defaults to current clock time.

        Returns:
            PCB: Process Control Block if successful, None if failed
        """
        if arrival_time is None:
            arrival_time = self.clock.time

        # Read the file first to verify it exists
        try:
            with open(filepath, 'r', encoding='utf-8') as _:
                self.print(f"Successfully verified file {filepath}")
        except FileNotFoundError:
            self.print(f"Error: File {filepath} not found")
            return None
        except IOError as e:
            self.print(f"Error reading file {filepath}: {e}")
            return None

        # Prepare the program (analyze and get program info)
        program_info = self.memory_manager.prepare_program(filepath)

        if not program_info:
            self.print(f"Error: Could not prepare program {filepath}")
            return None

        # Create PCB for the process
        pcb = self.create_pcb(program_info, arrival_time)

        # Check if memory is available
        if not self.handle_check_memory_available(pcb):
            self.print(f"Error: Not enough memory available for {pcb}")
            return None

        # Load process into memory
        if not self.handle_load_to_memory(pcb):
            self.print(f"Error: Failed to load {pcb} into memory")
            return None

        # Add to job queue
        self.job_queue.append(pcb)
        self.print(
            f"Successfully loaded {pcb} into memory and added to job queue")

        # Display state table if in verbose mode
        if self.verbose:
            self.display_state_table()

        return pcb

    def setschd(self, *args):
        """Set the scheduling algorithm.
        Args:
            algorithm (str): The scheduling algorithm to use 
                (MLFQ, RR, or FCFS)
        """
        try:
            if not args:
                algorithm = 'MLFQ'  # default
            else:
                algorithm = str(args[0]).strip().upper()  # Normalize input

            if algorithm not in self.scheduler.scheduling_algorithms:
                print(f"Invalid algorithm: {algorithm}")
                print(f"Available: {self.scheduler.scheduling_algorithms}")
                return

            self.scheduler.scheduling_algorithm = algorithm
            self.print(f"Set scheduling algorithm to {algorithm}")

            # Set default quantums for MLFQ
            if algorithm == 'MLFQ':
                # Priority 0 (small quantum)
                self.scheduler.q0_quantum = 1
                # Priority 1 (medium quantum)
                self.scheduler.q1_quantum = 2
                # Priority 2 (FCFS - large quantum)
                self.scheduler.q2_quantum = 100

                # Initialize MLFQ specific attributes
                self.scheduler.ready_queue_0 = []  # High priority
                self.scheduler.ready_queue_1 = []  # Medium priority
                self.scheduler.ready_queue_2 = []  # Low priority
                self.scheduler.cpu_bursts = {}  # Track CPU bursts

                # Move existing processes to high priority queue
                while self.ready_queue:
                    pcb = self.ready_queue.pop(0)
                    self.scheduler.ready_queue_0.append(pcb)
                    self.scheduler.cpu_bursts[pcb.pid] = 0
                    self.print(f"Moved {pcb} to high priority queue")

                self.print("Initialized MLFQ queues and parameters")

        except Exception as e:
            print(f"Error setting scheduling algorithm: {str(e)}")
            return

    def run_scheduler(self):
        """Run processes according to the current scheduling algorithm.
        For RR: Uses quantum settings from setRR
        For MLFQ: Uses 3-level queue with different quantums
        """
        if not self.scheduler.jobs_in_any_queue():
            print("No processes to run")
            return

        print(f"Running scheduler with {self.scheduler.scheduling_algorithm}")

        # Initialize scheduler state
        start_time = self.clock.time
        self.scheduler.last_schedule_time = start_time

        # Sort ready queues based on scheduling algorithm
        algorithm = self.scheduler.scheduling_algorithm
        if algorithm == 'MLFQ':
            self.sort_ready_queue_mlfq()
        elif algorithm == 'RR':
            self.sort_ready_queue_rr()
        else:
            self.sort_ready_queue()

        # Keep running until no more processes
        while self.scheduler.jobs_in_any_queue():
            self.scheduler.print_time()
            self.scheduler.check_new_jobs()
            self.scheduler.check_io_complete()

            if self.scheduler.jobs_in_ready_queue():
                # Get next process based on scheduling algorithm
                if algorithm == 'MLFQ':
                    next_pcb = self.scheduler.schedule_job_mlfq()
                elif algorithm == 'RR':
                    next_pcb = self.scheduler.schedule_job_rr()
                else:
                    next_pcb = self.scheduler.schedule_job()

                # Handle the process state after running
                if next_pcb:
                    self.scheduler.handle_process_state(next_pcb)

                if self.verbose:
                    self.display_state_table()
            else:
                self.clock.time += 1
                self.print("No jobs ready to run")

        # Print final metrics
        self.scheduler.print_metrics(start_time)
        if self.verbose:
            self.display_state_table()
            self.create_gantt_chart()

    # Wrapper methods for Scheduler's protected methods
    def sort_ready_queue_mlfq(self):
        """Wrapper for Scheduler's protected method."""
        self.scheduler._sort_ready_queue_mlfq()

    def sort_ready_queue_rr(self):
        """Wrapper for Scheduler's protected method."""
        self.scheduler._sort_ready_queue_rr()

    def sort_ready_queue(self):
        """Wrapper for Scheduler's protected method."""
        self.scheduler._sort_ready_queue()


if __name__ == '__main__':
    system = System()
    system.verbose = True
    system.call('execute', 'programs/fork.osx', 0)
    # system.handle_load('programs/add.osx')
    # result = system.run_program('programs/add.osx')
    # assert result == 2


# SWI to simulate user input, add a random amount of time to the clock, or add a certain amount for each SWI and add multiple SWI
# fork() parent should go to waiting state until all children are terminated
# Given overlapping programs they should all run

# draw gantt chart, generate a string 0 = waiting 1 = running
# be able to track throughput, waiting time, turnaround time, response time
