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
        context.output2st += f"{context.comm_memory_pos}-{context.comm_memory_pos + 4} - 0x{(opcode_to_binary[Opcode.LIT]):02x}{self.number:08x} - lit: stack.push({self.number}))\n"
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
        context.output2st += f"{context.comm_memory_pos}-{context.comm_memory_pos + 4} - 0x{(opcode_to_binary[Opcode.LOAD]):02x}{context.nameSpace[self.name]:08x} - load: stack.push(mem[{context.nameSpace[self.name]}]))\n"
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
        context.output2st += f"{context.comm_memory_pos} - 0x{(opcode_to_binary[Opcode.ADD]):02x} - add: \tstack.pop()\tstack.pop()\tstack.push(stack.top+stack.second]))\n"
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
        context.output2st += f"{context.comm_memory_pos} - 0x{(opcode_to_binary[Opcode.SUB]):02x} - sub: \tstack.pop()\tstack.pop()stack.push(stack.top-stack.second]))\n"
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
        context.output2st += f"{context.comm_memory_pos} - 0x{(opcode_to_binary[Opcode.MUL]):02x} - mul: \tstack.pop()\tstack.pop()stack.push(stack.top*stack.second]))\n"
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
        context.output2st += f"{context.comm_memory_pos} - 0x{(opcode_to_binary[Opcode.DIV]):02x} - div: stack.pop()\tstack.pop()\tstack.push(stack.top%stack.second]))\tstack.push(stack.top//stack.second]))\n"
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
        context.output2st += f"{context.comm_memory_pos} - 0x{(opcode_to_binary[Opcode.SUB]):02x} - sub (stack.top-stack.second)\n"
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
        context.output2st += f"{context.comm_memory_pos} - 0x{(opcode_to_binary[Opcode.SUB]):02x} - sub (stack.top-stack.second)\n"
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
        context.output2st += f"{context.comm_memory_pos} - 0x{(opcode_to_binary[Opcode.SUB]):02x} - sub: \tstack.pop()\tstack.pop()\tstack.push(stack.top-stack.second)\n"
        context.inc_comm_memory_pos(1)


class Context:
    data_memory_pos = 0  # на дата-мемори указатель  ( свободная ячейка) 32 бита
    comm_memory_pos = 0  # указатель  на дата-мемори( свободная ячейка) 8 бит
    nameSpace = dict()  # пространство имен переменных \\где какая переменнная лежит\
    nameValue = dict()  # имитация памяти TODO: а нужна вообще?
    nameType = dict()  # для соблюдения типизации
    output1st = "---------data_memory_pos-32-bit---\n"
    output2st = "---------command_memory---8-bit---\n<address> - <HEXCODE> - <mnemonic>\n"

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
            # context.output2st += f"{context.comm_memory_pos}-{context.comm_memory_pos + 4} - 0x{(opcode_to_binary[Opcode.LIT]):02x}{self.value.interpret():08x} - lit: stack.push({self.value.interpret()}))\n"
            self.value.execute()
            context.saveInt(self.name, self.value.interpret())
            context.output2st += f"{context.comm_memory_pos}-{context.comm_memory_pos + 4} - 0x{(opcode_to_binary[Opcode.STORE]):02x}{context.data_memory_pos - 1:08x} - store: mem[{context.data_memory_pos - 1}] <- stack.pop()\n"
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
                context.output2st += f"{context.comm_memory_pos}-{context.comm_memory_pos + 4} - 0x{(opcode_to_binary[Opcode.STORE]):02x}{context.nameSpace[self.name]:08x} - store: mem[{context.nameSpace[self.name]}] <- stack.pop()\n"
                context.inc_comm_memory_pos(5)
                print(f"Новое значение = {self.value.interpret()}")
            elif var_type == "долгоцело":
                pass
            elif var_type == "грамота":
                pass


class Halt(Statement):
    def execute(self):
        context.output2st += f"{context.comm_memory_pos} - 0x{(opcode_to_binary[Opcode.HALT]):02x} - halt\n"
        context.inc_comm_memory_pos(1)


