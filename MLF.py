import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict


class Process:
    def __init__(self, pid, arrival_time, burst_time, priority):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.priority = priority
        self.completed = False
        self.waiting_time = 0
        self.response_time = -1
        self.turnaround_time = 0


class Queue:
    def __init__(self, quantum):
        self.queue = []
        self.quantum = quantum
        self.time_slice = 0

    def add_process(self, process):
        self.queue.append(process)

    def get_next_process(self):
        if self.is_empty():
            return None
        if self.time_slice < self.quantum:
            self.time_slice += 1
            return self.queue[0]
        else:
            self.time_slice = 0
            self.queue.append(self.queue.pop(0))
            return self.queue[0]

    def is_empty(self):
        return len(self.queue) == 0


def create_gantt_chart(process_history, end_time):
    """Create a Gantt chart visualization of process execution."""
    fig, ax = plt.figure(figsize=(15, 5)), plt.gca()

    # Colors for different queues
    colors = {1: '#FF9999', 2: '#99FF99', 3: '#9999FF'}

    # Plot each process execution
    y_ticks = []
    y_labels = []
    for pid in sorted(set(pid for pid, _, _ in process_history)):
        y_ticks.append(pid)
        y_labels.append(f'Process {pid}')

        # Plot execution blocks for this process
        process_times = [(t, q) for p, t, q in process_history if p == pid]
        for i, (time, queue) in enumerate(process_times):
            ax.barh(pid, 1, left=time, color=colors[queue],
                    edgecolor='black', alpha=0.7)

    # Customize the chart
    ax.set_xlabel('Time')
    ax.set_ylabel('Process ID')
    ax.set_title('Process Execution Gantt Chart')
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    ax.set_xlim(0, end_time)
    ax.grid(True, axis='x', alpha=0.3)

    # Add legend
    legend_elements = [plt.Rectangle((0, 0), 1, 1, facecolor=color, edgecolor='black',
                                     alpha=0.7, label=f'Queue {i}')
                       for i, color in colors.items()]
    ax.legend(handles=legend_elements, loc='upper right')

    return fig


def main():
    # Read tasks from the input file
    with open("input.txt", "r", encoding='utf-8') as file:
        processes = []
        for line in file:
            # Skip empty lines and comments
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Parse process information
            try:
                # Handle both comma-separated and space-separated values
                values = line.replace(',', ' ').split()
                if len(values) != 4:
                    print(
                        f"Skipping invalid line (wrong number of values): {line}")
                    continue
                pid, arrival_time, burst_time, priority = map(int, values)
                processes.append(
                    Process(pid, arrival_time, burst_time, priority))
            except ValueError:
                print(f"Skipping invalid line (invalid numbers): {line}")
                continue

    # Check if we have any processes to schedule
    if not processes:
        print("Error: No valid processes found in input file")
        return

    # Create three queues with different time quantums
    q1 = Queue(8)  # Queue with the smallest quantum
    q2 = Queue(16)
    q3 = Queue(100)  # Queue with the largest quantum

    time = 0
    process_history = []  # Track process execution history for Gantt chart

    while any(process.remaining_time > 0 for process in processes):
        # Add processes to the appropriate queue based on their arrival time
        for process in processes:
            if process.arrival_time <= time and not process.completed:
                if process.priority <= 8:
                    q1.add_process(process)
                elif process.priority <= 16:
                    q2.add_process(process)
                else:
                    q3.add_process(process)

        # Check queues in order of priority
        process = q1.get_next_process()
        if process:
            if process.response_time == -1:
                process.response_time = time - process.arrival_time
            process.waiting_time += time
            print(f"Time {time}: Running process {process.pid} from Queue 1")
            process_history.append((process.pid, time, 1))  # Record execution
            process.remaining_time -= 1
            if process.remaining_time == 0:
                process.turnaround_time = time - process.arrival_time + 1
                process.completed = True

        process = q2.get_next_process()
        if process:
            if process.response_time == -1:
                process.response_time = time - process.arrival_time
            process.waiting_time += time
            print(f"Time {time}: Running process {process.pid} from Queue 2")
            process_history.append((process.pid, time, 2))  # Record execution
            process.remaining_time -= 1
            if process.remaining_time == 0:
                process.turnaround_time = time - process.arrival_time + 1
                process.completed = True

        process = q3.get_next_process()
        if process:
            if process.response_time == -1:
                process.response_time = time - process.arrival_time
            process.waiting_time += time
            print(f"Time {time}: Running process {process.pid} from Queue 3")
            process_history.append((process.pid, time, 3))  # Record execution
            process.remaining_time -= 1
            if process.remaining_time == 0:
                process.turnaround_time = time - process.arrival_time + 1
                process.completed = True

        time += 1

    # Calculate and print statistics
    total_waiting_time = sum(process.waiting_time for process in processes)
    total_response_time = sum(process.response_time for process in processes)
    total_turnaround_time = sum(
        process.turnaround_time for process in processes)

    num_processes = len(processes)
    avg_waiting_time = total_waiting_time / num_processes
    avg_response_time = total_response_time / num_processes
    avg_turnaround_time = total_turnaround_time / num_processes

    print("\nScheduling Statistics:")
    print(f"Average Waiting Time: {avg_waiting_time:.2f}")
    print(f"Average Response Time: {avg_response_time:.2f}")
    print(f"Average Turnaround Time: {avg_turnaround_time:.2f}")

    # Create and save Gantt chart
    fig = create_gantt_chart(process_history, time)
    plt.savefig('mlfq_gantt_chart.png', bbox_inches='tight')
    plt.close()
    print("\nGantt chart saved as 'mlfq_gantt_chart.png'")


if __name__ == "__main__":
    main()
