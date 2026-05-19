from abc import ABC, abstractmethod
import os
import json
import re
import sys
import random

from isa import Opcode, opcode_to_binary, binary_to_opcode

INPUT_PORT_ADDR = 31998
OUTPUT_PORT_ADDR = 31999


class Expression(ABC):
    global context

    @abstractmethod
    def interpret(self):
        pass

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def print_ast(self, level=0):
        pass


class Number(Expression):
    def __init__(self, number: int):
        self.number = number

    def interpret(self):
        return self.number

    def execute(self):
        val = self.number & 0xFFFFFFFF
        val = self.number & 0xFFFFFFFF
        context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[Opcode.LIT]):02x}{val:08x} - lit: stack.push({self.number}))\n"

        context.byte_code.append(opcode_to_binary[Opcode.LIT])
        context.byte_code.extend(val.to_bytes(4, byteorder='big'))
        context.inc_comm_memory_pos(5)

    def print_ast(self, level=0):
        return "  " * level + f"Number({self.number})\n"


class Variable(Expression):
    def __init__(self, name: str):
        self.name = name

    def interpret(self):
        if self.name not in context.nameSpace.keys():
            raise KeyError(f"ашипка: переменная {self.name} не была определена!")
        return context.nameValue[self.name]

    def execute(self):
        addr = context.nameSpace[self.name] & 0xFFFFFFFF
        context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[Opcode.LOAD]):02x}{addr:08x} - load: stack.push(mem[{context.nameSpace[self.name]}]))\n"

        context.byte_code.append(opcode_to_binary[Opcode.LOAD])
        context.byte_code.extend(addr.to_bytes(4, byteorder='big'))
        context.inc_comm_memory_pos(5)

    def print_ast(self, level=0):
        return "  " * level + f"Variable('{self.name}')\n"


class ReadAddress(Expression):
    def __init__(self, addr_expr: Expression):
        self.addr_expr = addr_expr

    def interpret(self):
        return 0

    def execute(self):
        self.addr_expr.execute()
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.TOA]):02x} - toa\n"
        context.byte_code.append(opcode_to_binary[Opcode.TOA])  # Переносим адрес со стека в регистр A
        context.inc_comm_memory_pos(1)

        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.ALOAD]):02x} - aload\n"
        context.byte_code.append(opcode_to_binary[Opcode.ALOAD])  # Читаем память по адресу в A на стек
        context.inc_comm_memory_pos(1)

    def print_ast(self, level=0):
        res = "  " * level + "ReadAddress:\n"
        res += self.addr_expr.print_ast(level + 1)
        return res


class Add(Expression):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def interpret(self):
        return (self.left.interpret() + self.right.interpret())

    def execute(self):
        self.left.execute()
        self.right.execute()
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.ADD]):02x} - add: \tstack.pop()\tstack.pop()\tstack.push(stack.top+stack.second]))\n"
        context.byte_code.append(opcode_to_binary[Opcode.ADD])
        context.inc_comm_memory_pos(1)

    def print_ast(self, level=0):
        return "  " * level + "Add:\n" + self.left.print_ast(level + 1) + self.right.print_ast(level + 1)


class Sub(Expression):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def interpret(self):
        return (self.left.interpret() - self.right.interpret())

    def execute(self):
        self.left.execute()
        self.right.execute()
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.SUB]):02x} - sub: \tstack.pop()\tstack.pop()stack.push(stack.top-stack.second]))\n"
        context.byte_code.append(opcode_to_binary[Opcode.SUB])
        context.inc_comm_memory_pos(1)

    def print_ast(self, level=0):
        return "  " * level + "Sub:\n" + self.left.print_ast(level + 1) + self.right.print_ast(level + 1)


class Mul(Expression):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def interpret(self):
        return (self.left.interpret() * self.right.interpret())

    def execute(self):
        self.left.execute()
        self.right.execute()
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.MUL]):02x} - mul: \tstack.pop()\tstack.pop()stack.push(stack.top*stack.second]))\n"
        context.byte_code.append(opcode_to_binary[Opcode.MUL])
        context.inc_comm_memory_pos(1)

    def print_ast(self, level=0):
        return "  " * level + "Mul:\n" + self.left.print_ast(level + 1) + self.right.print_ast(level + 1)


class Div(Expression):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def interpret(self):
        return (self.left.interpret() // self.right.interpret())

    def execute(self):
        self.left.execute()
        self.right.execute()
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.DIV]):02x} - div\n"
        context.byte_code.append(opcode_to_binary[Opcode.DIV])
        context.inc_comm_memory_pos(1)

    def print_ast(self, level=0):
        return "  " * level + "Div:\n" + self.left.print_ast(level + 1) + self.right.print_ast(level + 1)


