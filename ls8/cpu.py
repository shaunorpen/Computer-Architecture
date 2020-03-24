"""CPU functionality."""

import sys

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256    # 256 bytes of memory
        self.reg = [0] * 8      # 8 general-purpose registers
        self.pc = 0             # program counter initialised to zero

        # Instruction Set
        self.HLT = 0b0001
        self.LDI = 0b0010
        self.PRN = 0b0111

    def ram_read(self, address):
        return self.ram[address]

    def ram_write(self, address, value):
        self.ram[address] = value

    def load(self):
        """Load a program into memory."""

        address = 0

        # For now, we've just hardcoded a program:

        program = [
            # From print8.ls8
            0b10000010, # LDI R0,8
            0b00000000,
            0b00001000,
            0b01000111, # PRN R0
            0b00000000,
            0b00000001, # HLT
        ]

        for instruction in program:
            self.ram[address] = instruction
            address += 1

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        #elif op == "SUB": etc
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def decode(self, instruction):
        # bitshift right six places to get the number of operands
        num_operands = instruction >> 6
        # mask and bitshift right five places to get the alu operation flag
        alu_operation = (instruction & 0b00100000) >> 5
        # mask and bitshift right four places to get the set program counter flag
        set_program_counter = (instruction & 0b00010000) >> 4
        # mask everything but the last four characters to get the cpu instruction code
        cpu_instruction = instruction & 0b00001111
        return (num_operands, alu_operation, set_program_counter, cpu_instruction)

    def run(self):
        """Run the CPU."""
        # Read next instruction from memory address in PC and store it in the instruction register
        ir = self.ram_read(self.pc)
        # Decode the value stored in the instruction register
        (num_operands, alu_operation, set_program_counter, cpu_instruction) = self.decode(ir)
        # Read the next two byte values and store them in operand_a and operand_b
        operand_a = self.ram_read(self.pc + 1)
        operand_b = self.ram_read(self.pc + 2)
        # HLT
        if cpu_instruction == self.HLT:
            sys.exit()
        # LDI
        elif cpu_instruction == self.LDI:
            self.ram_write(operand_a, operand_b)
        # PRN
        elif cpu_instruction == self.PRN:
            print(self.ram_read(operand_a))
        else:
            raise Exception("Unsupported CPU instruction")
        # Update the PC to point to the next instruction
        self.pc += (1 + num_operands)
        # Loop
        self.run()
