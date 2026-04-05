#!/usr/bin/python3
"""Модель процессора, позволяющая выполнить машинный код полученный из программы
на языке Brainfuck.

Модель включает в себя три основных компонента:

- `DataPath` -- работа с памятью данных и вводом-выводом.

- `ControlUnit` -- работа с памятью команд и их интерпретация.

- и набор вспомогательных функций: `simulation`, `main`.
"""
from atexit import register
from typing import reveal_type

from isa import Opcode, opcode_to_binary, binary_to_opcode


class ALU:
    alu_output = None

    right = None
    "Правый вход в АЛУ"

    left = None
    "Левый вход в АЛУ"

    def __init__(self):
        alu_output = 0
        right = 0
        left = 0

    def add(self):
        self.alu_output = self.left + self.right

    def sub(self):
        self.alu_output = self.left - self.right

    def mul_step(self):
        pass

    def div_step(self):
        pass

    def inc_left(self):
        self.alu_output = self.left + 1

    def dec_left(self):
        self.alu_output = self.left - 1

    def bite_and(self):
        self.alu_output = self.left & self.right

    def bite_or(self):
        self.alu_output = self.left | self.right

    def bite_Xor(self):
        self.alu_output = self.left ^ self.right

    def bite_inv(self):
        self.alu_output = ~self.left


