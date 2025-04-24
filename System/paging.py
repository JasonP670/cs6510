class PageTableEntry:
    def __init__(self, frame=None, valid=False, reference=False, dirty=False):
        self.frame = frame
        self.valid = valid
        self.reference = reference
        self.dirty = dirty
        self.last_access_time = None