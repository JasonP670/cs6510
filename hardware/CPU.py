from constants import instructions
import struct


class CPU:
    def __init__(self, memory, system):
        self.memory = memory
        self.system = system
        num_registers = 12
        self.registers = [0 for _ in range(num_registers)]
        self.sp = 6  # Stack Pointer
        self.fp = 7  # Frame Pointer
        self.sl = 8  # Stack Limit
        self.z  = 9  # Zero Flag
        self.sb = 10 # Status Byte
        self.pc = 11 # Program Counter
        self.verbose = False
        self.ops = {
                # Arithmetic
                "ADD": self._add,
                "SUB": self._sub,
                "MUL": self._mul,
                "DIV": self._div,

                # MOVE Data
                "MOV": self._mov,
                "MVI": self._mvi,
                "STR": self._str,
                "ADR": self._adr,
                "STRB": self._strb,

                # Branching
                "B": self._b,
                "BL": self._bl,
                "BX": self._bx,
                "BNE": self._bne,
                "BGT": self._bgt,
                "BLT": self._blt,
                "BEQ": self._beq,

                # Logical
                "CMP": self._cmp,
                "AND": self._and,
                "ORR": self._orr,
                "EOR": self._eor,

            }
        
    def system_call(self, code):
        self.system.system_code(code)

    def run_pcb(self, pcb, verbose=False):
        if verbose: self.verbose = True
        self.setPC(pcb['start_line'])
    
    def run_program(self, pcb, verbose=False):
        if verbose: self.verbose = True
        code_start = pcb['code_start']
        code_end = pcb['code_end']
        self.registers[self.pc] = code_start
        running = True
        while running and self.registers[self.pc] < code_end:
            instruction = self._fetch()
            opcode, operands = self._decode(instruction)

            if opcode == "SWI":
                self._swi(operands)
                self.verbose = False
                break

            if opcode in self.ops:
                self.ops[opcode](operands)
                if self.verbose:
                    print(self.registers)
            else:
                self.system_call(103)
                print(f"Unknown opcode: {opcode}")
                self.verbose = False
                break

            if self.registers[self.pc] >= len(self.memory):
                self.system_call(110)
                print("End of memory reached")
                self.verbose = False
                break

    def _swi(self, operands):
        self.system_call(0)
        print("End of program")
        return None

    def _add(self, operands):
        """ 
            ADD R1 R2 R3 
            R1 = R2 + R3
        """
        first_register, second_register, third_register, _, _ = operands
        self.registers[first_register] = self.registers[second_register] + self.registers[third_register]
        if self.verbose:
            print(f" - ADD {self.registers[second_register] + self.registers[third_register]} ({third_register}) = {self.registers[second_register]} ({second_register}) + {self.registers[third_register]} ({third_register})")

    def _sub(self, operands):
        """
            SUB R1 R2 R3
            R1 = R2 - R3
        """
        first_register, second_register, third_register, _, _ = operands
        self.registers[first_register] = self.registers[second_register] - self.registers[third_register]
        if self.verbose:
            print(f" - SUB {self.registers[second_register] - self.registers[third_register]} ({third_register}) = {self.registers[second_register]} ({second_register}) - {self.registers[third_register]} ({third_register})")

    def _mul(self, operands):
        """
            MUL R1 R2 R3
            R1 = R2 * R3
        """
        first_register, second_register, third_register, _, _ = operands
        self.registers[first_register] = self.registers[second_register] * self.registers[third_register]
        if self.verbose:
            print(f" - MUL {self.registers[second_register] * self.registers[third_register]} ({third_register}) = {self.registers[second_register]} ({second_register}) * {self.registers[third_register]} ({third_register})")

            
    def _div(self, operands):
        """
            DIV R1 R2 R3
            R1 = R2 / R3
        """

        first_register, second_register, third_register, _, _ = operands
        if self.registers[third_register] == 0:
            self.system_call(104)
            print("Division by zero")
            return None
        
        self.registers[first_register] = self.registers[second_register] // self.registers[third_register]
        if self.verbose:
            print(f" - DIV {self.registers[second_register] // self.registers[third_register]} ({first_register}) = {self.registers[second_register]} ({second_register}) / {self.registers[third_register]} ({third_register})")


    def _mov(self, operands):
        """
            Move data from one register to another
            MOV R1 R2
            R1 <= R2
        """
        first_register, second_register, *_= operands
        self.registers[first_register] = self.registers[second_register]
        if self.verbose:
            print(f" - MOV {first_register} <= {second_register}")


    def _mvi(self, operands):
        """
            Load register with immediate value
            MVI R1 10
            R1 <= 10
        """
        register = operands[0]
        immediate_value_bytes = operands[1:5]
        immediate_value = struct.unpack('<I', bytes(immediate_value_bytes))[0]
        self.registers[register] = immediate_value
        if self.verbose:
            print(f" - MVI {register} <= {immediate_value}")

    def _adr(self, operands):
        """
            Load register with address
            ADR R1 0x1000
            R1 <= 0x1000
        """
        register = operands[0]
        address_bytes = operands[1:5]
        address = struct.unpack('<I', bytes(address_bytes))[0]
        self.registers[register] = address
        if self.verbose:
            print(f" - ADR {register} <= {address}")

    def _str(self, operands):
        """
            Store value from one register into memory location 
            pointed to by another register
            STR R1 R2
            MEM[R2] <= R1
        """    
        source_register, addess_register, *rest = operands
        address = self.registers[addess_register]
        value = self.registers[source_register]
        self.memory[address:address+4] = struct.pack('<I', value)
        if self.verbose:
            print(f" - STR {source_register} <= MEM[{addess_register}]")

    def _strb(self, operands):
        """
            Store byte from one register into memory location 
            pointed to by another register
            STRB R1 R2
            MEM[R2] <= byte(memory[R1])
        """    
        source_register, addess_register, *rest = operands
        address = self.registers[addess_register]
        value = self.memory[self.registers[source_register]]
        self.memory[address] = value & 0xFF
        if self.verbose:
            print(f" - STRB {source_register} <= MEM[{addess_register}]")

    def _b(self, operands):
        """
            Branch to address
        """
        address_bytes = operands[0:4]
        address = struct.unpack('<I', bytes(address_bytes))[0]
        self.setPC(address)
        if self.verbose:
            print(f" - B {address}")
    
    def _bl(self, operands):
        """
            Branch to address and link
        """
        address_bytes = operands[0:4]
        address = struct.unpack('<I', bytes(address_bytes))[0]
        pc = self.registers[self.pc]
        self.setPC(address)
        self.registers[5] = pc
        if self.verbose:
            print(f" - BL {address}")

    def _bx(self, operands):
        """
            Branch to address in register
        """
        register = operands[0]
        address = self.registers[register]
        self.setPC(address)
        if self.verbose:
            print(f" - BX {register}")

    def _bne(self, operands):
        """
            Jump to label if Z register is not zero
        """
        address_bytes = operands[0:4]
        address = struct.unpack('<I', bytes(address_bytes))[0]
        is_not_zero = self.registers[self.z] != 0
        if is_not_zero:
            self.setPC(address)
            if self.verbose:
                print(f" - BNE {address}")

    def _bgt(self, operands):
        """
            Jump to label if Z register is greater than zero
        """
        address_bytes = operands[0:4]
        address = struct.unpack('<I', bytes(address_bytes))[0]
        if self.registers[self.z] > 0:
            self.setPC(address)
            if self.verbose:
                print(f" - BGT {address}")

    def _blt(self, operands):
        """
            Jump to label if Z register is less than zero
        """
        address_bytes = operands[0:4]
        address = struct.unpack('<I', bytes(address_bytes))[0]
        if self.registers[self.z] < 0:
            self.setPC(address)
            if self.verbose:
                print(f" - BLT {address}")

    def _beq(self, operands):
        """
            Jump to label if Z register is equal to zero
        """
        address_bytes = operands[0:4]
        address = struct.unpack('<I', bytes(address_bytes))[0]
        if self.registers[self.z] == 0:
            self.setPC(address)
            if self.verbose:
                print(f" - BEQ {address}")

    def _cmp(self, operands):
        """
            Compare two registers
        """
        first_register, second_register, *_ = operands
        self.registers[self.z] = self.registers[first_register] - self.registers[second_register]

    def _and(self, operands):
        """
            AND R1 R2
            RZ = R1 & R2
        """
        first_register, second_register, third_register, _, _ = operands
        self.registers[first_register] = self.registers[second_register] & self.registers[third_register]
        if self.verbose:
            print(f" - AND {self.registers[second_register] & self.registers[third_register]} ({third_register}) = {self.registers[second_register]} ({second_register}) & {self.registers[third_register]} ({third_register})")

    def _orr(self, operands):
        """
            ORR R1 R2
            RZ = R1 | R2
        """
        first_register, second_register, *rest = operands
        self.registers[self.z] = self.registers[first_register] | self.registers[second_register]
        if self.verbose:
            print(f" - ORR {self.registers[self.z]} = {self.registers[first_register]} ({second_register}) | {self.registers[second_register]} ({second_register})")

    def _eor(self, operands):
        """
            EOR R1 R2
            RZ = R1 ^ R2
        """
        first_register, second_register, *rest = operands
        self.registers[self.z] = self.registers[first_register] ^ self.registers[second_register]
        if self.verbose:
            print(f" - EOR {self.registers[self.z]} = {self.registers[first_register]} ({second_register}) ^ {self.registers[second_register]} ({second_register})")
            
    def _decode(self, instruction):
        """
            Decode instruction into opcode and operands
        """
        opcode = instructions[instruction[0]]
        operands = instruction[1:]
        return opcode, operands

    
    
    def _fetch(self):
        """
            Fetch the next instruction
        """
        pc = self.registers[self.pc]
        instruction = self.memory[pc:pc+6]
        self.registers[self.pc] += 6
        return instruction
    
    def setPC(self, value):
        self.registers[self.pc] = value
    
    
    def __str__(self):
        return str(self.registers)


