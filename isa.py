from enum import Enum

"""

   ┌─────────┬─────────────────────────────────────────────────────────────┐
   │ 40...36 │ 35                                                        0 │
   ├─────────┼─────────────────────────────────────────────────────────────┤
   │  опкод  │                     аргумент                                │
   └─────────┴─────────────────────────────────────────────────────────────┘
   """
class Opcode(str, Enum):

    INC = "increment"
    DEC = "decrement"
    SUB = "sub"
    ADD = "add"
    MUL = "mul"
    DIV = "div"

    LIT = "literal"
    TOA = "stack_to_a"
    TOB = "stack_to_b"
    TOSTACKFROMA = "a_to_stack"
    TOSTACKFROMB = "b_to_stack"
    BSTORE = "b_store"
    ASTORE = "a_store"
    BLOAD = "b_load"
    ALOAD = "a_load"
    LOAD = "load"

    LSHIFT = "lshift"
    RSHIFT = "rshift"

    INV = "inv"
    AND = "and"
    XOR = "xor"
    OR = "or"

    DROP = "drop"
    DUP = "dup"
    OVER = "over"

    JMP = "jmp"
    CALL = "call"
    RET = "return"
    IF = "if"
    MIF = "mif"

    RINTOT = "r_to_top"
    TINTOR = "top_to_r"

    HALT = "halt"


    def __str__(self):
        """Переопределение стандартного поведения `__str__` для `Enum`: вместо
        `Opcode.INC` вернуть `increment`.
        """
        return str(self.value)


opcode_to_binary = {
    Opcode.INC: 0x00,  # 0000 А можно 0b0 +
    Opcode.DEC: 0x01,  # 0001 +
    Opcode.SUB: 0x02,  # 0010 +
    Opcode.ADD: 0x03,  # 0011  +
    Opcode.MUL: 0x04,  #
    Opcode.DIV: 0x05,  #

    Opcode.LIT: 0x06,  #   +
    Opcode.TOA: 0x07,  #   +
    Opcode.TOB: 0x08,  #   +
    Opcode.TOSTACKFROMA: 0x09,  # +
    Opcode.TOSTACKFROMB: 0x0A,  # +
    Opcode.BSTORE: 0x0B,  #
    Opcode.ASTORE: 0x0C,  #
    Opcode.BLOAD: 0x0D,  #
    Opcode.ALOAD: 0x0E,  #
    Opcode.LOAD: 0x0F,  #

    Opcode.LSHIFT: 0x10,  #
    Opcode.RSHIFT: 0x11,  #

    Opcode.INV: 0x12,  # +
    Opcode.AND: 0x13,  # +
    Opcode.XOR: 0x14,  # +
    Opcode.OR: 0x15,   # +

    Opcode.DROP: 0x16,  #
    Opcode.DUP: 0x17,   #
    Opcode.OVER: 0x18,  #

    Opcode.CALL: 0x19,  #
    Opcode.RET: 0x1A,   #
    Opcode.IF: 0x1B,    #
    Opcode.MIF: 0x1C,   #

    Opcode.RINTOT: 0x1D,#
    Opcode.TINTOR: 0x1E,#

    Opcode.HALT: 0xFF,  # +
}

binary_to_opcode = {
    0x00: Opcode.INC,  # 0000
    0x01: Opcode.DEC,  # 0001
    0x02: Opcode.SUB,  # 0010
    0x03: Opcode.ADD,  # 0011
    0x04: Opcode.MUL,
    0x05: Opcode.DIV,

    0x06: Opcode.LIT,
    0x07: Opcode.TOA,
    0x08: Opcode.TOB,
    0x09: Opcode.TOSTACKFROMA,
    0x0A: Opcode.TOSTACKFROMB,
    0x0B: Opcode.BSTORE,
    0x0C: Opcode.ASTORE,
    0x0D: Opcode.BLOAD,
    0x0E: Opcode.ALOAD,
    0x0F: Opcode.LOAD,

    0x10: Opcode.LSHIFT,
    0x11: Opcode.RSHIFT,

    0x12: Opcode.INV,
    0x13: Opcode.AND,
    0x14: Opcode.XOR,
    0x15: Opcode.OR,

    0x16: Opcode.DROP,
    0x17: Opcode.DUP,
    0x18: Opcode.OVER,

    0x19: Opcode.CALL,
    0x1A: Opcode.RET,
    0x1B: Opcode.IF,
    0x1C: Opcode.MIF,

    0x1D: Opcode.RINTOT,
    0x1E: Opcode.TINTOR,

    0xFF: Opcode.HALT,
}

opcode_to_mnemonic = {
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

def to_bytes(code):
    pass


def to_hex(code):
    pass


def from_bytes(binary_code):
    pass