class Eq(Expression):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def interpret(self):
        return (self.left.interpret() % self.right.interpret())

    def execute(self):
        self.left.execute()
        self.right.execute()

        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.MOD]):02x} - mod\n"
        context.byte_code.append(opcode_to_binary[Opcode.MOD])
        context.inc_comm_memory_pos(1)

    def print_ast(self, level=0):
        return "  " * level + "Mod (%):\n" + self.left.print_ast(level + 1) + self.right.print_ast(level + 1)


class Greater(Expression):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right
        self.op_type = ">"
        self.jump_opcode = Opcode.MIF

    def interpret(self):
        return int(self.left.interpret() > self.right.interpret())

    def execute(self):
        self.right.execute()
        self.left.execute()
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.SUB]):02x} - sub (stack.top-stack.second)\n"
        context.byte_code.append(opcode_to_binary[Opcode.SUB])
        context.inc_comm_memory_pos(1)

    def print_ast(self, level=0):
        return "  " * level + "Greater (>):\n" + self.left.print_ast(level + 1) + self.right.print_ast(level + 1)


class Less(Expression):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right
        self.op_type = "<"
        self.jump_opcode = Opcode.MIF

    def interpret(self):
        return int(self.left.interpret() < self.right.interpret())

    def execute(self):
        self.left.execute()
        self.right.execute()
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.SUB]):02x} - sub (stack.top-stack.second)\n"
        context.byte_code.append(opcode_to_binary[Opcode.SUB])
        context.inc_comm_memory_pos(1)

    def print_ast(self, level=0):
        return "  " * level + "Less (<):\n" + self.left.print_ast(level + 1) + self.right.print_ast(level + 1)


class Equal(Expression):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right
        self.op_type = "=="
        self.jump_opcode = Opcode.NIF

    def interpret(self):
        return int(self.left.interpret() == self.right.interpret())

    def execute(self):
        self.left.execute()
        self.right.execute()
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.SUB]):02x} - sub: \tstack.pop()\tstack.pop()\tstack.push(stack.top-stack.second)\n"
        context.byte_code.append(opcode_to_binary[Opcode.SUB])
        context.inc_comm_memory_pos(1)

    def print_ast(self, level=0):
        return "  " * level + "Equal (==):\n" + self.left.print_ast(level + 1) + self.right.print_ast(level + 1)


class StringLiteral(Expression):
    def __init__(self, text: str):
        self.text = text

        self.addr = context.saveStringData(text)

    def interpret(self):
        return self.addr

    def execute(self):
        context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[Opcode.LIT]):02x}{self.addr:08x} - lit: stack.push(addr of '{self.text}')\n"

        context.byte_code.append(opcode_to_binary[Opcode.LIT])
        context.byte_code.extend(self.addr.to_bytes(4, byteorder='big'))
        context.inc_comm_memory_pos(5)

    def print_ast(self, level=0):
        return "  " * level + f"StringLiteral(\"{self.text}\")\n"


class Context:
    data_memory_pos = 1  # на дата-мемори указатель  ( свободная ячейка) 32 бита
    comm_memory_pos = 0  # указатель  на дата-мемори( свободная ячейка) 8 бит
    nameSpace = dict()  # пространство имен переменных \\где какая переменнная лежит\
    nameValue = dict()  # имитация памяти TODO: а нужна вообще?
    nameType = dict()  # для соблюдения типизации
    data_image = {0: 0}
    output1st = "---------data_memory_pos-32-bit---\n"
    output2st = "---------command_memory---8-bit---\n<address> - <HEXCODE> - <mnemonic>\n"
    byte_code = bytearray()
    entry_point = 0

    def saveStringData(self, text):
        addr = self.data_memory_pos
        codes = []
        for char in text:
            self.data_image[self.data_memory_pos] = ord(char)
            codes.append(str(ord(char)))
            self.data_memory_pos += 1
        self.data_image[self.data_memory_pos] = 0
        codes.append("0")
        self.data_memory_pos += 1
        end_addr = self.data_memory_pos - 1
        self.output1st += f"0x{addr:02x}-0x{end_addr:02x} - String: \"{text}\" (ASCII: {', '.join(codes)}) | Указатель на начало: {addr} (0x{addr:02x})\n"
        return addr

    def saveLong(self, name, value, type="долгоцело"):
        self.nameValue[name] = value
        self.nameSpace[name] = self.data_memory_pos
        self.nameType[name] = type
        addr = self.data_memory_pos
        self.output1st += f"0x{addr:02x}-0x{addr + 1:02x} - Переменная '{name}' ({type}) расположено на 0x{addr:02x}\n"

        self.data_memory_pos += 2

    def saveInt(self, name, value, type="цело"):

        self.nameValue[name] = value
        self.nameSpace[name] = self.data_memory_pos
        self.nameType[name] = type

        self.data_image[self.data_memory_pos] = value

        addr = self.data_memory_pos
        if type == "грамота":
            self.output1st += f"0x{addr:02x}      - Переменная '{name}' (указатель на строку) расположен на 0x{addr:02x}\n"
        else:
            self.output1st += f"0x{addr:02x}      - Переменная '{name}' ({type}) расположен на 0x{addr:02x}\n"

        self.data_memory_pos += 1

    def rewrite(self, name, value):
        self.nameValue[name] = value

    def inc_comm_memory_pos(self, comm_bytes):
        self.comm_memory_pos += comm_bytes


