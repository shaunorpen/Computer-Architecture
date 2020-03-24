"""CPU functionality."""

import sys

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.running = True

        self.ram = [0] * 256    # 256 bytes of memory
        self.reg = [0] * 8      # 8 general-purpose registers
        self.pc = 0             # program counter initialised to zero

        self.instructions = dict()
        self.instructions[0b00000001] = 'HLT'
        self.instructions[0b10000010] = 'LDI'
        self.instructions[0b10100010] = 'MUL'
        self.instructions[0b01000111] = 'PRN'
        
        self.branch_table = dict()

        self.branch_table['LDI'] = lambda operand_a, operand_b, _: self.reg_write(operand_a, operand_b)
        self.branch_table['MUL'] = lambda operand_a, operand_b, instruction: self.alu(instruction, operand_a, operand_b)
        self.branch_table['PRN'] = lambda operand_a, _1, _2: print(self.reg_read(operand_a))

    def ram_read(self, address):
        return self.ram[address]

    def ram_write(self, address, value):
        self.ram[address] = value

    def reg_read(self, address):
        return self.reg[address]

    def reg_write(self, address, value):
        self.reg[address] = value

    def load(self):
        """Load a program into memory."""

        address = 0

        program = list()

        with open("/Users/shaunorpen/Lambda/ls8/ls8/examples/mult.ls8") as f:
            for line in f:
                line_values = line.split("#")
                program.append(int(line_values[0].strip(), 2))

        for instruction in program:
            self.ram[address] = instruction
            address += 1

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        elif op == 0b0010:
            self.reg[reg_a] *= self.reg[reg_b]
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

    def run(self):
        """Run the CPU."""
        while self.running == True:
            # Read next instruction from memory address in PC and store it in the instruction register
            ir = self.ram_read(self.pc)
            # Decode the value stored in the instruction register
            decoded_instruction = self.instructions[ir]
            # Find the number of operands
            num_operands = ir >> 6
            # For ALU operations find the instruction
            instruction = ir & 0b00001111
            # Read the next two byte values and store them in operand_a and operand_b
            operand_a = self.ram_read(self.pc + 1)
            operand_b = self.ram_read(self.pc + 2)
            # Halt
            if decoded_instruction == 'HLT':
                self.running = False
            else:
                # Execute the instruction
                self.branch_table[decoded_instruction](operand_a, operand_b, instruction)
                # Update the PC to point to the next instruction
                self.pc += (1 + num_operands)
                # Loop
                self.run()

        sys.exit()