class If(Statement):
    def __init__(self):
        super().__init__()
        self.condition: Expression = None
        self.body = []

    def execute(self):
        self.condition.execute()

        # Определяем, какой опкод прыжка использовать (MIF для < > или IF для ==)
        # Если в условии нет jump_opcode, по умолчанию берем IF
        op = None
        if isinstance(self.condition, Equal):
            op = Opcode.IF
        else:
            op = Opcode.MIF
        end_label = f"<if-end-{id(self)}>"
        if isinstance(self.condition, Equal):
            '''
            end_label потооом изменится
            '''
            context.output2st += f"{context.comm_memory_pos}-{context.comm_memory_pos + 4} - 0x{(opcode_to_binary[op]):02x}{end_label} - jump to {end_label} if stack.pop == 0\n"
        else:
            context.output2st += f"{context.comm_memory_pos}-{context.comm_memory_pos + 4} - 0x{(opcode_to_binary[op]):02x}{end_label} - jump to {end_label} if stack.pop >= 0\n"

        context.inc_comm_memory_pos(5)

        condition_result = self.condition.interpret()
        if condition_result != 0:
            for stmt in self.body:
                stmt.execute()
        else:
            old_values = context.nameValue.copy()
            for stmt in self.body:
                stmt.execute()
            context.nameValue = old_values

        context.output2st = context.output2st.replace(end_label, str(f"{context.comm_memory_pos:08x}"))


class While(Statement):
    def __init__(self):
        super().__init__()
        self.condition: Expression = None
        self.body = []

    def execute(self):
        begin_addr = context.comm_memory_pos  # чтобы прыгать обратон
        self.condition.execute()
        op = None
        if isinstance(self.condition, Equal):
            op = Opcode.IF
        else:
            op = Opcode.MIF
        # Определяем, какой опкод прыжка использовать (MIF для < > или IF для ==)

        end_label = f"<while-end-{id(self)}>"
        if isinstance(self.condition, Equal):
            '''
            end_label потооом изменится
            '''
            context.output2st += f"{context.comm_memory_pos}-{context.comm_memory_pos + 4} - 0x{(opcode_to_binary[op]):02x}{end_label} - jump to {end_label} if stack.pop == 0\n"
        else:
            context.output2st += f"{context.comm_memory_pos}-{context.comm_memory_pos + 4} - 0x{(opcode_to_binary[op]):02x}{end_label} - jump to {end_label} if stack.pop >= 0\n"

        context.inc_comm_memory_pos(5)

        condition_result = self.condition.interpret()
        if condition_result != 0:
            for stmt in self.body:
                stmt.execute()
        else:
            old_values = context.nameValue.copy()
            for stmt in self.body:
                stmt.execute()
            context.nameValue = old_values

        context.output2st += f"{context.comm_memory_pos}-{context.comm_memory_pos + 4}  - 0x{(opcode_to_binary[Opcode.JMP]):02x}{begin_addr:08x} - jump to {begin_addr}\n"
        context.inc_comm_memory_pos(5)
        end_addr = context.comm_memory_pos
        context.output2st = context.output2st.replace(end_label, str(f"{end_addr:08x}"))


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
    for i in range(first_index + 1, len(tokens)):  # + 1, так как первую ( нам не нужно смотреть
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
    '''

    :param expression: ожидается вход: массив токенов
    :return: выражение, котоое можно вычеслить
    '''
    "1 + 3 * 2 * 2 : 3"
    tokens = []
    if not isRecursion:
        tokens = expression.replace(" ", "")
        tokens = tokens.split(" ")
    else:
        tokens = expression
    print(tokens)
    '''
    найдем сначала все умножения/деления и превратим в объекты
    но, конечно, сначала все внутри ( )
    '''
    while check_next_highest_op(tokens):
        first_index, second_index = check_next_highest_op(tokens)
        subtokens = tokens[first_index + 1:second_index]  # если у меня ( 1 + 3 ) то я отправлю парситься 1 + 3

        print(subtokens)
        print(tokens)
        print(first_index, second_index)
        subexspression = parse_epression(subtokens, True)
        tokens[
            first_index:second_index + 1] = " "  # особенности языка)))  must assign iterable to extended slice.Дескать, с обоих сторон нужен итерируемый объект, но заглушку я заменю объектом
        tokens[first_index] = subexspression

    while check_next_hight_op(tokens):
        i = check_next_hight_op(tokens)
        print(tokens)
        # print(i)
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
        if left_token is not Expression and not None:
            left_token = parse_token(left_token)
        if right_token is not Expression and not None:
            right_token = parse_token(right_token)
        epx.left = left_token
        epx.right = right_token
        tokens[i] = (epx)
        tokens.pop(i - 1)
        tokens.pop(i)  # правый элемент на i+1, но я уже 1 удалил, так что i+1-1=1

    while check_next_low_op(tokens):
        i = check_next_low_op(tokens)
        print(tokens)
        # print(i)
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

        if left_token is not Expression and not None:
            left_token = parse_token(left_token)
        if right_token is not Expression and not None:
            right_token = parse_token(right_token)
        epx.left = left_token
        epx.right = right_token
        tokens[i] = (epx)
        tokens.pop(i - 1)
        tokens.pop(i)  # правый элемент на i+1 , но я уже 1 удалил, так что i+1-1=1
    # костыль, если приходит одно число
    for _ in range(len(tokens)):
        if not isinstance(tokens[_], Expression):
            tokens[_] = parse_token(tokens[_])
    '''
    print(tokens)
    print(tokens[0].left)
    print(tokens[0].right)
    print(tokens[0].interpret())
    '''
    final_expression = tokens[0]
    return final_expression  # в конечном итоге останется 1 операция


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