context = Context()


class Statement(ABC):
    global context

    def __init__(self):
        self.statement_list = []

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def print_ast(self, level=0):
        pass


class Program(Statement):
    def execute(self):
        for _ in self.statement_list:
            _.execute()

    def print_ast(self, level=0):
        res = "AST (Абстрактное Синтаксическое Дерево):\n"
        for stmt in self.statement_list:
            res += stmt.print_ast(level + 1)
        return res


class Entry_Point(Statement):
    def __init__(self, is_trap=False):
        super().__init__()
        self.is_trap = is_trap

    def execute(self):
        if self.is_trap:
            context.data_image[0] = context.comm_memory_pos
        else:
            context.entry_point = context.comm_memory_pos

        for _ in self.statement_list:
            _.execute()

    def print_ast(self, level=0):
        name = "TRAP HANDLER" if self.is_trap else "MAIN"
        res = "  " * level + f"Block [{name}]:\n"
        for stmt in self.statement_list:
            res += stmt.print_ast(level + 1)
        return res


class Variable_Declaration(Statement):
    def __init__(self):
        super().__init__()
        type = "цело"
        name = "variable"
        value: Expression = None

    def execute(self):
        if self.name in context.nameSpace.keys():
            raise KeyError(f"ашипка: переменная {self.name} уже определена")
        else:
            self.value.execute()
            context.saveInt(self.name, self.value.interpret())
            addr = (context.data_memory_pos - 1) & 0xFFFFFFFF
            context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[Opcode.STORE]):02x}{addr:08x} - store: mem[{context.data_memory_pos - 1}] <- stack.pop()\n"

            context.byte_code.append(opcode_to_binary[Opcode.STORE])
            context.byte_code.extend(addr.to_bytes(4, byteorder='big'))
            context.inc_comm_memory_pos(5)

    def print_ast(self, level=0):
        res = "  " * level + f"Declaration (type: {self.type}, var: '{self.name}'):\n"
        res += self.value.print_ast(level + 1)
        return res


class Assignment(Statement):

    def __init__(self):
        name = "variable"
        value: Expression = None
        super().__init__()

    def execute(self):
        if self.name not in context.nameSpace.keys():
            raise KeyError(f"ашипка: переменная {self.name} не объявлялась ранее :З")
        else:
            var_type = context.nameType[self.name]
            if var_type == "цело":
                self.value.execute()
                context.rewrite(self.name, self.value.interpret())

                addr = context.nameSpace[self.name] & 0xFFFFFFFF
                context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[Opcode.STORE]):02x}{addr:08x} - store: mem[{context.nameSpace[self.name]}] <- stack.pop()\n"

                context.byte_code.append(opcode_to_binary[Opcode.STORE])
                context.byte_code.extend(addr.to_bytes(4, byteorder='big'))
                context.inc_comm_memory_pos(5)
            elif var_type == "грамота":
                pass

    def print_ast(self, level=0):
        res = "  " * level + f"Assignment (var: '{self.name}'):\n"
        res += self.value.print_ast(level + 1)
        return res


class Halt(Statement):
    def execute(self):
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.HALT]):02x} - halt\n"
        context.byte_code.append(opcode_to_binary[Opcode.HALT])
        context.inc_comm_memory_pos(1)

    def print_ast(self, level=0):
        return "  " * level + "Halt\n"


