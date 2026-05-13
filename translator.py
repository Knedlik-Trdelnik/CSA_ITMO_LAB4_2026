from abc import ABC, abstractmethod
from datetime import datetime
from os import system

from isa import Opcode, opcode_to_binary, binary_to_opcode


class Expression(ABC):
    global context

    @abstractmethod
    def interpret(self):
        pass

    @abstractmethod
    def execute(self):
        pass


class Number(Expression):
    def __init__(self, number: int):
        self.number = number

    def interpret(self):
        return self.number

    def execute(self):
        val = self.number & 0xFFFFFFFF
        context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[Opcode.LIT]):02x}{val:08x} - lit: stack.push({self.number}))\n"

        context.byte_code.append(opcode_to_binary[Opcode.LIT])
        context.byte_code.extend(val.to_bytes(4, byteorder='big'))
        context.inc_comm_memory_pos(5)


class Variable(Expression):
    def __init__(self, name: str):
        self.name = name
        print(context.nameSpace.keys())

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


class Div(Expression):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def interpret(self):
        return (self.left.interpret() // self.right.interpret())

    def execute(self):
        self.left.execute()
        self.right.execute()
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.DIV]):02x} - div: stack.pop()\tstack.pop()\tstack.push(stack.top%stack.second]))\tstack.push(stack.top//stack.second]))\n"
        context.byte_code.append(opcode_to_binary[Opcode.DIV])
        context.inc_comm_memory_pos(1)


class Eq(Expression):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def interpret(self):
        return (self.left.interpret() % self.right.interpret())

    def execute(self):
        pass


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


class Equal(Expression):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right
        self.op_type = "=="
        self.jump_opcode = Opcode.IF

    def interpret(self):
        return int(self.left.interpret() == self.right.interpret())

    def execute(self):
        self.left.execute()
        self.right.execute()
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.SUB]):02x} - sub: \tstack.pop()\tstack.pop()\tstack.push(stack.top-stack.second)\n"
        context.byte_code.append(opcode_to_binary[Opcode.SUB])
        context.inc_comm_memory_pos(1)


class Context:
    data_memory_pos = 0  # на дата-мемори указатель  ( свободная ячейка) 32 бита
    comm_memory_pos = 0  # указатель  на дата-мемори( свободная ячейка) 8 бит
    nameSpace = dict()  # пространство имен переменных \\где какая переменнная лежит\
    nameValue = dict()  # имитация памяти TODO: а нужна вообще?
    nameType = dict()  # для соблюдения типизации
    output1st = "---------data_memory_pos-32-bit---\n"
    output2st = "---------command_memory---8-bit---\n<address> - <HEXCODE> - <mnemonic>\n"
    byte_code = bytearray()

    def saveLong(self, name, value, type="долгоцело"):
        self.nameValue[name] = value
        self.nameSpace[name] = self.data_memory_pos
        self.nameType[name] = type
        self.data_memory_pos += 2

        pass

    def saveInt(self, name, value, type="цело"):
        self.nameValue[name] = value
        self.nameSpace[name] = self.data_memory_pos
        self.nameType[name] = type
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


class Program(Statement):
    def execute(self):
        for _ in self.statement_list:
            _.execute()


class Entry_Point(Statement):
    def execute(self):
        for _ in self.statement_list:
            _.execute()


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
                if abs(self.value.interpret()) > 2 ** 31 - 1:
                    raise KeyError(f"ашипка: выражение, присваиваемое {self.name}, находится вне ОДЗ 32-битного int`а")
                context.rewrite(self.name, self.value.interpret())
                addr = context.nameSpace[self.name] & 0xFFFFFFFF
                context.output2st += f"0x{context.comm_memory_pos:02x}-0x{context.comm_memory_pos + 4:02x} - 0x{(opcode_to_binary[Opcode.STORE]):02x}{addr:08x} - store: mem[{context.nameSpace[self.name]}] <- stack.pop()\n"

                context.byte_code.append(opcode_to_binary[Opcode.STORE])
                context.byte_code.extend(addr.to_bytes(4, byteorder='big'))
                context.inc_comm_memory_pos(5)
                print(f"Новое значение = {self.value.interpret()}")
            elif var_type == "долгоцело":
                pass
            elif var_type == "грамота":
                pass