def translate(file):
    global context
    program = Program()
    main = None
    loop = None

    read_main = False
    read_fucns = False
    read_loop = False
    for line in file:
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
            read_main = True
            main = Entry_Point()
            program.statement_list.append(main)
        elif tokens[0] == "main-end":
            main.statement_list.append(Halt())
            read_main = False
        print(tokens)

        '''
        Начинается намазюк
        '''
        if read_main or read_loop:
            if tokens[0] in {"цело", "долгоцело", "грамота"}:
                st = Variable_Declaration()
                st.type = tokens[0]
                st.name = tokens[1]
                st.value = parse_epression(tokens[3::], True)
                if read_main:
                    main.statement_list.append(st)
                elif read_loop:
                    loop.body.append(st)
            elif tokens[0] == "if":
                read_loop = True
                st = If()
                loop = st
                condition = tokens[2:-1]

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
                main.statement_list.append(st)
            elif tokens[0] == "if-end":
                loop = None
                read_loop = False
            elif tokens[0] == "while":
                read_loop = True
                st = While()
                loop = st
                condition = tokens[2:-1]

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
                main.statement_list.append(st)
            elif tokens[0] == "while-end":
                loop = None
                read_loop = False
            elif len(tokens) >= 3:
                if (tokens[1] == "="):
                    st = Assignment()
                    st.name = tokens[0]
                    st.value = parse_epression(tokens[2::], True)
                    if read_loop:
                        loop.body.append(st)
                    elif read_main:
                        main.statement_list.append(st)

    print(program.statement_list[0].statement_list)
    program.execute()
    final_output = context.output1st + context.output2st
    print("Состояния переменных:")
    print(context.nameValue)
    return final_output


def main(source="input.txt", target="_", test="test.txt"):
    """Функция запуска транслятора. Параметры -- исходный и целевой файлы."""
    f = open(source, encoding="utf-8")

    code = translate(f)
    # binary_code = to_bytes(code)
    # hex_code = to_hex(code)
    with open(test, "w", encoding="utf-8") as f:
        f.write(code)
    '''
    
    with open(target + ".hex", "w") as f:
        f.write(hex_code)
    '''
    # print("source LoC:", len(source.split("\n")), "code instr:", len(code))


if __name__ == "__main__":
    # parse_epression("((1+3)*2)*(2-1)")
    '''
    assert len(sys.argv) == 3, "Wrong arguments: translator_asm.py <input_file> <target_file>"
    _, source, target = sys.argv
    '''
    main()