class DataPath:
    """Тракт данных (пассивный), включая: ввод/вывод, память и арифметику.

    ```text
     latch --------->+--------------+  addr   +--------+
     data            | data_address |---+---->|  data  |
     addr      +---->+--------------+   |     | memory |
               |                        |     |        |
           +-------+                    |     |        |
    sel -->|  MUX  |         +----------+     |        |
           +-------+         |                |        |
            ^     ^          |                |        |
            |     |          |        data_in |        | data_out
            |     +---(+1)---+          +---->|        |-----+
            |                |          |     |        |     |
            +---------(-1)---+          |  oe |        |     |
                                        | --->|        |     |
                                        |     |        |     |
                                        |  wr |        |     |
                                        | --->|        |     |
                                        |     +--------+     |
                                        |                    v
                                    +--------+  latch_acc +-----+
                          sel ----> |  MUX   |  --------->| acc |
                                    +--------+            +-----+
                                     ^   ^  ^                |
                                     |   |  |                +---(==0)---> zero
                                     |   |  |                |
                                     |   |  +---(+1)---------+
                                     |   |                   |
                                     |   +------(-1)---------+
                                     |                       |
            input -------------------+                       +---------> output
    ```

    - data_memory -- однопортовая, поэтому либо читаем, либо пишем.

    - input/output -- токенизированная логика ввода-вывода. Не детализируется в
      рамках модели.

    - input -- чтение может вызвать остановку процесса моделирования, если буфер
      входных значений закончился.

    Реализованные методы соответствуют сигналам защёлкивания значений:

    - `signal_latch_data_addr` -- защёлкивание адреса в памяти данных;
    - `signal_latch_acc` -- защёлкивание аккумулятора;
    - `signal_wr` -- запись в память данных;
    - `signal_output` -- вывод в порт.

    Сигнал "исполняется" за один такт. Корректность использования сигналов --
    задача `ControlUnit`.
    """
    address_memory = None
    "Регистр адреса, туда поступает значение из регистра а или б"

    stack = None
    "Стек...что еще сказать?"

    return_stack = None
    "Стек возврата...я все сказал"

    data_memory_size = None
    "Размер памяти данных."

    data_memory = None
    "Память данных. Инициализируется нулевыми значениями."

    register_a = None
    "Регистр А. Инициализируется нулём."

    register_b = None
    "Регистр В. Инициализируется нулём."

    ALU = None

    def __init__(self, data_memory_size, ALU):
        assert data_memory_size > 0, "Data_memory size should be non-zero"
        self.data_memory_size = data_memory_size
        self.data_memory = [0] * data_memory_size
        self.stack = []
        # TODO: сделать огр на размер стека
        self.data_address = 0
        self.register_a = 0
        self.register_b = 0
        self.ALU = ALU

    def signal_set_a(self, stack_or_ALU):
        if stack_or_ALU == True:
            self.register_a = self.stack.pop()
        else:
            self.register_a = self.ALU.alu_output

    def signal_set_b(self, stack_or_ALU):
        if stack_or_ALU == True:
            self.register_b = self.stack.pop()
        else:
            self.register_b = self.ALU.alu_output

    def signal_latch_AR(self, value):
        self.address_memory = value

    def read_from_memory(self):
        return self.data_memory[self.data_address]

    def stack_pop(self):
        return self.stack.pop()

    def stack_push(self, first_part, second_part, third_part, comm_value=[0, 0, 0, 0]):
        if first_part and second_part and not third_part:  # 1 1 0 A->TOP
            self.stack.append(self.register_a)
            self.register_a = 0
        elif first_part and not second_part and not third_part:  # 1 0 0 B->TOP
            self.stack.append(self.register_b)
            self.register_b = 0
        elif not first_part and second_part and not third_part:  # 0 1 0 ALU->TOP
            self.stack.append(self.ALU.alu_output)
        elif not first_part and not second_part and not third_part:  # 0 0 0 MEM->TOP
            word = self.data_memory[self.data_address]
            self.stack.append(word[3] << 0 | word[2] << 8 | word[1] << 16 | word[0] << 24)
        elif first_part and second_part and third_part:  # 1 1 1 COM_MEM->TOP
            print("мяу")
            word = comm_value
            self.stack.append(word[3] << 0 | word[2] << 8 | word[1] << 16 | word[0] << 24)

    def return_stack_pop(self):
        return self.return_stack.pop()

    def return_stack_push(self, first_part, second_part, third_part, comm_value=0):
        if first_part and second_part:  # 1 1 0 A->TOP
            self.stack_push(self.register_a)
        elif first_part and not second_part:  # 1 0 0 B->TOP
            self.stack_push(self.register_b)
        elif not first_part and second_part:  # 0 1 0 ALU->TOP
            self.stack_push(self.ALU.alu_output)
        elif not first_part and not second_part:  # 0 0 0 MEM->TOP
            word = self.data_memory[self.data_address]
            self.stack_push(word[3] << 0 | word[2] << 8 | word[1] << 16 | word[0] << 24)
        elif first_part and second_part and third_part:  # 1 1 1 COM_MEM->TOP
            word = self.data_memory[self.data_address]
            self.stack_push(comm_value)

    "Т.к. на входах в АЛУ у меня MUX, то и сигналы, собственно, должны поступать"

    def signal_set_left_ALU(self, is_stack):
        if is_stack:
            self.ALU.left = self.stack_pop()
        else:
            self.ALU.left = self.register_a

    def signal_set_right_ALU(self, is_stack):
        if is_stack:
            self.ALU.right = self.stack_pop()
        else:
            self.ALU.right = self.register_b


