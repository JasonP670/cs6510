class Queue:
    def __init__(self, quantum=4):
        self.processes = []
        self.quantum = quantum

    def __len__(self):
        return len(self.processes)
    
    def add_process(self, pcb):
        self.processes.append(pcb)
    
    def get_process(self):
        return self.processes.pop(0)
    
    def is_empty(self):
        return len(self.processes) == 0
    

    def get_quantum(self):
        return self.quantum    

    def set_quantum(self, quantum):
        self.quantum = quantum

    def reset(self):
        self.processes = []
        self.quantum = 1000000