class If(Statement):
    def __init__(self):
        super().__init__()
        self.condition: Expression = None

    def execute(self):
        self.condition.execute()

        op = self.condition.jump_opcode
        end_label = f"<if-end-{id(self)}>"

        context.byte_code.append(opcode_to_binary[op])
        patch_idx = len(context.byte_code)
        context.byte_code.extend(b'\x00\x00\x00\x00')

        if isinstance(self.condition, Equal):
            context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[op]):02x}{end_label} - jump to 0x{end_label} if stack.pop == 0\n"
        else:
            context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[op]):02x}{end_label} - jump to 0x{end_label} if stack.pop >= 0\n"

        context.inc_comm_memory_pos(5)

        condition_result = self.condition.interpret()
        if condition_result != 0:
            for stmt in self.statement_list:
                stmt.execute()
        else:
            old_values = context.nameValue.copy()
            for stmt in self.statement_list:
                stmt.execute()
            context.nameValue = old_values

        end_addr = context.comm_memory_pos
        context.output2st = context.output2st.replace(end_label, str(f"{end_addr:08x}"))
        context.byte_code[patch_idx: patch_idx + 4] = (end_addr & 0xFFFFFFFF).to_bytes(4, byteorder='big')

    def print_ast(self, level=0):
        res = "  " * level + "If statement:\n"
        res += "  " * (level + 1) + "- Condition:\n"
        res += self.condition.print_ast(level + 2)
        res += "  " * (level + 1) + "- Body:\n"
        for stmt in self.statement_list:
            res += stmt.print_ast(level + 2)
        return res


class While(Statement):
    def __init__(self):
        super().__init__()
        self.condition: Expression = None

    def execute(self):
        begin_addr = context.comm_memory_pos
        self.condition.execute()

        op = self.condition.jump_opcode
        end_label = f"<while-end-{id(self)}>"

        context.byte_code.append(opcode_to_binary[op])
        patch_idx = len(context.byte_code)
        context.byte_code.extend(b'\x00\x00\x00\x00')

        if isinstance(self.condition, Equal):
            context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[op]):02x}{end_label} - jump to 0x{end_label} if stack.pop == 0\n"
        else:
            context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[op]):02x}{end_label} - jump to 0x{end_label} if stack.pop >= 0\n"

        context.inc_comm_memory_pos(5)

        condition_result = self.condition.interpret()
        if condition_result != 0:
            for stmt in self.statement_list:
                stmt.execute()
        else:
            old_values = context.nameValue.copy()
            for stmt in self.statement_list:
                stmt.execute()
            context.nameValue = old_values

        context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x}  - 0x{(opcode_to_binary[Opcode.JMP]):02x}{begin_addr:08x} - jump to 0x{begin_addr:08x}\n"

        context.byte_code.append(opcode_to_binary[Opcode.JMP])
        context.byte_code.extend((begin_addr & 0xFFFFFFFF).to_bytes(4, byteorder='big'))
        context.inc_comm_memory_pos(5)

        end_addr = context.comm_memory_pos
        context.output2st = context.output2st.replace(end_label, str(f"{end_addr:08x}"))
        context.byte_code[patch_idx: patch_idx + 4] = (end_addr & 0xFFFFFFFF).to_bytes(4, byteorder='big')

    def print_ast(self, level=0):
        res = "  " * level + "While loop:\n"
        res += "  " * (level + 1) + "- Condition:\n"
        res += self.condition.print_ast(level + 2)
        res += "  " * (level + 1) + "- Body:\n"
        for stmt in self.statement_list:
            res += stmt.print_ast(level + 2)
        return res


class For(Statement):
    def __init__(self):
        super().__init__()
        self.condition: Expression = None
        self.var_dec: Variable_Declaration = None
        self.var_assig: Assignment = None

    def execute(self):
        self.var_dec.execute()
        begin_addr = context.comm_memory_pos
        self.condition.execute()

        op = self.condition.jump_opcode
        end_label = f"<while-end-{id(self)}>"

        context.byte_code.append(opcode_to_binary[op])
        patch_idx = len(context.byte_code)
        context.byte_code.extend(b'\x00\x00\x00\x00')

        if isinstance(self.condition, Equal):
            context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[op]):02x}{end_label} - jump to 0x{end_label} if stack.pop == 0\n"
        else:
            context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[op]):02x}{end_label} - jump to 0x{end_label} if stack.pop >= 0\n"

        context.inc_comm_memory_pos(5)

        condition_result = self.condition.interpret()
        if condition_result != 0:
            for stmt in self.statement_list:
                stmt.execute()
        else:
            old_values = context.nameValue.copy()
            for stmt in self.statement_list:
                stmt.execute()
            context.nameValue = old_values

        self.var_assig.execute()

        context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x}  - 0x{(opcode_to_binary[Opcode.JMP]):02x}{begin_addr:08x} - jump to 0x{begin_addr:08x}\n"

        context.byte_code.append(opcode_to_binary[Opcode.JMP])
        context.byte_code.extend((begin_addr & 0xFFFFFFFF).to_bytes(4, byteorder='big'))
        context.inc_comm_memory_pos(5)

        end_addr = context.comm_memory_pos
        context.output2st = context.output2st.replace(end_label, str(f"{end_addr:08x}"))
        context.byte_code[patch_idx: patch_idx + 4] = (end_addr & 0xFFFFFFFF).to_bytes(4, byteorder='big')


