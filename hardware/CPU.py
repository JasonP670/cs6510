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
        self.running = False

        self.ops = {
                # System Calls
                "SWI": self._swi,
                
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
                "LDR": self._ldr,
                "LDRB": self._ldrb,

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

    # def run_pcb(self, pcb, verbose=False):
    #     if verbose: self.verbose = True
    #     self.setPC(pcb['start_line'])
    
    def run_program(self, pcb, verbose=False):
        # pcb['start_time'] = self.system.clock.time
        if verbose: self.verbose = True

        # Restor CPU state from PCB
        self.pcb = pcb
        self.registers = pcb.registers.copy()
        self.registers[self.pc] = pcb.pc

        self.running = True

        while self.running and self.registers[self.pc] < pcb['code_end']:
            instruction = self._fetch()
            opcode, operands = self._decode(instruction)


            if not self._execute(opcode, operands, pcb):
                break

            self.system.clock.increment()
            pcb.execution_time += 1

            if self.registers[self.pc] >= len(self.memory):
                self.system_call(110)
                print("End of memory reached")
                self.verbose = False
                break

    def _execute(self, opcode, operands, pcb):
        if opcode == "SWI":
            return self._swi(operands, pcb)
            

        elif opcode in self.ops:
            self.ops[opcode](operands)
            return True
        
        else:
            self.system_call(103)
            print(f"Unknown opcode: {opcode}")
            self.verbose = False
            self.running = False
            return False

    def _swi(self, operands, pcb):
        swi = int(operands[0])
        if self.verbose:
            print(f"\tSWI\t{swi}")
        if swi == 1: # End of file
            pcb.registers = self.registers.copy()
            pcb.terminated(self.system.clock.time)
            self.system_call(0)
            if self.verbose:
                print("\tEnd of program")
            self.verbose = False
            self.running = False
            return False
        
        elif swi == 2: # Print result (register 0)
            print(f'Result of operations: {self.registers[0]}')

        elif swi == 20: # Wait for IO
            pcb['registers'] = self.registers.copy()
            pcb['pc'] = self.registers[self.pc]

            pcb.waiting()
            if self.verbose:
                print("Waiting for IO")
            self.verbose = False
            self.running = False
            return False
            


            
        elif swi == 10: # FORK
            pcb.registers = self.registers.copy()
            pcb.pc = self.registers[self.pc]
            self.system.fork(pcb)
            # self.registers = pcb.registers.copy()
            self.verbose = False
            self.running = False
            return
        
        elif swi == 11: # EXEC
            self.system.exec(pcb)
            self.verbose = False
            self.running = False
            return
        
        elif swi == 12: # WAIT
            self.system.wait(pcb)
            return True
        
        return True
            

    def _add(self, operands):
        """ 
            ADD R1 R2 R3 
            R1 = R2 + R3
        """
        first_register, second_register, third_register, _, _ = operands
        self.registers[first_register] = self.registers[second_register] + self.registers[third_register]
        if self.verbose:
            print(f"\tADD\t{self.registers[second_register] + self.registers[third_register]} ({third_register}) = {self.registers[second_register]} ({second_register}) + {self.registers[third_register]} ({third_register})\t{self.registers}")

    def _sub(self, operands):
        """
            SUB R1 R2 R3
            R1 = R2 - R3
        """
        first_register, second_register, third_register, _, _ = operands
        self.registers[first_register] = self.registers[second_register] - self.registers[third_register]
        if self.verbose:
            print(f"\tSUB\t{self.registers[second_register] - self.registers[third_register]} ({third_register}) = {self.registers[second_register]} ({second_register}) - {self.registers[third_register]} ({third_register})\t{self.registers}")

    def _mul(self, operands):
        """
            MUL R1 R2 R3
            R1 = R2 * R3
        """
        first_register, second_register, third_register, _, _ = operands
        self.registers[first_register] = self.registers[second_register] * self.registers[third_register]
        if self.verbose:
            print(f"\tMUL\t{self.registers[second_register] * self.registers[third_register]} ({third_register}) = {self.registers[second_register]} ({second_register}) * {self.registers[third_register]} ({third_register})\t{self.registers}")

            
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
            print(f"\tDIV\t{self.registers[second_register] // self.registers[third_register]} ({first_register}) = {self.registers[second_register]} ({second_register}) / {self.registers[third_register]} ({third_register})\t{self.registers}")


    def _mov(self, operands):
        """
            Move data from one register to another
            MOV R1 R2
            R1 <= R2
        """
        first_register, second_register, *_= operands
        self.registers[first_register] = self.registers[second_register]
        if self.verbose:
            print(f"\tMOV\tR{first_register} <= R{second_register}\t\t\t{self.registers}")


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
            print(f"\tMVI\tR{register} <= {immediate_value}\t\t\t{self.registers}")

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
            print(f"\tADR\tR{register} <= {address}\t\t\t{self.registers}")

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

    def _ldr(self, operands):
        """
            Load value from memory location pointed to by one register into another register
            LDR R1 R2
            R1 <= MEM[R2]
        """    
        source_register, addess_register, *rest = operands
        address = self.registers[addess_register]
        value = struct.unpack('<I', self.memory[address:address+4])[0]
        self.registers[source_register] = value
        if self.verbose:
            print(f" - LDR {source_register} <= MEM[{addess_register}]")

    def _ldrb(self, operands):
        """
            Load byte from memory location pointed to by one register into another register
            LDRB R1 R2
            R1 <= byte(MEM[R2])
        """    
        source_register, addess_register, *rest = operands
        address = self.registers[addess_register]
        value = self.memory[address]
        self.registers[source_register] = value
        if self.verbose:
            print(f" - LDRB {source_register} <= MEM[{addess_register}]")

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
        address = struct.unpack('<I', bytes(address_bytes))[0] + self.pcb.loader
        
        if self.registers[self.z] == 0:
            self.setPC(address)
            if self.verbose:
                print(f"\tBEQ address: {address}")

    def _cmp(self, operands):
        """
            Compare two registers
        """
        first_register, second_register, *_ = operands
        val1 = self.registers[first_register]
        val2 = self.registers[second_register]
        val = val1 - val2
        self.registers[self.z] = val

    def _and(self, operands):
        """
            AND R1 R2
            RZ = R1 & R2
        """
        first_register, second_register, third_register, _, _ = operands
        val2 = self.registers[second_register]
        val3 = self.registers[third_register]
        val = val2 & val3
        self.registers[first_register] = val
        if self.verbose:
            print(f" - AND {self.registers[second_register] & self.registers[third_register]} ({third_register}) = {self.registers[second_register]} ({second_register}) & {self.registers[third_register]} ({third_register})")

    def _orr(self, operands):
        """
            ORR R1 R2
            RZ = R1 | R2
        """
        first_register, second_register, *rest = operands
        val1 = self.registers[first_register]
        val2 = self.registers[second_register]
        val = val1 | val2
        self.registers[self.z] = self.registers[first_register] | self.registers[second_register]
        if self.verbose:
            print(f" - ORR {self.registers[self.z]} = {self.registers[first_register]} ({second_register}) | {self.registers[second_register]} ({second_register})")

    def _eor(self, operands):
        """
            EOR R1 R2
            RZ = R1 ^ R2
        """
        first_register, second_register, *rest = operands
        val1 = self.registers[first_register]
        val2 = self.registers[second_register]
        val = val1 ^ val2
        self.registers[self.z] = val
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


