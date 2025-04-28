from hardware.Memory import Memory
from struct import unpack
from constants import PCBState
from .paging import PageTableEntry

class MemoryManager:
    """
    Memory Manager for the system. Handles loading programs into memory,
    translating virtual addresses to physical addresses, and managing memory allocation.
    """

    def __init__(self, system, size):
        self.memory = Memory(size)
        self.system = system
        self.memory_map = []

        # Initial page size 4 lines of code, can be changed by 
        # set_page_size() method
        self.page_size = 6 * 4 # 24 bytes (4 instructions of 6 bytes each)

        # Initial page limit for each process
        # This can be changed by set_page_limit() method
        self.default_page_limit = 3

        # Number of frames in memory
        self.num_frames = self.memory.size // self.page_size
        
        # List of free frames in memory
        # This is used to keep track of which frames are available for allocation
        self.free_frames = list(range(self.num_frames))

        # Dictionary to store loaded programs
        # The key is the process ID (PID) and the value is the program data
        # This allows for easy access to the program data when needed
        # Simulates our hard disk
        self.programs = {}

        # Track number of page faults
        self.page_faults = 0

    def prepare_program(self, filepath):
        """Validate program file and memory availability before loading."""

        if not filepath:
            return self.system_code(103, "Please specify the file path.")
                
        try:
            with open(filepath, 'rb') as f:
                # Unpack header, which consists of 3 integers (12 bytes)
                byte_size, pc, loader = self._read_header(f)
                
                if not self._is_valid_loader(loader, byte_size, filepath):
                    return None
                
                return {
                    'filepath': filepath,
                    'byte_size': byte_size,
                    'loader': loader,
                    'pc': pc,
                    'code_start': pc,
                    'code_end': loader + byte_size - 1,
                    'data_start': loader,
                    'data_end': pc - 1
                }

        except FileNotFoundError:
            self.system_code(109, f"File not found: {filepath}")
            return None
        except Exception as e:
            self.system_code(100)
            print("An error occurred while loading the file.")
            print(e)
            return None
        
    def _read_header(self, f):
        header = f.read(12)
        byte_size, pc, loader = unpack('III', header) 
        return byte_size, pc, loader
    
    def _is_valid_loader(self, loader, byte_size, filepath):
        """ Validate loader address and program size. """
        if byte_size <= 0:
            self.system_code(101, f"Invalid program size: {byte_size} bytes.", filepath)
            return False
        if byte_size > self.memory.size:
            self.system_code(102, f"Program size {byte_size} exceeds memory size {self.memory.size}.", filepath)
            return False

                
        return True
    
    def allocate_memory(self, pcb):
        """ Allocate memory if available and update memory map. """
        start = pcb.loader
        end = start + pcb.byte_size
        if self.check_memory_available(pcb):
            self.memory_map.append({'start': start, 'end': end, 'pcb': pcb})
            return True
        return False
    

    def load_to_memory(self, pcb):
        """
        Loads a program into main memory from its associated file.

        This method reads the binary contents of a program file, skipping the initial
        12 bytes of the header, and stores the program's content into memory mapped by
        the process ID (PID). It also initializes the process's page table, calculates
        the number of pages needed, and sets memory management properties like the maximum 
        number of resident pages allowed.

        Args:
            pcb (PCB): The Process Control Block containing metadata about the program,
                    including file path, byte size, and PID.

        Returns:
            bool or None: Returns True if the program is successfully loaded;
                        returns None if an error occurs during loading.

        Raises:
            None: Any file-related exceptions are caught and handled internally.
        """
        try:
            with open(pcb.file, 'rb') as f:
                # Skip header
                f.seek(12) 

                # Store program in memory
                self.programs[pcb.pid] = f.read(pcb.byte_size) 
        
        except Exception as e:
            self.system_code(100, f"Error loading {pcb['file']}: {e}")
            return None
        
        # Reset page table
        pcb.page_table = {} 
        
        # Calculate number of pages
        pcb.num_pages = (pcb.byte_size + self.page_size -1) // self.page_size 

        # Set max resident pages
        pcb.max_resident_pages = self.default_page_limit 
        
        # Initialize resident pages set
        pcb.resident_pages = set() 
        self.system.print(f"Program '{pcb.file}' prepared with {pcb.num_pages} pages.")
        return True
        
    def load_page(self, pcb, page_number):
        """
        Loads a specific page of a program into main memory.

        If the page is not already resident, this method handles loading it from the 
        stored program into an available memory frame. It enforces memory management rules 
        such as the maximum number of resident pages per process and triggers page eviction
        if necessary. The method also updates the process's page table with the new frame 
        information.

        Args:
            pcb (PCB): The Process Control Block associated with the program.
            page_number (int): The logical page number to load.

        Raises:
            MemoryError: If the requested page number exceeds the total number of pages
                        for the program.

        Behavior:
            - Skips loading if the page is already valid and resident.
            - Evicts pages if the process has reached its maximum allowed resident pages.
            - Evicts system-wide pages if there are no free frames.
            - Updates the page table and memory once the page is loaded.
        """
        if page_number >= pcb.num_pages:
            raise MemoryError("Page number out of bounds.")
        
        # Check if page is already loaded
        if page_number in pcb.page_table and pcb.page_table[page_number].valid:
            return
        
        # Check how many pages are currently loaded
        if len(pcb.resident_pages) >= pcb.max_resident_pages:
            self.system.print(f"[LIMIT] PID {pcb.pid} has reached max resident pages ({pcb.max_resident_pages})")
            self.evict_page(pcb)

        # If frame needed, check free frame availability
        if not self.free_frames:
            self.evict_page() 

        # Get a free frame
        frame = self.free_frames.pop(0) 
        
        # Calculate the start and end of the page in the program
        page_start = page_number * self.page_size
        page_end = page_start + self.page_size

        # Load the page from program store
        page_data = self.programs[pcb.pid][page_start:page_end]
        mem_start = frame * self.page_size
        self.memory[mem_start:mem_start + len(page_data)] = page_data


        # update page table
        pcb.page_table[page_number] = PageTableEntry(frame=frame, valid=True, reference=True, dirty=False)
        pcb.resident_pages.add(page_number)
        self.system.print(f"Program '{pcb.file}' loaded page {page_number} -> frame {frame}.")

    def translate(self, pcb, virtual_address):
        """ Translate a virtual address to a physical address. """
        page_number = virtual_address // self.page_size
        offset = virtual_address % self.page_size

        if page_number not in pcb.page_table or pcb.page_table[page_number].valid == False:
            self.page_faults += 1
            self.load_page(pcb, page_number)

        frame = pcb.page_table[page_number].frame
        physical_address = (frame * self.page_size) + offset
        return physical_address
    
    def evict_page(self, target_pcb=None):
        """ Evict a page from memory. """
        if target_pcb: # Max number of pages for this pcb has been reached
            for vp, entry in target_pcb.page_table.items():
                if entry.valid:
                    self.system.print(f"[EVICT] PID {target_pcb.pid} - Page {vp} evicted (limit reached).")

                    # Invalidate page
                    entry.valid = False
                    target_pcb.resident_pages.remove(vp)

                    # free the frame
                    self.free_frames.append(entry.frame)

                    # clear frame info so it's not used again without reload
                    entry.frame = None

                    return
        else:
            # Default behavior - evict any valid page from any process
            for pcb in self.system.process_table().values():
                for vp, entry in pcb.page_table.items():
                    if entry.valid:
                        # Evict the page
                        self.system.print(f"Evicting page {vp} from process {pcb.pid}.")

                        # Invalidate the page
                        entry.valid = False
                        entry.reference = False
                        entry.dirty = False

                        # Free the frame
                        self.free_frames.append(entry.frame)
                        return

    def free_memory(self, pcb):
        """ Free memory and update memory map. """
        start = pcb.loader
        end = start + pcb.byte_size
        self.memory_map = [alloc for alloc in self.memory_map if alloc['pcb'].pid != pcb.pid]
        self.memory[start:end] = [0] * (end - start) # Clear memory
        return True
        # return False
    

    def system_code(self, code, *args):
        self.system.system_code(code, *args)

    def check_memory_available(self, pcb):
        start = pcb.loader
        end = start + pcb.byte_size

        for alloc in self.memory_map:
            alloc_start = alloc['start']
            alloc_end = alloc['end']

            # if (end <= alloc['start'] or start >= alloc['end']):
            if (start < alloc_end) and (alloc_start < end):
                if alloc['pcb'].state == PCBState.TERMINATED:
                    self.free_memory(alloc['pcb'])
                    return True
                else:
                    return False
        return True
    
    def set_page_limit(self, limit):
        if limit <= 0:
            self.system_code(101, "Invalid page limit.")
            return False
        self.default_page_limit = limit
        self.system.print(f"Set maximum resident pages to {limit} for all processes.")

    def get_page_limit(self):
        return self.default_page_limit
    
    def set_page_size(self, size):
        """ Change the page size for memory management. """
        if size <= 0:
            self.system_code(101, "Invalid page size.")
            return False
        
        if any(self.system.job_queue):
            self.system_code(101, "Cannot change page size while processes are loaded.")
            return False
        
        self.page_size = size * 6 # Size in bytes (6 bytes per instruction)
        self.num_frames = self.memory.size // self.page_size
        self.free_frames = list(range(self.num_frames))
        return True
    
    def get_page_size(self):
        """ Get the current page size. """
        return self.page_size

    def system_code(self, code, *args):
        self.system.system_code(code, *args)