class Output(Statement):
    def __init__(self):
        super().__init__()
        self.value: Expression = None

    def execute(self):
        self.value.execute()

        context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[Opcode.STORE]):02x}{OUTPUT_PORT_ADDR:08x} - store: mem[{OUTPUT_PORT_ADDR}] <- stack.pop() (ВЫВОД)\n"

        context.byte_code.append(opcode_to_binary[Opcode.STORE])
        context.byte_code.extend(OUTPUT_PORT_ADDR.to_bytes(4, byteorder='big'))
        context.inc_comm_memory_pos(5)

    def print_ast(self, level=0):
        res = "  " * level + "Output (пиши_память):\n"
        res += self.value.print_ast(level + 1)
        return res


class Input(Expression):
    def interpret(self):
        return 0

    def execute(self):
        context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[Opcode.LOAD]):02x}{INPUT_PORT_ADDR:08x} - load: stack.push(mem[{INPUT_PORT_ADDR}]) (ВВОД)\n"
        context.byte_code.append(opcode_to_binary[Opcode.LOAD])
        context.byte_code.extend(INPUT_PORT_ADDR.to_bytes(4, byteorder='big'))
        context.inc_comm_memory_pos(5)

    def print_ast(self, level=0):
        return "  " * level + "Input (читай_память)\n"


class PrintString(Statement):
    def __init__(self):
        super().__init__()
        self.value: Expression = None

    def execute(self):
        self.value.execute()
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.TOA]):02x} - toa\n"
        context.byte_code.append(opcode_to_binary[Opcode.TOA])
        context.inc_comm_memory_pos(1)
        begin_addr = context.comm_memory_pos
        end_label = f"<str-end-{id(self)}>"
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.ALOADP]):02x} - aloadp (@+)\n"
        context.byte_code.append(opcode_to_binary[Opcode.ALOADP])
        context.inc_comm_memory_pos(1)
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.DUP]):02x} - dup\n"
        context.byte_code.append(opcode_to_binary[Opcode.DUP])
        context.inc_comm_memory_pos(1)

        context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[Opcode.IF]):02x}{end_label} - if (выход из цикла)\n"
        context.byte_code.append(opcode_to_binary[Opcode.IF])
        patch_idx = len(context.byte_code)
        context.byte_code.extend(b'\x00\x00\x00\x00')
        context.inc_comm_memory_pos(5)

        context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[Opcode.STORE]):02x}{OUTPUT_PORT_ADDR:08x} - store: Вывод символа\n"
        context.byte_code.append(opcode_to_binary[Opcode.STORE])
        context.byte_code.extend(OUTPUT_PORT_ADDR.to_bytes(4, byteorder='big'))
        context.inc_comm_memory_pos(5)

        context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[Opcode.JMP]):02x}{begin_addr:08x} - jump to 0x{begin_addr:08x} (повтор цикла)\n"
        context.byte_code.append(opcode_to_binary[Opcode.JMP])
        context.byte_code.extend(begin_addr.to_bytes(4, byteorder='big'))
        context.inc_comm_memory_pos(5)

        end_addr = context.comm_memory_pos
        context.output2st = context.output2st.replace(end_label, str(f"{end_addr:08x}"))
        context.byte_code[patch_idx: patch_idx + 4] = (end_addr & 0xFFFFFFFF).to_bytes(4, byteorder='big')

    def print_ast(self, level=0):
        res = "  " * level + "PrintString (пиши_строку):\n"
        res += self.value.print_ast(level + 1)
        return res

class IRetStatement(Statement):
    def execute(self):
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.IRET]):02x} - iret (возврат из прерывания)\n"
        context.byte_code.append(opcode_to_binary[Opcode.IRET])
        context.inc_comm_memory_pos(1)

    def print_ast(self, level=0):
        return "  " * level + "IRetStatement (trap-end)\n"

class EIStatement(Statement):
    def execute(self):
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.EI]):02x} - ei (разрешить прерывания)\n"
        context.byte_code.append(opcode_to_binary[Opcode.EI])
        context.inc_comm_memory_pos(1)

    def print_ast(self, level=0):
        return "  " * level + "Enable Interrupts (ei)\n"