class ControlUnit:
    command_memory_size = None
    "Размер памяти команд."

    command_memory = None
    "Память команд. Инициализируется нулевыми значениями."

    program_counter = None
    "Счётчик команд. Инициализируется нулём."

    data_path = None
    "Блок обработки данных."

    _tick = None
    "Текущее модельное время процессора (в тактах). Инициализируется нулём."

    step = None
    "Шаг выполнения инструкции"

    def __init__(self, command_memory_size, data_path):
        self.command_memory_size = command_memory_size
        self.command_memory = [0] * command_memory_size
        self.data_path = data_path
        self.program_counter = 0
        self._tick = 0
        self.step = 0

    def tick(self):
        """Продвинуть модельное время процессора вперёд на один такт."""
        self._tick += 1

    def current_tick(self):
        """Текущее модельное время процессора (в тактах)."""
        return self._tick

    def signal_latch_program_counter(self, first_part, second_part):
        """Защёлкнуть новое значение счётчика команд.
        На входе в MUX 4 значения - для выбора нужно два параметра
        """
        "Пока что у меня фиксированная длина"
        if first_part and second_part:  # 1 1
            self.program_counter = self.data_path.return_stack_pop()
        elif first_part and not second_part:  # 1 0
            self.program_counter = self.data_path.return_stack_pop()  # TODO: изменить на аргумент инструкции для if
        elif not first_part and second_part:  # 0 1
            self.program_counter += 5
        elif not first_part and not second_part:  # 0 0
            self.program_counter += 1

    def process_next_tick(self):  # noqa: C901 # код имеет хорошо структурирован, по этому не проблема.

        """Основной цикл процессора. Декодирует и выполняет инструкцию.

        Обработка инструкции:

        1. Проверить `Opcode`.

        2. Вызвать методы, имитирующие необходимые управляющие сигналы.

        3. Продвинуть модельное время вперёд на один такт (`tick`).

        4. (если необходимо) повторить шаги 2-3.

        5. Перейти к следующей инструкции.

        Обработка функций управления потоком исполнения вынесена в
        `decode_and_execute_control_flow_instruction`.
        """
        instr = self.command_memory[self.program_counter]

        argue = self.command_memory[self.program_counter + 0x1:self.program_counter + 0x5]

        opcode = binary_to_opcode[instr]
        self.debug_print(opcode, argue)

        if opcode is Opcode.HALT:
            raise StopIteration()

        if opcode is Opcode.LIT:
            value = argue[3] << 0 | argue[2] << 8 | argue[1] << 16 | argue[0] << 24
            "А у меня все в Big-endian"
            self.data_path.stack_push(True, True, True, argue)
            self.signal_latch_program_counter(False, True)
            "По - хорошему, одновременно с чтением защелкиваем PC...но ладно"
            self.tick()
            return

        if opcode is Opcode.INC:
            if self.step == 0:
                self.data_path.signal_set_left_ALU(True)
                self.data_path.ALU.inc_left()
                self.step += 1
                self.tick()
                return
            if self.step == 1:
                self.data_path.stack_push(
                    False, True, False
                )
                self.step = 0
                self.signal_latch_program_counter(False, False)
                self.tick()
                return

        if opcode is Opcode.DEC:
            if self.step == 0:
                self.data_path.signal_set_left_ALU(True)
                self.step += 1
                self.tick()
                return
            if self.step == 1:
                self.data_path.stack_push(
                    False, True, False
                )
                self.step = 0
                self.signal_latch_program_counter(False, False)
                self.tick()
                return

        if opcode is Opcode.SUB:
            if self.step == 0:
                self.data_path.signal_set_left_ALU(True)
                self.data_path.signal_set_right_ALU(True)
                self.data_path.ALU.sub()
                self.step += 1
                self.tick()
                return
            if self.step == 1:
                self.data_path.stack_push(
                    False, True, False
                )
                self.step = 0
                self.signal_latch_program_counter(False, False)
                self.tick()
                return

        if opcode is Opcode.TOA:
            self.data_path.signal_set_a(True)
            self.signal_latch_program_counter(False, False)
            self.tick()
            return

        if opcode is Opcode.TOB:
            self.data_path.signal_set_b(True)
            self.signal_latch_program_counter(False, False)
            self.tick()
            return

        if opcode is Opcode.TOSTACKFROMA:
            self.data_path.stack_push(True, True, False)
            self.signal_latch_program_counter(False, False)
            self.tick()
            return

        if opcode is Opcode.TOSTACKFROMB:
            self.data_path.stack_push(True, True, False)
            self.signal_latch_program_counter(False, False)
            self.tick()
            return

        if opcode is Opcode.INV:
            if self.step == 0:
                self.data_path.signal_set_left_ALU(True)
                self.data_path.ALU.bite_inv()
                self.step += 1
                self.tick()
                return
            if self.step == 1:
                self.data_path.stack_push(
                    False, True, False
                )
                self.step = 0
                self.signal_latch_program_counter(False, False)
                self.tick()
                return
        if opcode is Opcode.AND:
            if self.step == 0:
                self.data_path.signal_set_left_ALU(True)
                self.data_path.signal_set_right_ALU(True)
                self.data_path.ALU.bite_and()
                self.step += 1
                self.tick()
                return
            if self.step == 1:
                self.data_path.stack_push(
                    False, True, False
                )
                self.step = 0
                self.signal_latch_program_counter(False, False)
                self.tick()
                return
        if opcode is Opcode.XOR:
            if self.step == 0:
                self.data_path.signal_set_left_ALU(True)
                self.data_path.signal_set_right_ALU(True)
                self.data_path.ALU.bite_Xor()
                self.step += 1
                self.tick()
                return
            if self.step == 1:
                self.data_path.stack_push(
                    False, True, False
                )
                self.step = 0
                self.signal_latch_program_counter(False, False)
                self.tick()
                return
        if opcode is Opcode.OR:
            if self.step == 0:
                self.data_path.signal_set_left_ALU(True)
                self.data_path.signal_set_right_ALU(True)
                self.data_path.ALU.bite_or()
                self.step += 1
                self.tick()
                return
            if self.step == 1:
                self.data_path.stack_push(
                    False, True, False
                )
                self.step = 0
                self.signal_latch_program_counter(False, False)
                self.tick()
                return

        if opcode is Opcode.ADD:
            if self.step == 0:
                self.data_path.ALU.signal_set_left(self.data_path.stack.pop())
                self.data_path.ALU.signal_set_right(self.data_path.stack.pop())
                self.data_path.ALU.add()
                self.step += 1
                self.tick()
                return
            if self.step == 1:
                self.data_path.stack_push(
                    self.data_path.ALU.alu_output
                )
                self.step = 0
                self.signal_latch_program_counter(False, False)
                self.tick()
                return

    def debug_print(self, instruction, arg):
        top = 0
        second = 0
        int_atg = arg[3] << 0 | arg[2] << 8 | arg[1] << 16 | arg[0] << 24
        try:
            top = self.data_path.stack[-1]
        except IndexError:
            pass
        try:
            second = self.data_path.stack[-2]
        except IndexError:
            pass
        print(
            f"Program counter: {self.program_counter}, reg_A: {self.data_path.register_a}, reg_B {self.data_path.register_b}\n"
            f"Stack top: {top}, stack second: {second}\n"
            f"Current tick: {self.current_tick() + 1}, current step = {self.step}, {not self.step}\n"
            f"Current command: {instruction.__str__()}, current agument = {int_atg}\n"
            f"<address> - <HEXCODE> - <mnemonic>\n"
            f"{self.program_counter} - {(opcode_to_binary.get(instruction)):02x}{(int_atg):08x} - <mnemonic>\n"
            f"----------Состояние регистров и памяти на начало такта!----------\n")


