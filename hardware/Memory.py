class Memory:
    """
    A class to represent a memory block.
    The memory is represented as a bytearray, and the size can be specified in bytes, kilobytes, megabytes, or gigabytes.
    The memory is initialized to 1 kilobyte."""
    def __init__(self, size='1K'):
        self.size = self.calculate_size(size)
        self.cols = 6
        self.rows = self.size // self.cols
        self._memory = bytearray(self.size)

    def calculate_size(self, size):
        """
        Calculate the size of the memory in bytes.
        The size can be specified in bytes (B), kilobytes (K), megabytes (M), or gigabytes (G).
        """
        size_int = int(size[:-1])
        size_char = size[-1]

        if size_char == 'B':
            return size_int
        if size_char == 'K':
            return size_int * 1024
        if size_char == 'M':
            return size_int * 1024 * 1024
        if size_char == 'G':
            return size_int * 1024 * 1024 * 1024
        
    def __repr__(self):
        return f"<Memory size={self.size} bytes>"

    def __str__(self):
        """Return a string representation of the memory block."""
        string = '\n'
        l = 0
        for i in range(self.rows):
            if i % 5 == 0:
                _ = ''
            string += f"{l}-{l+5}: "
            l += 6
            for j in range(self.cols):
                index = i * self.cols + j
                if index < len(self._memory):
                    string += f"{self._memory[index]:02X} "
                else:
                    string += "   "
            string += '\n'
        return string
    
    def __getitem__(self, key):
        if isinstance(key, int):
            return self._memory[key]
        elif isinstance(key, slice):
            return self._memory[key]
        else:
            raise TypeError('Tried to get from memory with invalid access type.')
    
    def __setitem__(self, key, value):
        if isinstance(key, int):
            self._memory[key] = value
        elif isinstance(key, slice):
            self._memory[key] = value
        else:
            raise TypeError("Tried to store in memory with invalid access type")

    def __len__(self):
        return len(self._memory)
    