class DIStatement(Statement):
    def execute(self):
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.DI]):02x} - di (запретить прерывания)\n"
        context.byte_code.append(opcode_to_binary[Opcode.DI])
        context.inc_comm_memory_pos(1)

    def print_ast(self, level=0):
        return "  " * level + "Disable Interrupts (di)\n"

class WriteAddress(Statement):
    def __init__(self, addr_expr: Expression, val_expr: Expression):
        self.addr_expr = addr_expr
        self.val_expr = val_expr

    def execute(self):
        self.val_expr.execute()
        self.addr_expr.execute()
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.TOA]):02x} - toa\n"
        context.byte_code.append(opcode_to_binary[Opcode.TOA])
        context.inc_comm_memory_pos(1)

        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.ASTORE]):02x} - astore\n"
        context.byte_code.append(opcode_to_binary[Opcode.ASTORE])
        context.inc_comm_memory_pos(1)

    def print_ast(self, level=0):
        res = "  " * level + "WriteAddress (пиши_адрес):\n"
        res += "  " * (level + 1) + "- Address:\n"
        res += self.addr_expr.print_ast(level + 2)
        res += "  " * (level + 1) + "- Value:\n"
        res += self.val_expr.print_ast(level + 2)
        return res

math_op = {"*", "+", "-", ":", "%"}
high_op = {"*", ":", "%"}


def check_next_highest_op(tokens):
    first_index = 0
    second_index = -1
    cnt = 1
    try:
        first_index = tokens.index("(")
    except:
        return
    for i in range(first_index + 1, len(tokens)):
        if cnt == 0:
            break
        if cnt < 0:
            print("fsdfsfd")
            raise KeyError("Неправильная последовательность скобок")

        if tokens[i] == ")":
            cnt -= 1
            if cnt == 0:
                second_index = i
        if tokens[i] == "(":
            cnt += 1

    if second_index == -1:
        raise KeyError("Неправильная последовательность скобок")
    return first_index, second_index


def check_next_hight_op(tokens):
    mul_index = 0
    div_index = 0
    eq_index = 0
    try:
        mul_index = tokens.index("*")
    except:
        pass
    try:
        div_index = tokens.index(":")
    except:
        pass
    try:
        eq_index = tokens.index("%")
    except:
        pass
    a = [mul_index, div_index, eq_index]
    b = [x for x in a if x != 0]
    try:
        return min(b)
    except:
        return 0


def check_next_low_op(tokens):
    sub_index = 0
    add_index = 0

    try:
        sub_index = tokens.index("-")
    except:
        pass
    try:
        add_index = tokens.index("+")
    except:
        pass
    a = [sub_index, add_index]
    b = [x for x in a if x != 0]
    try:
        return min(b)
    except:
        return 0


def parse_epression(expression, isRecursion=False):
    tokens = []
    if not isRecursion:
        tokens = expression.replace(" ", "")
        tokens = tokens.split(" ")
    else:
        tokens = expression

    while check_next_highest_op(tokens):
        first_index, second_index = check_next_highest_op(tokens)
        subtokens = tokens[first_index + 1:second_index]

        subexspression = parse_epression(subtokens, True)
        tokens[first_index:second_index + 1] = " "
        tokens[first_index] = subexspression

    while check_next_hight_op(tokens):
        i = check_next_hight_op(tokens)

        token = tokens[i]
        left_token = None
        right_token = None
        epx = None
        if i != 0:
            left_token = tokens[i - 1]
        if i != len(tokens) - 1:
            right_token = tokens[i + 1]
        if token == "*":
            epx = Mul()
        elif token == ":":
            epx = Div()
        elif token == "%":
            epx = Eq()

        if left_token is not None and not isinstance(left_token, Expression):
            left_token = parse_token(left_token)
        if right_token is not None and not isinstance(right_token, Expression):
            right_token = parse_token(right_token)

        epx.left = left_token
        epx.right = right_token
        tokens[i] = (epx)
        tokens.pop(i - 1)
        tokens.pop(i)

    while check_next_low_op(tokens):
        i = check_next_low_op(tokens)

        token = tokens[i]
        left_token = None
        right_token = None
        epx = None
        if i != 0:
            left_token = tokens[i - 1]
        if i != len(tokens) - 1:
            right_token = tokens[i + 1]
        if token == "-":
            epx = Sub()
        elif token == "+":
            epx = Add()

        if left_token is not None and not isinstance(left_token, Expression):
            left_token = parse_token(left_token)
        if right_token is not None and not isinstance(right_token, Expression):
            right_token = parse_token(right_token)

        epx.left = left_token
        epx.right = right_token
        tokens[i] = (epx)
        tokens.pop(i - 1)
        tokens.pop(i)

    for _ in range(len(tokens)):
        if not isinstance(tokens[_], Expression):
            tokens[_] = parse_token(tokens[_])

    final_expression = tokens[0]
    return final_expression


