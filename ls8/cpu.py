"""CPU functionality."""

import sys

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""

        self.ram = [0] * 256    # 256 bytes of memory

        """
        REGISTERS

        8 general-purpose 8-bit numeric registers R0-R7.

        * R5 is reserved as the interrupt mask (IM)
        * R6 is reserved as the interrupt status (IS)
        * R7 is reserved as the stack pointer (SP)

        > These registers only hold values between 0-255. After performing math on
        > registers in the emulator, bitwise-AND the result with 0xFF (255) to keep the
        > register values in that range.
        """

        self.reg = [0] * 8      # 8 general purpose registers
        self.reg[5] = 0         # interrupt mask
        self.reg[6] = 0         # interrupt status
        self.reg[7] = 0xF4      # stack pointer

        """
        INTERNAL REGISTERS

        * `PC`: Program Counter, address of the currently executing instruction
        * `IR`: Instruction Register, contains a copy of the currently executing instruction
        * `MAR`: Memory Address Register, holds the memory address we're reading or writing
        * `MDR`: Memory Data Register, holds the value to write or the value just read
        * `FL`: Flags, see below
        """

        self.pc = 0             # program counter
        self.ir = 0             # instruction register 
        self.mar = 0            # memory address register
        self.mdr = 0            # memory data register
        self.fl = 0             # flags

        """
        The flags register `FL` holds the current flags status. These flags
        can change based on the operands given to the `CMP` opcode.

        The register is made up of 8 bits. If a particular bit is set, that flag is "true".

        `FL` bits: `00000LGE`

        * `L` Less-than: during a `CMP`, set to 1 if registerA is less than registerB,
        zero otherwise.
        * `G` Greater-than: during a `CMP`, set to 1 if registerA is greater than
        registerB, zero otherwise.
        * `E` Equal: during a `CMP`, set to 1 if registerA is equal to registerB, zero
        otherwise.
        """
        
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
        self.branch_table[0b10100000] = self.add
        self.branch_table[0b10100010] = self.mul
        self.branch_table[0b10100111] = self.cmp
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
        self.branch_table[0b01010000] = self.call
        self.branch_table[0b00010001] = self.ret
        self.branch_table[0b01010100] = self.jmp
        self.branch_table[0b01010101] = self.jeq
        self.branch_table[0b01010110] = self.jne
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
        self.branch_table[0b10000010] = self.ldi
        self.branch_table[0b01000101] = self.push
        self.branch_table[0b01000110] = self.pop
        self.branch_table[0b01000111] = self.prn

    def add(self):
        self.mar += 1
        reg_a = self.ram_read()
        self.mar += 1
        reg_b = self.ram_read()
        self.alu('ADD', reg_a, reg_b)
        self.pc += 3

    def mul(self):
        self.mar += 1
        reg_a = self.ram_read()
        self.mar += 1
        reg_b = self.ram_read()
        self.alu('MUL', reg_a, reg_b)
        self.pc += 3

    def ldi(self):
        self.mar += 1
        reg_a = self.ram_read()
        self.mar += 1
        reg_b = self.ram_read()
        self.reg[reg_a] = reg_b
        self.pc += 3

    def push(self):
        """
        Push the value in the given register on the stack.

        1. Decrement the `SP`.
        2. Copy the value in the given register to the address pointed to by
        `SP`.

        Machine code:
        
        01000101 00000rrr
        45 0r
        
        """
        self.mar += 1
        reg_a = self.ram_read()
        self.reg[7] -= 1
        self.mar = self.reg[7]
        self.mdr = self.reg[reg_a]
        self.ram_write()
        self.pc += 2

    def pop(self):
        """
        Pop the value at the top of the stack into the given register.

        1. Copy the value from the address pointed to by `SP` to the given register.
        2. Increment `SP`.

        Machine code:
        
        01000110 00000rrr
        46 0r
        
        """
        self.mar += 1
        reg_a = self.ram_read()
        self.mar = self.reg[7]
        self.reg[reg_a] = self.ram_read()
        self.reg[7] += 1
        self.pc += 2

    def call(self):
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
        self.mar += 1
        reg_a = self.ram_read()
        # decrement the stack pointer
        self.reg[7] -= 1
        # copy the value at memory address program counter + 2 to the address pointed at by the stack pointer
        self.mar = self.reg[7]
        self.mdr = self.pc + 2
        self.ram_write()
        # set the pc to the address stored in the given register
        self.pc = self.reg[reg_a]

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
        self.mar = self.reg[7]
        self.pc = self.ram_read()
        # increment the stack pointer
        self.reg[7] += 1

    def cmp(self):
        """
        Compare the values in two registers.

        * If they are equal, set the Equal `E` flag to 1, otherwise set it to 0.

        * If registerA is less than registerB, set the Less-than `L` flag to 1,
        otherwise set it to 0.

        * If registerA is greater than registerB, set the Greater-than `G` flag
        to 1, otherwise set it to 0.

        Machine code:
        ```
        10100111 00000aaa 00000bbb
        A7 0a 0b
        ```
        """
        self.mar += 1
        reg_a = self.ram_read()
        self.mar += 1
        reg_b = self.ram_read()
        if self.reg[reg_a] == self.reg[reg_b]:
            self.fl = 0b00000001
        elif self.reg[reg_a] > self.reg[reg_b]:
            self.fl = 0b00000010
        else:
            self.fl = 0b00000100
        self.pc += 3

    def jmp(self):
        """
        Jump to the address stored in the given register.

        Set the `PC` to the address stored in the given register.

        Machine code:
        ```
        01010100 00000rrr
        54 0r
        ```
        """
        self.mar += 1
        reg_a = self.ram_read()
        self.pc = self.reg[reg_a]

    def jeq(self):
        """
        If `equal` flag is set (true), jump to the address stored in the given register.

        Machine code:
        ```
        01010101 00000rrr
        55 0r
        ```
        """
        if self.fl == 0b00000001:
            self.mar += 1
            reg_a = self.ram_read()
            self.pc = self.reg[reg_a]
        else:
            self.pc += 2

    def jne(self):
        """
        If `E` flag is clear (false, 0), jump to the address stored in the given
        register.

        Machine code:
        ```
        01010110 00000rrr
        56 0r
        """
        if self.fl & 0b00000001 == 0:
            self.mar += 1
            reg_a = self.ram_read()
            self.pc = self.reg[reg_a]
        else:
            self.pc += 2

    def prn(self):
        self.mar += 1
        reg_a = self.ram_read()
        print(self.reg[reg_a])
        self.pc += 2

    def ram_read(self):
        return self.ram[self.mar]

    def ram_write(self):
        self.ram[self.mar] = self.mdr

    def load(self):
        """Load a program into memory."""

        program = list()

        with open("/Users/shaunorpen/Lambda/ls8/ls8/examples/sctest.ls8") as f:
            for line in f:
                line_values = line.split("#")
                instruction_string = line_values[0]
                if len(instruction_string) > 0:
                    program.append(int(instruction_string.strip(), 2))

        for i in range(len(program)):
            self.mar = i
            self.mdr = program[i]
            self.ram_write()

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        elif op == 'MUL':
            self.reg[reg_a] *= self.reg[reg_b]
        #elif op == "SUB": etc
        else:
            raise Exception("Unsupported ALU operation")

    def run(self):
        """Run the CPU."""
        # Read the first instruction
        self.mar = self.pc
        self.ir = self.ram_read()
        # If the instruction is anything other than HLT, run the program
        while not self.ir == 1:
            # Execute the instruction
            self.branch_table[self.ir]()
            # Read next instruction
            self.mar = self.pc
            self.ir = self.ram_read()
            # Loop
            self.run()