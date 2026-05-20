from enum import Enum

"""

   ┌─────────┬─────────────────────────────────────────────────────────────┐
   │ 40...36 │ 35                (если он есть)                          0 │
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
    MOD = "mod"

    LIT = "literal"
    TOA = "stack_to_a"
    TOSTACKFROMA = "a_to_stack"
    ASTORE = "a_store"
    ALOAD = "a_load"
    LOAD = "load"
    STORE = "store"

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

    ALOADP = "a_store_+"

    IRET = "iret"
    EI = "ei"
    DI = "di"
    NIF = "nif"

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
    Opcode.ADD: 0x03,  # 0011 +
    Opcode.MUL: 0x04,  # TODO: :З :З :З :З :З :З :З :З :З :З :З :З :З :З
    Opcode.DIV: 0x05,  #

    Opcode.LIT: 0x06,  # +
    Opcode.TOA: 0x07,  # +
    Opcode.TOSTACKFROMA: 0x09,  # +
    Opcode.ASTORE: 0x0C,  #
    Opcode.ALOAD: 0x0E,  #
    Opcode.LOAD: 0x0F,
    Opcode.STORE: 0x1F,  #

    Opcode.LSHIFT: 0x10,  # +
    Opcode.RSHIFT: 0x11,  # +

    Opcode.INV: 0x12,  # +
    Opcode.AND: 0x13,  # +
    Opcode.XOR: 0x14,  # +
    Opcode.OR: 0x15,  # +

    Opcode.DROP: 0x16,  # +
    Opcode.DUP: 0x17,  # +
    Opcode.OVER: 0x18,  # +

    Opcode.CALL: 0x19,  #
    Opcode.RET: 0x1A,  #
    Opcode.IF: 0x1B,  #
    Opcode.MIF: 0x1C,  #

    Opcode.RINTOT: 0x1D,  # +
    Opcode.TINTOR: 0x1E,  # +


    Opcode.JMP: 0x20,
    Opcode.ALOADP: 0x21,
    Opcode.IRET: 0x22,
    Opcode.EI: 0x23,
    Opcode.DI: 0x24,
    Opcode.NIF: 0x25,
Opcode.MOD: 0x26,
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
    0x09: Opcode.TOSTACKFROMA,
    0x0C: Opcode.ASTORE,
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

    0x1F: Opcode.STORE,

    0x20: Opcode.JMP,
    0x21: Opcode.ALOADP,
    0x22: Opcode.IRET,
    0x23: Opcode.EI,
    0x24: Opcode.DI,
    0x25: Opcode.NIF,
    0x26: Opcode.MOD,
    0xFF: Opcode.HALT,
}


def to_bytes(code):
    pass


def to_hex(code):
    pass


def from_bytes(binary_code):
    pass