def parse_token(token, tokens=None, index=0):
    if isinstance(token, Expression):
        return token
    if token is None:
        return None

    if isinstance(token, str) and "читай_память" in token:
        return Input()

    if isinstance(token, str) and token.startswith("читай_адрес("):
        var_name = token[12:-1].strip()
        return ReadAddress(Variable(var_name))

    if isinstance(token, str) and token.startswith('"') and token.endswith('"'):
        return StringLiteral(token[1:-1])

    if token in math_op:
        match token:
            case "+":
                return Add()
            case "-":
                return Sub()
            case "*":
                return Mul()
            case ":":
                return Div()
            case "%":
                return Eq()
    elif token not in math_op:
        try:
            return Number(int(token))
        except ValueError:
            return Variable(token)


def parse_condition(st: Statement, tokens, line):
    condition = tokens
    if "==" in condition:
        idx = condition.index("==")
        st.condition = Equal(
            parse_epression(condition[:idx], True),
            parse_epression(condition[idx + 1:], True)
        )
    elif "<" in condition:
        idx = condition.index("<")
        st.condition = Less(
            parse_epression(condition[:idx], True),
            parse_epression(condition[idx + 1:], True)
        )
    elif ">" in condition:
        idx = condition.index(">")
        st.condition = Greater(
            parse_epression(condition[:idx], True),
            parse_epression(condition[idx + 1:], True)
        )
    else:
        raise KeyError(f"Cringe: условие в {line} невозможно распознать! Проверьте написание == (=)")


def translate(file):
    global context
    program = Program()

    statement_stack = []
    statement_stack.append(program)

    for line in file:
        if line == "\n" or line.strip() == "":
            continue

        try:
            index_of_end = line.index(";")
        except ValueError:
            raise KeyError(f"|||{line}||| - нет ; на конце")

        raw_string = line[:index_of_end].strip()
        tokens = re.findall(r'"[^"]*"|\S+', raw_string)

        if not tokens:
            continue

        if tokens[0] == "main":

            main_block = Entry_Point()
            statement_stack.append(main_block)

        elif tokens[0] == "main-end":
            if isinstance(statement_stack[-1], Entry_Point):
                main_block = statement_stack.pop()
                main_block.statement_list.append(Halt())
                statement_stack[-1].statement_list.append(main_block)
            else:
                raise KeyError("Неправильная стуктура вложенности (main)!")

        elif tokens[0] == "ei":
            statement_stack[-1].statement_list.append(EIStatement())

        elif tokens[0] == "di":
            statement_stack[-1].statement_list.append(DIStatement())

        elif tokens[0] == "trap":

            trap_block = Entry_Point(is_trap=True)

            statement_stack.append(trap_block)

        elif tokens[0] == "trap-end":
            trap_block = statement_stack.pop()
            trap_block.statement_list.append(IRetStatement())
            statement_stack[-1].statement_list.append(trap_block)

        elif tokens[0] in {"цело", "долгоцело", "грамота"}:
            st = Variable_Declaration()
            st.type = tokens[0]
            st.name = tokens[1]
            st.value = parse_epression(tokens[3::], True)
            statement_stack[-1].statement_list.append(st)


        elif tokens[0].startswith("пиши_память"):
            st = Output()
            start = line.find('(')
            end = line.rfind(')')
            expr_str = line[start + 1:end].strip()
            expr_tokens = [t for t in expr_str.split(" ") if t]
            st.value = parse_epression(expr_tokens, True)
            statement_stack[-1].statement_list.append(st)

        elif tokens[0].startswith("пиши_строку"):
            st = PrintString()
            start = line.find('(')
            end = line.rfind(')')
            expr_str = line[start + 1:end].strip()
            expr_tokens = [t for t in expr_str.split(" ") if t]
            st.value = parse_epression(expr_tokens, True)
            statement_stack[-1].statement_list.append(st)

        elif tokens[0].startswith("пиши_адрес"):
            st = WriteAddress(None, None)
            start = line.find('(')
            end = line.rfind(')')
            args = line[start + 1:end].strip().split(',')

            st.addr_expr = parse_epression([args[0].strip()], True)
            st.val_expr = parse_epression([args[1].strip()], True)
            statement_stack[-1].statement_list.append(st)

        elif tokens[0] == "if":
            st = If()
            condition = tokens[2:-1]
            parse_condition(st, condition, line)
            statement_stack.append(st)

        elif tokens[0] == "while":
            st = While()
            condition = tokens[2:-1]
            parse_condition(st, condition, line)
            statement_stack.append(st)

        elif tokens[0] == "for":
            st = For()
            condition = tokens[2:-1]

            first_zap = condition.index(",")
            second_zap = condition.index(",", first_zap + 1, len(condition) - 1)

            dec = condition[:first_zap]
            cond = condition[first_zap + 1:second_zap]
            assig = condition[second_zap + 1:]

            vd = Variable_Declaration()
            vd.type = dec[0]
            vd.name = dec[1]
            vd.value = parse_epression(dec[3::], True)
            st.var_dec = vd

            parse_condition(st, cond, line)

            assignment = Assignment()
            assignment.name = assig[0]
            assignment.value = parse_epression(assig[2::], True)
            st.var_assig = assignment

            statement_stack.append(st)

        elif tokens[0] in {"while-end", "if-end", "for-end"}:
            loop = statement_stack.pop()
            statement_stack[-1].statement_list.append(loop)

        elif len(tokens) >= 3 and tokens[1] == "=":
            st = Assignment()
            st.name = tokens[0]
            st.value = parse_epression(tokens[2::], True)
            statement_stack[-1].statement_list.append(st)

    ast_output = statement_stack[0].print_ast()
    print(ast_output)
    statement_stack.pop().execute()

    final_output = context.output1st + context.output2st
    return final_output


