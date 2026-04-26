import sys
from abc import ABC, abstractmethod


class Expression(ABC):
    @abstractmethod
    def interpret(self):
        pass


class Number(Expression):
    def __init__(self, number: int):
        self.number = number

    def interpret(self):
        return self.number


class Add(Expression):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def interpret(self):
        return (self.left.interpret() + self.right.interpret())


class Sub(Expression):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def interpret(self):
        return (self.left.interpret() - self.right.interpret())


class Mul(Expression):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def interpret(self):
        return (self.left.interpret() * self.right.interpret())


class Div(Expression):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def interpret(self):
        return (self.left.interpret() // self.right.interpret())


class Eq(Expression):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def interpret(self):
        return (self.left.interpret() % self.right.interpret())


math_op = {"*", "+", "-", ":", "%"}
high_op = {"*", ":", "%"}


def parse_epression(expression):

    line = "1 + 3 * 2"
    "line = 3 * 2 + 1"
    tokens = line.split()

    tokens_pos = 0
    print(tokens)
    '''
    найдем сначала все умножения/деления и превратим в объекты
    '''
    try:
        while tokens.index("*"):
            print(tokens)
            i = tokens.index("*")
            #print(i)
            token = tokens[i]
            left_token = None
            right_token = None
            epx = None
            if i != 0:
                left_token = tokens[i - 1]
            if i != len(tokens) - 1:
                right_token = tokens[i + 1]
            epx = Mul()
            if left_token is not Expression and not None:
                left_token = parse_token(left_token)
            if right_token is not Expression and not None:
                right_token = parse_token(right_token)
            epx.left = left_token
            epx.right = right_token
            tokens[i]=(epx)
            tokens.pop(i - 1)
            tokens.pop(i ) # правый элемент на i+1 , но я уже 1 удалил, так что i+1-1=1
    except ValueError:
        pass
    try:
        while tokens.index(":"):
            print(tokens)
            i = tokens.index(":")
            # print(i)
            token = tokens[i]
            left_token = None
            right_token = None
            epx = None
            if i != 0:
                left_token = tokens[i - 1]
            if i != len(tokens) - 1:
                right_token = tokens[i + 1]
            epx = Div()
            if left_token is not Expression and not None:
                left_token = parse_token(left_token)
            if right_token is not Expression and not None:
                right_token = parse_token(right_token)
            epx.left = left_token
            epx.right = right_token
            tokens[i] = (epx)
            tokens.pop(i - 1)
            tokens.pop(i)  # правый элемент на i+1 , но я уже 1 удалил, так что i+1-1=1
    except ValueError:
        pass
    try:
        while tokens.index("+"):
            print(tokens)
            i = tokens.index("+")
            # print(i)
            token = tokens[i]
            left_token = None
            right_token = None
            epx = None
            if i != 0:
                left_token = tokens[i - 1]
            if i != len(tokens) - 1:
                right_token = tokens[i + 1]
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
    except ValueError:
        pass
    try:
        while tokens.index("-"):
            print(tokens)
            i = tokens.index("-")
            # print(i)
            token = tokens[i]
            left_token = None
            right_token = None
            epx = None
            if i != 0:
                left_token = tokens[i - 1]
            if i != len(tokens) - 1:
                right_token = tokens[i + 1]
            epx = Sub()
            if left_token is not Expression and not None:
                left_token = parse_token(left_token)
            if right_token is not Expression and not None:
                right_token = parse_token(right_token)
            epx.left = left_token
            epx.right = right_token
            tokens[i] = (epx)
            tokens.pop(i - 1)
            tokens.pop(i)  # правый элемент на i+1 , но я уже 1 удалил, так что i+1-1=1
    except ValueError:
        pass
    try:
        while tokens.index("%"):
            print(tokens)
            i = tokens.index("%")
            # print(i)
            token = tokens[i]
            left_token = None
            right_token = None
            epx = None
            if i != 0:
                left_token = tokens[i - 1]
            if i != len(tokens) - 1:
                right_token = tokens[i + 1]
            epx = Eq()
            if left_token is not Expression and not None:
                left_token = parse_token(left_token)
            if right_token is not Expression and not None:
                right_token = parse_token(right_token)
            epx.left = left_token
            epx.right = right_token
            tokens[i] = (epx)
            tokens.pop(i - 1)
            tokens.pop(i)  # правый элемент на i+1 , но я уже 1 удалил, так что i+1-1=1
    except ValueError:
        pass

    print(tokens)
    print(tokens[0].left)
    print(tokens[0].right)
    print(tokens[0].interpret())


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
        return Number(int(token))


def translate():
    pass


def main(source, target):
    """Функция запуска транслятора. Параметры -- исходный и целевой файлы."""
    with open(source, encoding="utf-8") as f:
        source = f.read()

    code = translate(source)
    # binary_code = to_bytes(code)
    # hex_code = to_hex(code)
    '''
    with open(target, "wb") as f:
        f.write(binary_code)
    with open(target + ".hex", "w") as f:
        f.write(hex_code)
    '''
    print("source LoC:", len(source.split("\n")), "code instr:", len(code))


if __name__ == "__main__":
    parse_epression("23123123")

    assert len(sys.argv) == 3, "Wrong arguments: translator_asm.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
