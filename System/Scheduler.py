import random
from constants import PCBState

class Scheduler:
    def __init__(self, system):
        self.system = system
        self.scheduling_algorithms = ['FCFS', 'SJF', 'RR', 'Priority']
        self.scheduling_algorithm = 'FCFS'


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
                pcb = self.schedule_job()
                self.handle_process_state(pcb)
                if self.system.verbose:
                    self.system.display_state_table()
            else:
                # If no job is ready increment clock
                self.system.clock += 1
                self.system.print("No jobs ready to run")
        self.print_metrics(start_time)
        

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
                    self.system.ready_queue.append(self.system.job_queue.pop(i)) # move job from job queue to ready queue
                else:
                    self.system.print(f"Error loading {pcb} to memory")
                    return None
            else:
                i += 1
        

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
                # self.system.handle_free_memory(pcb)
                self.system.terminated_queue.append(pcb)
            elif pcb.state == PCBState.WAITING:
                wait_until = self.system.clock.time + random.randint(1, 50)
                pcb.wait_until = wait_until
                self.system.print(f"{pcb} waiting until {wait_until}")
                self.system.io_queue.append(pcb)
            elif pcb.state == PCBState.READY:
                self.system.ready_queue.append(pcb)
            else:
                self.system.print(f"Error: Invalid state {pcb.state} for {pcb}")
            
    def print_time(self):
        """ Print the current time."""
        print(f"==================== Clock: {self.system.clock.time} ====================")

    def jobs_in_ready_queue(self):
        """ Check if there are jobs in the ready queue."""
        return self.system.ready_queue
    
    def jobs_in_any_queue(self):
        """ Check if there are jobs in the system."""
        return self.system.job_queue or self.system.ready_queue or self.system.io_queue

    def check_io_complete(self):
        for i, pcb in enumerate(self.system.io_queue):
            if self.system.clock.time >= pcb.wait_until:
                self.system.io_queue.pop(i)
                self.system.ready_queue.append(pcb)
                self.system.print(f"IO complete for {pcb}")

    def print_metrics(self, start_time):
        end_time = self.system.clock.time
        n_jobs = len(self.system.terminated_queue)
        total_waiting_time = sum([pcb.waiting_time for pcb in self.system.terminated_queue])
        average_waiting_time = total_waiting_time / n_jobs
        print(f"\n{n_jobs} jobs completed in {end_time - start_time} time units (start: {start_time}, end: {end_time})\nThroughput: {n_jobs / (end_time - start_time)}\nAverage waiting time: {average_waiting_time}")
