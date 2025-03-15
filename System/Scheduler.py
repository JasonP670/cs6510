import random
from constants import PCBState
from enum import Enum
import matplotlib.pyplot as plt
import datetime

class SchedulingStrategy(Enum):
    FCFS = 'FCFS'
    RR = 'RR'
    MLFQ = 'MLFQ'

class Scheduler:
    def __init__(self, system):
        self.system = system
        self.scheduling_strategy = SchedulingStrategy.MLFQ
        self.mlfq_index = 0  # Add an index to track the current queue in MLfQ
        self.check_promote_at = 5 # Times to run pcb before promoting/demoting
        self.gantt_chart = []

    def schedule_jobs(self):
        """ Schedule jobs in the system."""
        start_time = self.system.clock.time
        self._sort_ready_queue()

        while self.jobs_in_any_queue(): # If theres programs one of the queues
            self.print_time()
            self.check_new_jobs()
            self.check_io_complete()


            # Run the next job in the ready queue, FCFS
            if self.jobs_in_ready_queue():
                pcb, quantum = self.get_next_job()
                run_start_time = self.system.clock.time
                self.run_process(pcb, quantum)
                run_end_time = self.system.clock.time
                self.add_to_gantt_chart(pcb, run_start_time, run_end_time)                
                self.handle_process_state(pcb)
                if self.system.verbose:
                    self.system.display_state_table()
            else:
                # If no job is ready increment clock
                self.gantt_chart.append((self.system.clock.time, 'IDLE', None))
                self.system.clock += 1
                self.system.print("No jobs ready to run")

        metrics = self.get_metrics(start_time)
        # self.system.print(f"\n{metrics['n_jobs']} jobs completed in {metrics['runtime']} time units (start: {metrics['start_time']}, end: {metrics['end_time']})\nThroughput: {metrics['turnaround']}\nAverage waiting time: {metrics['average_waiting_time']}")

        # self.print_gantt_chart()
        self.plot_gantt_chart()
        return metrics

    def check_new_jobs(self):
        """ Move jobs from job queue to ready queue, if current time is past programs arrival time."""
        i = 0
        while i < len(self.system.job_queue): # Iterate through job queue
            pcb = self.system.job_queue[i]
            if self.system.clock.time < pcb.arrival_time: # Once we find a job that has not arrived yet, break out of loop
                break

            # Ensure memory is available without overlapping with other processes
            if self.system.handle_check_memory_available(pcb):
                if self.system.handle_load_to_memory(pcb):
                    self.system.Q1.add_process(self.system.job_queue.pop(i))
                    # self.system.ready_queue.append(self.system.job_queue.pop(i)) # move job from job queue to ready queue
                else:
                    self.system.print(f"Error loading {pcb} to memory")
                    return None
            else:
                i += 1

    def get_process(self):
        if self.scheduling_strategy == SchedulingStrategy.FCFS:
            return self.system.ready_queue.pop(0)
        
    def run_process(self, pcb, quantum):
        pcb.ready(self.system.clock.time)
        pcb.run_count += 1
        self.system.print(f"\nScheduling {pcb}")
        self.system.run_pcb(pcb, quantum)

    def schedule_job(self):
        """ Schedule the next job in the ready queue."""
        pcb = self.system.ready_queue.pop(0)
        pcb.ready(self.system.clock.time) # mark it as ready
        self.system.print(f"\nScheduling {pcb}")
        self.system.run_pcb(pcb)
        return pcb
        
        
    def _sort_ready_queue(self):
        """ Sort the ready queue by arrival time."""
        self.system.ready_queue.sort(key=lambda x: x.arrival_time)

    def handle_process_state(self, pcb):
        """ Handle the state of the process after running."""
        if pcb:
            if pcb.state == PCBState.TERMINATED:
                self.system.terminated_queue.append(pcb)

            elif pcb.state == PCBState.WAITING:
                if pcb.CPU_code == 21:
                    pcb.wait_until = self.system.clock.time
                    self.system.io_queue.append(pcb)
                    self.system.io_queue.pop()
                    pcb.ready(self.system.clock.time)
                    self.put_process_back(pcb)
                else:
                    wait_until = self.system.clock.time + random.randint(1, 50)
                    pcb.wait_until = wait_until
                    self.system.print(f"{pcb} waiting until {wait_until}")
                    self.system.io_queue.append(pcb)

            elif (pcb.state == PCBState.READY or pcb.state == PCBState.RUNNING):
                self.put_process_back(pcb)

            else:
                self.system.print(f"Error: Invalid state {pcb.state} for {pcb}")
            
    def print_time(self):
        """ Print the current time."""
        self.system.print(f"==================== Clock: {self.system.clock.time} ====================")

    def jobs_in_ready_queue(self):
        """ Check if there are jobs in the ready queue."""
        return (len(self.system.Q1) + 
                len(self.system.Q2) + 
                len(self.system.Q3)) > 0
    
    def jobs_in_any_queue(self):
        """ Check if there are jobs in the system."""
        return (self.jobs_in_ready_queue() or
                (len(self.system.job_queue) + 
                len(self.system.ready_queue) + 
                len(self.system.io_queue)) > 0)

    def check_io_complete(self):
        for i, pcb in enumerate(self.system.io_queue):
            if self.system.clock.time >= pcb.wait_until:
                self.system.io_queue.pop(i)
                self.put_process_back(pcb)
                pcb.ready(self.system.clock.time)
                self.system.print(f"IO complete for {pcb}")

    def get_metrics(self, start_time):
        end_time = self.system.clock.time
        n_jobs = len(self.system.terminated_queue)
        total_waiting_time = sum([pcb.waiting_time for pcb in self.system.terminated_queue])
        total_response_time = sum([pcb.response_time for pcb in self.system.terminated_queue])
        total_turnaround_time = sum([pcb.turnaround_time for pcb in self.system.terminated_queue])
        average_waiting_time = total_waiting_time / n_jobs
        average_response_time = total_response_time / n_jobs
        average_turnaround_time = total_turnaround_time / n_jobs

        return {'n_jobs': n_jobs, 
                'runtime': end_time - start_time, 
                'avg_turnaround': average_turnaround_time,
                'throughput': n_jobs / (end_time - start_time), 
                'avg_wait_time': average_waiting_time,
                'avg_response_time': average_response_time,
                'start_time': start_time,
                'end_time': end_time}
    

    def add_to_gantt_chart(self, pcb, start_time, end_time):
        self.gantt_chart.append((start_time, end_time, pcb.pid, pcb.queue_level))

    def print_gantt_chart(self):
        gantt_string = ''
        for i, (time, pid, queue) in enumerate(self.gantt_chart):
            gantt_string += f"{pid}"
            if i < len(self.gantt_chart) - 1:
                gantt_string += ', '
        print(gantt_string)


    def plot_gantt_chart(self, show=False):
        color_map = {
            'IDLE': '#A0A0A0',
            1: '#4682B4',
            2: '#8FBC8F',
            3: '#D2691E'
        }

        fig, ax = plt.subplots(figsize=(12, 5))
        process_intervals = {}
        process_queues = {}

        for start_time, end_time, pid, queue_level in self.gantt_chart:
            if pid not in process_intervals:
                process_intervals[pid] = []

            # if not process_intervals[pid] or process_intervals[pid][-1][1] != time - 1:
            #     process_intervals[pid].append([time, time])
            process_intervals[pid].append((start_time, end_time, queue_level))


        sorted_processes = ['IDLE'] + sorted([p for p in process_intervals.keys() if p != 'IDLE'])
        process_positions = {pid: i for i, pid in enumerate(sorted_processes)}

        program_size = self.system.terminated_queue[0].file.split('/')[2].split('-')[0]



        ax.set_title(f'Gantt Chart - {self.scheduling_strategy.value} - {program_size} - Q1: {self.system.Q1.quantum}, Q2: {self.system.Q2.quantum}') 
        ax.set_xlabel('Time')
        ax.set_ylabel('Processes')
        ax.set_yticks(range(len(process_positions)))
        ax.set_yticklabels(process_positions.keys())

        

        for pid, intervals in process_intervals.items():
            for start, end, queue in intervals:
                color = color_map.get(queue, color_map['IDLE'])
                ax.barh(process_positions[pid], end - start, left=start, height=0.4, color=color, label=f'Q{queue}')
                

        # Remove duplicate labels and add grid lines
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))  # Remove duplicates
        ax.legend(by_label.values(), by_label.keys())
        plt.grid(axis='x', linestyle='--', alpha=0.6)
        
        current_datetime = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        plt.savefig(f'charts/gantt_charts/{self.scheduling_strategy.value}_{program_size}_{self.system.Q1.quantum}_{self.system.Q2.quantum}.png')
        plt.close('all')
        if show:
            plt.show()


    def get_next_job(self):
        """ Get the next job in the ready queue."""
        if (self.scheduling_strategy == SchedulingStrategy.FCFS or 
            self.scheduling_strategy == SchedulingStrategy.RR):
            return self.system.Q1.get_process(), self.system.Q1.get_quantum()
        
        elif self.scheduling_strategy == SchedulingStrategy.MLFQ:
            queues = [self.system.Q1, self.system.Q2, self.system.Q3]
            for _ in range(len(queues)): # Loop through all queues, getting one process from each
                queue = queues[self.mlfq_index]
                self.mlfq_index = (self.mlfq_index + 1) % len(queues)
                if len(queue) > 0:
                    return queue.get_process(), queue.get_quantum()
        else:
            raise ValueError(f"Invalid scheduling strategy {self.scheduling_strategy}")

    def set_strategy(self, strategy):
        if len(self.system.Q1) > 0 or len(self.system.Q2) > 0 or len(self.system.Q3) > 0:
            raise ValueError("Cannot change scheduling strategy while jobs are in the system")
        
        strategy = strategy.upper()
        
        
        if strategy in SchedulingStrategy._value2member_map_:
            if strategy == SchedulingStrategy.FCFS.value:
                self.system.Q1.set_quantum(1000000)
                self.scheduling_strategy = SchedulingStrategy.FCFS
            elif strategy == SchedulingStrategy.RR.value:
                self.system.Q1.set_quantum(10)
                self.scheduling_strategy = SchedulingStrategy.RR
            elif strategy == SchedulingStrategy.MLFQ.value:
                self.system.Q1.set_quantum(8)
                self.system.Q2.set_quantum(16)
                self.scheduling_strategy = SchedulingStrategy.MLFQ
            
            self.system.print(f"Setting scheduling strategy to {strategy}")
            return True
        
        
        raise ValueError(f"Invalid scheduling strategy {strategy}")
    
    def put_process_back(self, pcb):
        if self.scheduling_strategy == SchedulingStrategy.MLFQ:
            self.check_for_promotion(pcb)

        if pcb.queue_level == 1:
            self.system.Q1.add_process(pcb)
        elif pcb.queue_level == 2:
            self.system.Q2.add_process(pcb)
        elif pcb.queue_level == 3:
            self.system.Q3.add_process(pcb)
        else:
            raise ValueError(f"Invalid queue level {pcb.queue_level}")
        
    def check_for_promotion(self, pcb):
        if pcb.run_count == self.check_promote_at:
            preemption_ratio = pcb.preempt_count / pcb.run_count

            if preemption_ratio > 0.2: # If preempt more than 80% of the time, promote Q1 -> Q2 -> Q3
                self.promote(pcb) 
            elif preemption_ratio < 0.2:
                self.demote(pcb)
            # else:
            #     print("Something went wrong in put_process_back, preemption ratio: ", preemption_ratio)

            pcb.preempt_count = 0
            pcb.run_count = 0
        
    def promote(self, pcb):
        if pcb.queue_level == 1:
            pcb.queue_level = 2
            self.system.print(f"Promoting {pcb} to Q2")
        elif pcb.queue_level == 2:
            pcb.queue_level = 3
            self.system.print(f"Promoting {pcb} to Q3")
        elif pcb.queue_level == 3:
            pcb.queue_level = 3
        else:
            raise ValueError(f"Invalid queue level {pcb.queue_level}")
        
    def demote(self, pcb):
        if pcb.queue_level == 1:
            pcb.queue_level = 1
        elif pcb.queue_level == 2:
            pcb.queue_level = 1
            self.system.print(f"Demoting {pcb} to Q1")
        elif pcb.queue_level == 3:
            pcb.queue_level = 2
        else:
            raise ValueError(f"Invalid queue level {pcb.queue_level}")
    

