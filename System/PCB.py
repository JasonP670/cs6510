from constants import PCBState

class PCB:
    """
    Process Control Block (PCB) class to manage process information.
    Each PCB contains information about the process's state, registers,
    memory management, metrics, and child processes.
    """
    def __init__(self, pid, pc, registers=None, state=PCBState.NEW):
        self.pid = pid
        self.file = None

        # Registers
        self.pc = pc
        if registers:
            self.registers = registers
        else:
            self.registers = [0] * 12

        # States
        self.state = state

        # memory management
        self.page_table = {}
        self.resident_pages = set()
        self.max_resident_pages = None

        # Code Sections
        self.loader = None
        self.byte_size = None
        self.data_start = None
        self.data_end = None
        self.code_start = None
        self.code_end = None

        # Metrics
        self.arrival_time = None
        self.start_time = None
        self.end_time = None
        self.waiting_time = 0
        self.execution_time = 0
        self.response_time = None
        self.turnaround_time = None

        # Children
        self.children = []

        self.queue_level = 1
        self.run_count = 0
        self.preempt_count = 0

        self.CPU_code = None

    def __str__(self):
        return f"PCB(pid={self.pid}, file={self.file}, state={self.state.name})"
        
    def __repr__(self):
        return f"PCB(pid={self.pid}, file={self.file}, state={self.state.name})"
    
    def __getitem__(self, key):
        return getattr(self, key)
    
    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __compare__(self, other):
        return self.pid == other.pid
    
    def ready(self, time):
        """
        Set the PCB state to READY and update the waiting time.
        If the PCB is being moved to the ready queue for the first time,
        set the start time and calculate the waiting time.
        """
        self.state = PCBState.READY
        if self.start_time == None:
            self.start_time = time
            self.waiting_time = time - self.arrival_time

    def running(self):
        """
        Set the PCB state to RUNNING and update the response time.
        If the PCB is being moved to the running state for the first time,
        set the start time and calculate the response time.
        """ 
        self.state = PCBState.RUNNING
        if self.response_time == None:
            self.response_time = self.start_time - self.arrival_time

    def waiting(self):
        """
        Set the PCB state to WAITING.
        """
        self.state = PCBState.WAITING

    def terminated(self, time):
        """
        Set the PCB state to TERMINATED and update the end time, turnaround time and waiting time
        """
        self.state = PCBState.TERMINATED
        self.end_time = time
        self.turnaround_time = self.end_time - self.arrival_time
        self.waiting_time = self.turnaround_time - self.execution_time

    def set_arrival_time(self, time):
        self.arrival_time = time

    def get_pc(self):
        return self.registers[11]
   
    def make_child(self, pid, pc):
        """
        Create a child PCB with the same state and registers as the parent.
        The child PCB will have a new PID and program counter (PC).
        """
        child = PCB(pid, pc, self.registers.copy(), self.state)
        child.loader = self.loader
        child.byte_size = self.byte_size
        child.data_start = self.data_start
        child.data_end = self.data_end
        child.code_start = self.code_start
        child.code_end = self.code_end
        child.file = self.file + " (child)"

        self.add_child(child)

        return child
    
    def has_children(self):
        return len(self.children) > 0
    
    def add_child(self, child):
        self.children.append(child)
    
    def get_children(self):
        return self.children
    
    def update(self, program_info):
        """
        Update the PCB with new program information.
        This includes the loader, byte size, data start and end addresses,
        and code start and end addresses.
        """
        self.loader = program_info['loader']
        self.byte_size = program_info['byte_size']
        self.data_start = program_info['data_start']
        self.data_end = program_info['data_end']
        self.code_start = program_info['code_start']
        self.code_end = program_info['code_end']