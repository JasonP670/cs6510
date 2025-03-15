class Clock:
    def __init__(self, time: int = 0):
        self.time = time

    def __str__(self):
        return str(self.time)
    
    def __iadd__(self, other):
        self.time += other
        return self
    
    def __lt__(self, other):
        return self.time < other
    
    def __le__(self, other):
        return self.time <= other
    
    def __eq__(self, other):
        return self.time == other
    
    def __gt__(self, other):
        return self.time > other
    
    def __ge__(self, other):
        return self.time >= other
    
    def increment(self):
        self.time += 1
        return self
    
    def reset(self):
        self.time = 0