class PCB:
    def __init__(self, pid, pc, registers=None, state="NEW"):
        self.pid = pid
        self.pc = pc
        if registers:
            self.registers = registers
        else:
            self.registers = [0] * 12
        self.state = state
        self.states = ['NEW', 'READY', 'RUNNING', 'WAITING', 'TERMINATED']
        self.loader = None
        self.byte_size = None
        self.data_start = None
        self.data_end = None
        self.code_start = None
        self.code_end = None
        self.execution_time = 0
        self.waiting_time = 0
        self.arrival_time = None
        self.start_time = None
        self.end_time = None
        self.file = None
        self.children = []

    def __str__(self):
        return f"PCB(pid={self.pid}, file={self.file}, state={self.state})"
        
    def __repr__(self):
        return f"PCB(pid={self.pid}, file={self.file}, state={self.state})"
    
    def __getitem__(self, key):
        return getattr(self, key)
    
    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __compare__(self, other):
        return self.pid == other.pid
    
    def ready(self):
        self.state = 'READY'
    def running(self): 
        self.state = 'RUNNING'
    def waiting(self):
        self.state = 'WAITING'
    def terminated(self):
        self.state = 'TERMINATED'
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
        child.file = self.file

        self.add_child(child)

        return child
    
    def has_children(self):
        return len(self.children) > 0
    
    def add_child(self, child):
        self.children.append(child)
    
    def get_children(self):
        return self.children