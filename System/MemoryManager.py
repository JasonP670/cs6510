from hardware.Memory import Memory
from struct import unpack
from constants import PCBState
from .memory_constants import PAGE_SIZE, NUM_PAGES


class MemoryManager:
    def __init__(self, system, size):
        self.memory = Memory(size)
        self.system = system
        self.memory_map = []

        # Use global constants
        self.page_size = PAGE_SIZE
        self.num_pages = NUM_PAGES

        # allocations:numpy:ndarray  # to swap memory content?

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
        except (IOError, ValueError) as e:
            self.system_code(100)
            print("An error occurred while loading the file.")
            print(e)
            return None

    def _read_header(self, f):
        header = f.read(12)
        byte_size, pc, loader = unpack('III', header)
        pc += loader
        return byte_size, pc, loader

    def _is_valid_loader(self, loader, byte_size, filepath):
        if loader > self.memory.size:
            self.system_code(
                110, f"Loader address {loader} is out of bounds.", filepath)
            return False

        if loader + byte_size > self.memory.size:
            self.system_code(
                102, f"Not enough memory to store program at location {loader}.\nProgram requires {byte_size} bytes.\nMemory has {self.memory.size - loader} bytes available.", filepath)
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
        """ Load program into memory if space is available. """
        if not self.allocate_memory(pcb):
            self.system_code(102, f"Failed to allocate memory for {pcb.file}")
            return None
        try:
            with open(pcb.file, 'rb') as f:
                f.seek(12)  # Skip header
                self.memory[pcb.loader: pcb.loader +
                            pcb.byte_size] = f.read(pcb.byte_size)
                self.system.print(f"Loaded {pcb.file} to memory")
                return True
        except (IOError, ValueError) as e:
            self.system_code(100, f"Error loading {pcb.file}: {e}")
            self.free_memory(pcb)
            return None

    def free_memory(self, pcb):
        """ Free memory and update memory map. """
        start = pcb.loader
        end = start + pcb.byte_size
        self.memory_map = [
            alloc for alloc in self.memory_map if alloc['pcb'].pid != pcb.pid]
        self.memory[start:end] = [0] * (end - start)  # Clear memory
        return True
        # return False

    def translate(self, addr: int, pages: list[int]) -> int:
        """Translate a virtual address to a physical address using the page table."""
        page_number = addr // self.page_size
        offset = addr % self.page_size

        if page_number >= len(pages):
            self.system_code(
                110, f"Page number {page_number} is out of bounds")
            return -1

        physical_page = pages[page_number]
        if physical_page == -1:  # Page not in memory
            self.system_code(111, f"Page {page_number} is not in memory")
            return -1

        return (physical_page * self.page_size) + offset

    def get_range(self, mem_range: tuple, pages: list[int]) -> list:
        """Get data from a range of memory addresses."""
        start, end = mem_range
        if start < 0 or end >= self.memory.size:
            self.system_code(
                110, f"Memory range {start}-{end} is out of bounds")
            return []

        result = []
        for addr in range(start, end + 1):
            physical_addr = self.translate(addr, pages)
            if physical_addr == -1:
                return []
            result.append(self.memory[physical_addr])
        return result

    def set_range(self, mem_range: tuple, data: list, pages: list[int]) -> None:
        """Set data in a range of memory addresses."""
        start, end = mem_range
        if start < 0 or end >= self.memory.size:
            self.system_code(
                110, f"Memory range {start}-{end} is out of bounds")
            return

        if len(data) != (end - start + 1):
            self.system_code(
                112, f"Data length {len(data)} does not match range size {end - start + 1}")
            return

        for i, addr in enumerate(range(start, end + 1)):
            physical_addr = self.translate(addr, pages)
            if physical_addr == -1:
                return
            self.memory[physical_addr] = data[i]

    def get_real_range(self, mem_range: tuple) -> list:
        """Get data directly from physical memory range."""
        start, end = mem_range
        if start < 0 or end >= self.memory.size:
            self.system_code(
                110, f"Memory range {start}-{end} is out of bounds")
            return []
        return self.memory[start:end + 1]

    def get_pages(self, pages: list[int]) -> list:
        """Get the content of specified pages."""
        result = []
        for page in pages:
            if page == -1:  # Page not in memory
                result.append([0] * self.page_size)
            else:
                start = page * self.page_size
                end = start + self.page_size - 1
                result.append(self.get_real_range((start, end)))
        return result

    def set_pages(self, pages: list[int], data: list) -> None:
        """Set the content of specified pages."""
        if len(pages) != len(data):
            self.system_code(
                112, f"Number of pages {len(pages)} does not match data length {len(data)}")
            return

        for page, page_data in zip(pages, data):
            if page == -1:  # Page not in memory
                continue
            if len(page_data) != self.page_size:
                self.system_code(
                    112, f"Page data length {len(page_data)} does not match page size {self.page_size}")
                return

            start = page * self.page_size
            end = start + self.page_size - 1
            self.memory[start:end + 1] = page_data

    def check_memory_available(self, pcb):
        start = pcb.loader
        end = start + pcb.byte_size

        for alloc in self.memory_map:
            alloc_start = alloc['start']
            alloc_end = alloc['end']

            if (start < alloc_end) and (alloc_start < end):
                if alloc['pcb'].state == PCBState.TERMINATED:
                    self.free_memory(alloc['pcb'])
                    return True
                return False
        return True

    def system_code(self, code, *args):
        self.system.system_code(code, *args)