class Halt(Statement):
    def execute(self):
        context.output2st += f"0x{context.comm_memory_pos:02x} - 0x{(opcode_to_binary[Opcode.HALT]):02x} - halt\n"
        context.byte_code.append(opcode_to_binary[Opcode.HALT])
        context.inc_comm_memory_pos(1)


class If(Statement):
    def __init__(self):
        super().__init__()
        self.condition: Expression = None

    def execute(self):
        self.condition.execute()

        op = Opcode.IF if isinstance(self.condition, Equal) else Opcode.MIF
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


class While(Statement):
    def __init__(self):
        super().__init__()
        self.condition: Expression = None

    def execute(self):
        begin_addr = context.comm_memory_pos
        self.condition.execute()

        op = Opcode.IF if isinstance(self.condition, Equal) else Opcode.MIF
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

        op = Opcode.IF if isinstance(self.condition, Equal) else Opcode.MIF
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
    def execute(self):
        pass


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
    print(tokens)

    while check_next_highest_op(tokens):
        first_index, second_index = check_next_highest_op(tokens)
        subtokens = tokens[first_index + 1:second_index]

        print(subtokens)
        print(tokens)
        print(first_index, second_index)
        subexspression = parse_epression(subtokens, True)
        tokens[first_index:second_index + 1] = " "
        tokens[first_index] = subexspression

    while check_next_hight_op(tokens):
        i = check_next_hight_op(tokens)
        print(tokens)
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
        print(tokens)
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


def parse_token(token, tokens=[], index=0):
    if isinstance(token, Expression):
        return token
    if token is None:
        return None

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
        print(statement_stack)
        print(line)
        if (line == "\n"):
            continue
        print(line.strip())
        try:
            index_of_end = line.index(";")
        except ValueError:
            raise KeyError(f"|||{line}||| - нет ; на конце")
        tokens = line[:index_of_end].split(" ")

        if tokens[0] == "main":
            main = Entry_Point()
            statement_stack.append(main)

        elif tokens[0] == "main-end":
            if isinstance(statement_stack[-1], Entry_Point):
                main = statement_stack.pop()
                main.statement_list.append(Halt())
                statement_stack[-1].statement_list.append(
                    main
                )
            else:
                print(statement_stack)
                raise KeyError("Неправильная стуктура вложенности!")

        print(tokens)

        if True:
            if tokens[0] in {"цело", "долгоцело", "грамота"} and ("читай_память" not in line) and (
                    "пиши_память" not in line):
                st = Variable_Declaration()
                st.type = tokens[0]
                st.name = tokens[1]
                st.value = parse_epression(tokens[3::], True)

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

            elif tokens[0] == "while-end" or tokens[0] == "if-end" or tokens[0] == "for-end":
                loop = statement_stack.pop()
                statement_stack[-1].statement_list.append(
                    loop
                )
            elif len(tokens) >= 3:
                # Обновил проверку приоритетов or/and
                if (tokens[1] == "=") and ("читай_память" not in line) and ("пиши_память" not in line):
                    st = Assignment()
                    st.name = tokens[0]
                    st.value = parse_epression(tokens[2::], True)
                    statement_stack[-1].statement_list.append(st)

    statement_stack.pop().execute()

    final_output = context.output1st + context.output2st
    print("Состояния переменных:")
    print(context.nameValue)
    return final_output

def to_bytes(code):

    return bytes(context.byte_code)


def main(source="input.txt", target="program", test="test.txt"):
    with open(source, encoding="utf-8") as f_debug:
        code = translate(f_debug)

    with open(test, "w", encoding="utf-8") as f:
        f.write(code)

    binary_data = to_bytes(code)

    with open(target + ".bin", "wb") as f:
        f.write(binary_data)

    print(f"Успешно! Размер бинарного файла: {len(binary_data)} байт.")


if __name__ == "__main__":
    main()