def to_bytes(code):
    return bytes(context.byte_code)


def makeShedule(input_text, filename="shedule.txt"):
    current_tick = 500
    with open(filename, "w", encoding="utf-8") as f:
        for char in input_text:
            step = 40
            current_tick += step
            f.write(f"{current_tick} {char}\n")
        current_tick += 40
        newline_code = ord('\n')
        f.write(f"{current_tick} {newline_code}\n")
    print(f"Расписание ввода сохранено в: {filename}")


def main(source="input"):
    with open(f"{source}.txt", encoding="utf-8") as f_debug:
        code = translate(f_debug)

    output_dir = "compiled"
    os.makedirs(output_dir, exist_ok=True)

    file_name = os.path.basename(source)

    target_path = os.path.join(output_dir, file_name)

    with open(f"{target_path}_debug.txt", "w", encoding="utf-8") as f:
        f.write(code)

    binary_data = to_bytes(code)

    with open(f"{target_path}.bin", "wb") as f:
        f.write(binary_data)

    config = {
        "input_port": INPUT_PORT_ADDR,
        "output_port": OUTPUT_PORT_ADDR,
        "data_memory_size": 32000,
        "command_memory_size": 32000,
        "entry_point": context.entry_point,
        "data_image": context.data_image
    }

    with open(f"{target_path}_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    print("Трансляция успешна")

    print(f"Объем бинарника (Размер бинарного файла): {len(binary_data)} байт.")

    print(f"Конфиг лежит и все остальное в папке compiled.Его имя = {source}_config.json")

    print("Байт-код:")
    cnt = 0
    for i in context.byte_code:
        print(f"{hex(cnt)[2:]}:{hex(i)[2:]}", end=" ")
        cnt += 1



if __name__ == "__main__":
    print("+++ ЗАПУСК ПРОЦЕДУРЫ ТРАНСЛЯЦИИ В БИНАРНЫЙ ГИМН +++")
    print("%ВЫБОР ПРОЦЕДУРЫ%\n1 // [ТРАНСЛЯЦИЯ И ЗАПУСК]\n2 // [ФОРМИРОВАНИЕ ОЧЕРЕДИ ВВОДА]")

    choice = input().strip()

    base_path = sys.argv[1] if len(sys.argv) > 1 else None

    if choice == "1":
        if base_path:
            main(source=base_path)
        else:
            print("--- Предупреждение: Путь не указан. Используется дефолтный 'input' ---")
            main(source="input")

    elif choice == "2":
        print("+++ УКАЖИТЕ ВАШЕ СООБЩЕНИЕ +++")
        user_message = input()

        output_dir = "compiled"
        os.makedirs(output_dir, exist_ok=True)

        if base_path:
            file_name = os.path.basename(base_path)
            schedule_file = os.path.join(output_dir, f"{file_name}_shedule.txt")
        else:
            schedule_file = os.path.join(output_dir, "shedule.txt")

        makeShedule(user_message, filename=schedule_file)
