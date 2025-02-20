from constants import PCBState

class PCB:
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
        # self.states = ['NEW', 'READY', 'RUNNING', 'WAITING', 'TERMINATED']

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
        self.state = PCBState.READY
        if self.start_time == None:
            self.start_time = time
            self.waiting_time = time - self.arrival_time

    def running(self): 
        self.state = PCBState.RUNNING
        if self.response_time == None:
            self.response_time = self.start_time - self.arrival_time

    def waiting(self):
        self.state = PCBState.WAITING

    def terminated(self, time):
        self.state = PCBState.TERMINATED
        self.end_time = time
        self.turnaround_time = self.end_time - self.arrival_time
        self.waiting_time = self.turnaround_time - self.execution_time

    def set_arrival_time(self, time):    
        self.arrival_time = time

    def get_pc(self):
        return self.registers[11]
   
    def make_child(self, pid, pc):
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
        self.loader = program_info['loader']
        self.byte_size = program_info['byte_size']
        self.data_start = program_info['data_start']
        self.data_end = program_info['data_end']
        self.code_start = program_info['code_start']
        self.code_end = program_info['code_end']