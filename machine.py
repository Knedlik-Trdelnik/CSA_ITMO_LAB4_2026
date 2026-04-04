#!/usr/bin/python3
"""Модель процессора, позволяющая выполнить машинный код полученный из программы
на языке Brainfuck.

Модель включает в себя три основных компонента:

- `DataPath` -- работа с памятью данных и вводом-выводом.

- `ControlUnit` -- работа с памятью команд и их интерпретация.

- и набор вспомогательных функций: `simulation`, `main`.
"""

from isa import Opcode, opcode_to_binary, binary_to_opcode


class ALU:
    right = None
    "Правый вход в АЛУ"

    left = None
    "Левый вход в АЛУ"

    "Т.к. на входах в АЛУ у меня MUX, то и сигналы, собственно, должны поступать"

    def signal_latch_left(self, value):
        self.left = value

    def signal_latch_right(self, value):
        self.right = value

    def add(self):
        return self.right + self.left

    def sub(self):
        return self.right - self.left

    def mul_step(self):
        pass

    def div_step(self):
        pass

    def inc_left(self):
        pass

    def inc_right(self):
        return self.right + 1

    def inc_left(self):
        return self.left - 1


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

    data_address = None
    "Адрес в памяти данных. Инициализируется нулём."

    register_a = None
    "Регистр А. Инициализируется нулём."

    register_b = None
    "Регистр В. Инициализируется нулём."

    def __init__(self, data_memory_size):
        assert data_memory_size > 0, "Data_memory size should be non-zero"
        self.data_memory_size = data_memory_size
        self.data_memory = [0] * data_memory_size
        self.stack = []
        #TODO: сделать огр на размер стека
        self.data_address = 0
        self.register_a = 0
        self.register_b = 0

    def signal_latch_a(self, value):
        self.register_a = value

    def signal_latch_b(self, value):
        self.register_b = value

    def signal_latch_AR(self, value):
        self.address_memory = value

    def stack_pop(self):
        return self.stack.pop()

    def stack_push(self, value):
        return self.stack.append(value)

    def return_stack_pop(self):
        return self.return_stack.pop()

    def return_stack_push(self, value):
        return self.return_stack.push(value)


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

    def signal_latch_program_counter(self):
        """Защёлкнуть новое значение счётчика команд.

        Если `sel_next` равен `True`, то счётчик будет увеличен на единицу,
        иначе -- будет установлен в значение аргумента текущей инструкции.
        """
        "Пока что у меня фиксированная длина"

        self.program_counter += 5


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

        self.signal_latch_program_counter()
        "Одновременно с чтением защелкиваем"

        opcode = binary_to_opcode[instr]
        if opcode is Opcode.HALT:
            self.debug_print()
            raise StopIteration()

        if opcode is Opcode.LIT:
            value = argue[3] << 0 | argue[2] << 8 | argue[1] << 16 | argue[0] << 24
            "А у меня все в Big-endian"
            self.data_path.stack_push(value)
            self.tick()

            return
        "ОСТАЛЬНОЕ НЕ ГОТОВО!"
        if opcode is Opcode.JZ:
            if self.step == 0:
                addr = instr["arg"]
                self.data_path.signal_latch_acc()
                self.step = 1
                self.tick()
                return
            if self.step == 1:
                if self.data_path.zero():
                    self.signal_latch_program_counter(sel_next=False)
                else:
                    self.signal_latch_program_counter(sel_next=True)
                self.step = 0
                self.tick()
                return

        if opcode in {Opcode.RIGHT, Opcode.LEFT}:
            self.data_path.signal_latch_data_addr(opcode.value)
            self.signal_latch_program_counter(sel_next=True)
            self.step = 0
            self.tick()
            return

        if opcode in {Opcode.INC, Opcode.DEC, Opcode.INPUT}:
            if self.step == 0:
                self.data_path.signal_latch_acc()
                self.step = 1
                self.tick()
                return
            if self.step == 1:
                self.data_path.signal_wr(opcode.value)
                self.signal_latch_program_counter(sel_next=True)
                self.step = 0
                self.tick()
                return

        if opcode is Opcode.PRINT:
            if self.step == 0:
                self.data_path.signal_latch_acc()
                self.step = 1
                self.tick()
                return
            if self.step == 1:
                self.data_path.signal_output()
                self.signal_latch_program_counter(sel_next=True)
                self.step = 0
                self.tick()
                return

    def debug_print(self):
        print(f"Program counter: {self.program_counter}, reg_A: {self.data_path.register_a}, reg_B {self.data_path.register_b}\n"
              f"Stack top: {self.data_path.stack[-1]}, stack second: {self.data_path.stack[-2]}\n")


def run_cpu():
    alu = ALU()
    DP = DataPath(64)
    CU = ControlUnit(64, DP)

    CU.command_memory[0] = 0x4
    CU.command_memory[1] = 0x00
    CU.command_memory[2] = 0x00
    CU.command_memory[3] = 0x00
    CU.command_memory[4] = 0x0A
    CU.command_memory[5] = 0x4
    CU.command_memory[6] = 0x00
    CU.command_memory[7] = 0x00
    CU.command_memory[8] = 0x00
    CU.command_memory[9] = 0x04
    CU.command_memory[10] = 0xFF
    while CU.current_tick() < 100:
        CU.process_next_tick()


if __name__ == "__main__":
    run_cpu()
