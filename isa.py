from enum import Enum

"""

   ┌─────────┬─────────────────────────────────────────────────────────────┐
   │ 40...36 │ 35                                                        0 │
   ├─────────┼─────────────────────────────────────────────────────────────┤
   │  опкод  │                     аргумент                                │
   └─────────┴─────────────────────────────────────────────────────────────┘
   """
class Opcode(str, Enum):

    SUB = "sub"
    ADD = "add"
    INC = "increment"
    DEC = "decrement"
    JMP = "jmp"
    LIT = "literal"
    TOA = "stack_to_a"
    TOB = "stack_to_b"
    HALT = "halt"
    CALL = "call"
    OVER = "over"
    RET = "return"


    def __str__(self):
        """Переопределение стандартного поведения `__str__` для `Enum`: вместо
        `Opcode.INC` вернуть `increment`.
        """
        return str(self.value)


opcode_to_binary = {
    Opcode.INC: 0x0,  # 0000 А можно 0b0
    Opcode.DEC: 0x1,  # 0001
    Opcode.SUB: 0x2,  # 0010
    Opcode.ADD: 0x3,  # 0011
    Opcode.LIT: 0x4,  # 0100
    Opcode.JMP: 0x5,  # 0110
    Opcode.CALL: 0x6,
    Opcode.RET: 0x7,
    Opcode.OVER: 0x8,
    Opcode.TOA: 0x9,
    Opcode.TOB: 0xA,
    Opcode.HALT: 0xFF,
}

binary_to_opcode = {
    0x0: Opcode.INC,  # 0000
    0x1: Opcode.DEC,  # 0001
    0x2: Opcode.SUB,  # 0010
    0x3: Opcode.ADD,  # 0011
    0x4: Opcode.LIT,  # 0100
    0x5: Opcode.JMP,  # 0110
    0x6: Opcode.CALL,
    0x7: Opcode.RET,
    0x8: Opcode.OVER,
    0x9: Opcode.TOA,
    0xA: Opcode.TOB,
    0xFF: Opcode.HALT,
}

def to_bytes(code):
    pass


def to_hex(code):
    pass


def from_bytes(binary_code):
    pass


