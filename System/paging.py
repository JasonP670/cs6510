class PageTableEntry:
    """
    A class representing a page table entry in a virtual memory system.
    Each entry contains information about a page, including its frame number,
    validity, reference bit, dirty bit, and last access time.
    """
    def __init__(self, frame=None, valid=False, reference=False, dirty=False):
        self.frame = frame
        self.valid = valid
        self.reference = reference
        self.dirty = dirty
        self.last_access_time = None