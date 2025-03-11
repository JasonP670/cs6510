class Queue:
    def __init__(self, quantum=1000000):
        self.processes = []
        self.quantum = quantum

    def add_process(self, process):
        self.processes.append(process)

    def get_next_process(self):
        if self.processes:
            return self.processes.pop(0)

    def set_quantum(self, quantum):
        self.quantum = quantum

    def __len__(self):
        return len(self.processes)