"""CPU functionality."""

import sys

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.running = True

        self.ram = [0] * 256    # 256 bytes of memory
        self.reg = [0] * 8      # 8 general-purpose registers
        self.pc = 0             # program counter initialised to point to memory address zero
        self.sp = int('F4', 16) # stack pointer initialised to point to memory address F4
        self.update_pc = True   # flag to determine whether to update the pc or not

        self.instructions = dict()
        self.instructions[0b01010000] = 'CALL'
        self.instructions[0b00000001] = 'HLT'
        self.instructions[0b10000010] = 'LDI'
        self.instructions[0b10100010] = 'MUL'
        self.instructions[0b01000110] = 'POP'
        self.instructions[0b01000111] = 'PRN'
        self.instructions[0b01000101] = 'PUSH'
        self.instructions[0b00010001] = 'RET'
        self.instructions[0b10100000] = 'ADD'
        
        self.branch_table = dict()
        """
        ALU ops
        ADD  10100000 00000aaa 00000bbb
        SUB  10100001 00000aaa 00000bbb
        MUL  10100010 00000aaa 00000bbb
        DIV  10100011 00000aaa 00000bbb
        MOD  10100100 00000aaa 00000bbb

        INC  01100101 00000rrr
        DEC  01100110 00000rrr

        CMP  10100111 00000aaa 00000bbb

        AND  10101000 00000aaa 00000bbb
        NOT  01101001 00000rrr
        OR   10101010 00000aaa 00000bbb
        XOR  10101011 00000aaa 00000bbb
        SHL  10101100 00000aaa 00000bbb
        SHR  10101101 00000aaa 00000bbb
        """
        self.branch_table['MUL'] = self.mul
        self.branch_table['ADD'] = self.add
        """
        PC Mutators
        CALL 01010000 00000rrr
        RET  00010001

        INT  01010010 00000rrr
        IRET 00010011

        JMP  01010100 00000rrr
        JEQ  01010101 00000rrr
        JNE  01010110 00000rrr
        JGT  01010111 00000rrr
        JLT  01011000 00000rrr
        JLE  01011001 00000rrr
        JGE  01011010 00000rrr
        """
        self.branch_table['CALL'] = self.call
        self.branch_table['RET'] = self.ret
        """
        Other
        NOP  00000000

        HLT  00000001 

        LDI  10000010 00000rrr iiiiiiii

        LD   10000011 00000aaa 00000bbb
        ST   10000100 00000aaa 00000bbb

        PUSH 01000101 00000rrr
        POP  01000110 00000rrr

        PRN  01000111 00000rrr
        PRA  01001000 00000rrr
        """
        self.branch_table['HLT'] = self.hlt
        self.branch_table['LDI'] = self.ldi
        self.branch_table['PUSH'] = self.push
        self.branch_table['POP'] = self.pop
        self.branch_table['PRN'] = self.prn

    def add(self, operand_a, operand_b):
        self.alu('ADD', operand_a, operand_b)

    def mul(self, operand_a, operand_b):
        self.alu('MUL', operand_a, operand_b)
    
    def hlt(self):
        self.running = False

    def ldi(self, operand_a, operand_b):
        self.reg[operand_a] = operand_b

    def push(self, reg_address):
        """
        Push the value in the given register on the stack.

        1. Decrement the `SP`.
        2. Copy the value in the given register to the address pointed to by
        `SP`.

        Machine code:
        
        01000101 00000rrr
        45 0r
        
        """
        self.sp -= 1
        self.ram[self.sp] = self.reg[reg_address]

    def pop(self, reg_address):
        """
        Pop the value at the top of the stack into the given register.

        1. Copy the value from the address pointed to by `SP` to the given register.
        2. Increment `SP`.

        Machine code:
        
        01000110 00000rrr
        46 0r
        
        """
        self.reg[reg_address] = self.ram[self.sp]
        self.sp += 1

    def call(self, reg_address):
        """
        Calls a subroutine (function) at the address stored in the register.

        1. The address of the ***instruction*** _directly after_ `CALL` is
        pushed onto the stack. This allows us to return to where we left off when the subroutine finishes executing.
        2. The PC is set to the address stored in the given register. We jump to that location in RAM and execute the first instruction in the subroutine. The PC can move forward or backwards from its current location.

        Machine code:
        ```
        01010000 00000rrr
        50 0r
        ```
        """
        # decrement the stack pointer
        self.sp -= 1
        # copy the value at memory address program counter + 2 to the address pointed at by the stack pointer
        self.ram[self.sp] = self.pc + 2
        # set the pc to the address stored in the given register
        self.pc = self.reg[reg_address]
        # set the update_pc flag as false
        self.update_pc = False

    def ret(self):
        """
        Return from subroutine.

        Pop the value from the top of the stack and store it in the `PC`.

        Machine Code:
        ```
        00010001
        11
        ```
        """
        # copy the value from the top of the stack into the pc
        self.pc = self.ram[self.sp]
        # increment the stack pointer
        self.sp += 1
        # set the update_pc flag as false
        self.update_pc = False

    def prn(self, operand_a):
        print(self.reg[operand_a])

    def ram_read(self, address):
        return self.ram[address]

    def ram_write(self, address, value):
        self.ram[address] = value

    def load(self):
        """Load a program into memory."""

        address = 0

        program = list()

        with open("/Users/shaunorpen/Lambda/ls8/ls8/examples/call.ls8") as f:
            for line in f:
                line_values = line.split("#")
                instruction_string = line_values[0]
                if len(instruction_string) > 0:
                    program.append(int(instruction_string.strip(), 2))

        for instruction in program:
            self.ram[address] = instruction
            address += 1

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        elif op == 'MUL':
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
            # Read the next two byte values and store them in operand_a and operand_b
            operand_a = self.ram_read(self.pc + 1)
            operand_b = self.ram_read(self.pc + 2)
            # Construct ARGS
            args = list()
            if num_operands > 0:
                args.append(operand_a)
                if num_operands > 1:
                    args.append(operand_b)
            # Execute the instruction
            self.branch_table[decoded_instruction](*args)
            # Update the PC to point to the next instruction
            if self.update_pc:
                self.pc += (1 + num_operands)
            # Set the update_pc flag to true
            self.update_pc = True
            # Loop
            self.run()