def run_cpu():
    alu = ALU()
    DP = DataPath(64, alu)
    CU = ControlUnit(64, DP)

    CU.command_memory[0] = 0x6    # LIT
    CU.command_memory[1] = 0x00
    CU.command_memory[2] = 0x00
    CU.command_memory[3] = 0x00
    CU.command_memory[4] = 0x0A
    CU.command_memory[5] = 0x6    # LIT
    CU.command_memory[6] = 0x00
    CU.command_memory[7] = 0x00
    CU.command_memory[8] = 0x00
    CU.command_memory[9] = 0x04
    CU.command_memory[10] = 0x02  # SUB
    CU.command_memory[11] = 0x00  # INC
    CU.command_memory[12] = 0x07  # TOA
    CU.command_memory[13] = 0x09  # TOSTACKFROMA
    CU.command_memory[14] = 0x12  # INV
    CU.command_memory[15] = 0x6   # LIT
    CU.command_memory[16] = 0xFF
    CU.command_memory[17] = 0xFF
    CU.command_memory[18] = 0xFF
    CU.command_memory[19] = 0xFF
    CU.command_memory[20] = 0x15  #OR
    CU.command_memory[21] = 0xFF  # HALT
    try:
        while CU.current_tick() < 100:
            CU.process_next_tick()
    except StopIteration:
        print("Усе")


if __name__ == "__main__":
    run_cpu()
