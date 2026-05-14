from isa import Opcode, opcode_to_binary, binary_to_opcode
import json
import sys

class ALU:
    alu_output = None
    right = None
    left = None

    flag_z = False
    flag_n = False

    def __init__(self):
        self.alu_output = 0
        self.right = 0
        self.left = 0
        self.flag_z = False
        self.flag_n = False

    def update_flags(self, value):
        """Обновляет флаги Z и N на основе переданного значения."""
        self.flag_z = (value == 0)
        self.flag_n = (value < 0)

    def pass_through(self):
        self.alu_output = self.left
        self.update_flags(self.alu_output)

    def add(self):
        self.alu_output = self.left + self.right
        self.update_flags(self.alu_output)

    def sub(self):
        self.alu_output = self.right -self.left
        self.update_flags(self.alu_output)

    def mul_step(self):
        self.update_flags(self.alu_output)
        pass

    def div_step(self):
        self.update_flags(self.alu_output)
        pass

    def inc_left(self):
        self.alu_output = self.left + 1
        self.update_flags(self.alu_output)

    def dec_left(self):
        self.alu_output = self.left - 1
        self.update_flags(self.alu_output)

    def bite_and(self):
        self.alu_output = self.left & self.right
        self.update_flags(self.alu_output)

    def bite_or(self):
        self.alu_output = self.left | self.right
        self.update_flags(self.alu_output)

    def bite_Xor(self):
        self.alu_output = self.left ^ self.right
        self.update_flags(self.alu_output)

    def bite_inv(self):
        self.alu_output = ~self.left
        self.update_flags(self.alu_output)

    def bite_lshift(self):
        self.alu_output = self.left << 1
        self.update_flags(self.alu_output)

    def bite_rshift(self):
        self.alu_output = self.left >> 1
        self.update_flags(self.alu_output)


class DataPath:
    """Тракт данных (пассивный), включая: ввод/вывод, память и арифметику.
    - data_memory_pos -- однопортовая, поэтому либо читаем, либо пишем.

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
    input_buffer = None
    output_buffer = None

    IO_INPUT_ADDR = None
    IO_OUTPUT_ADDR = None
    """ 
    Для MMM
    """

    address_register = None
    "Регистр адреса, туда поступает значение из регистра а"

    stack = None
    "Стек...что еще сказать?"

    stack_pointer = 0

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

    def __init__(self, data_memory_size, alu, input_port, output_port, input_data=""):
        self.data_memory_size = data_memory_size
        self.data_memory = [0] * data_memory_size
        self.return_stack = []
        self.stack = []
        self.address_register = 0
        self.register_a = 0
        self.register_b = 0
        self.ALU = alu


        self.IO_INPUT_ADDR = input_port
        self.IO_OUTPUT_ADDR = output_port

        self.input_buffer = list(input_data)
        self.output_buffer = []

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

    def read_from_memory(self):
        """Чтение из памяти с дешифратором адреса (Memory-Mapped I/O)"""
        addr = self.address_register
        if addr == self.IO_INPUT_ADDR:
            if len(self.input_buffer) == 0:
                raise EOFError("Входной буфер пуст! Остановка.")
            symbol = self.input_buffer.pop(0)
            print(f"[I/O] Прочитан символ: '{symbol}' (значение = {ord(symbol)})")
            return ord(symbol)
        elif addr == self.IO_OUTPUT_ADDR:
            raise KeyError("Cannot read from output!")
        else:
            return self.data_memory[addr]

    def write_to_memory(self):
        """Запись в память с дешифратором адреса (Memory-Mapped I/O)"""
        addr = self.address_register
        value = self.stack_pop()
        if addr == self.IO_OUTPUT_ADDR:
            char = chr(value & 0xFF)
            self.output_buffer.append(value)
            print(f"[I/O] Выведен символ: '{char}' (значение =  {value})")
        elif addr == self.IO_INPUT_ADDR:
            raise KeyError("Cannot write to input!")
        else:
            self.data_memory[addr] = value

    def stack_pop(self):

        return self.stack.pop()

    def stack_push(self, first_part, second_part, third_part, comm_value=0):
        if first_part and second_part and not third_part:  # 1 1 0 A->TOP
            self.stack.append(self.register_a)
            self.register_a = 0
        elif first_part and not second_part and not third_part:  # 1 0 0 B->TOP
            self.stack.append(self.register_b)
            self.register_b = 0
        elif not first_part and second_part and not third_part:  # 0 1 0 ALU->TOP
            self.stack.append(self.ALU.alu_output)
        elif not first_part and not second_part and not third_part:  # 0 0 0 MEM->TOP
            self.stack.append(comm_value)
        elif first_part and second_part and third_part:  # 1 1 1 COM_MEM->TOP
            self.stack.append(comm_value)
        elif first_part and not second_part and third_part:  # 1 0 1 R_STAK.POP->TOP
            self.stack.append(self.return_stack_pop())

    def stack_dup(self):
        self.stack.append(self.stack[-1])

    # TODO: переписать на использование регистра B как буфера
    def stack_over(self):
        top = self.stack.pop()
        second = self.stack.pop()
        self.stack.append(top)
        self.stack.append(second)

    def return_stack_pop(self):
        return self.return_stack.pop()

    def return_stack_push(self, from_PC=False, PC_VAL=0):
        if not from_PC:
            self.return_stack.append(self.stack.pop())
            return
        self.return_stack.append(PC_VAL)

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

    def signal_latch_addres_register(self, a_or_cu, cu_value=0):
        if a_or_cu == True:
            self.address_register = self.register_a
        else:
            self.address_register = cu_value


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

    def __init__(self, command_memory_size, data_path, entry_point=0):
        self.command_memory_size = command_memory_size
        self.command_memory = [0] * command_memory_size
        self.data_path = data_path
        self.program_counter = entry_point
        self._tick = 0
        self.step = 0

    def tick(self):
        """Продвинуть модельное время процессора вперёд на один такт."""
        self._tick += 1

    def current_tick(self):
        """Текущее модельное время процессора (в тактах)."""
        return self._tick

    def signal_latch_program_counter(self, first_part, second_part, arg_value=0):
        """Защёлкнуть новое значение счётчика команд.
        На входе в MUX 4 значения - для выбора нужно два параметра.
        """
        if first_part and second_part:        # 1 1: Из стека возвратов (RET)
            self.program_counter = self.data_path.return_stack_pop()
        elif first_part and not second_part:  # 1 0: Переход по адресу (JMP, IF, CALL)
            self.program_counter = arg_value
        elif not first_part and second_part:  # 0 1: Пропуск 4 байт аргумента (LIT, LOAD, невыполненный IF)
            self.program_counter += 5
        elif not first_part and not second_part:  # 0 0: Обычная 1-байтовая инструкция
            self.program_counter += 1

    def process_next_tick(self):

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

            value = int.from_bytes(argue, byteorder='big', signed=True)
            "А у меня все в Big-endian"
            self.data_path.stack_push(True, True, True, value)
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

        if opcode is Opcode.DROP:
            self.data_path.stack_pop()
            self.signal_latch_program_counter(False, False)
            self.tick()
            return

        if opcode is Opcode.DUP:
            self.data_path.stack_dup()
            self.signal_latch_program_counter(False, False)
            self.tick()
            return

        if opcode is Opcode.OVER:
            self.data_path.stack_over()
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

        if opcode is Opcode.LSHIFT:
            if self.step == 0:
                self.data_path.signal_set_left_ALU(True)
                self.data_path.ALU.bite_lshift()
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
        if opcode is Opcode.RSHIFT:
            if self.step == 0:
                self.data_path.signal_set_left_ALU(True)
                self.data_path.ALU.bite_rshift()
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
                self.data_path.signal_set_left_ALU(True)
                self.data_path.signal_set_right_ALU(True)
                self.data_path.ALU.add()
                self.step += 1
                self.tick()
                return
            if self.step == 1:
                self.data_path.stack_push(False, True, False)
                self.step = 0
                self.signal_latch_program_counter(False, False)
                self.tick()
                return

        if opcode is Opcode.RINTOT:
            self.data_path.stack_push(True, False, True)
            self.signal_latch_program_counter(False, False)
            self.tick()
            return

        if opcode is Opcode.TINTOR:
            self.data_path.return_stack_push(False)
            self.signal_latch_program_counter(False, False)
            self.tick()
            return
        if opcode is Opcode.STORE:
            if self.step == 0:

                value = int.from_bytes(argue, byteorder='big', signed=True)

                self.data_path.signal_latch_addres_register(False, value)
                self.step += 1
                self.tick()
            if self.step == 1:
                self.data_path.write_to_memory()
                self.step = 0
                self.signal_latch_program_counter(False, True)
                self.tick()
                return
        if opcode is Opcode.LOAD:
            if self.step == 0:
                value = int.from_bytes(argue, byteorder='big', signed=True)

                self.data_path.signal_latch_addres_register(False, value)
                self.step += 1
                self.tick()
            if self.step == 1:
                val = self.data_path.read_from_memory()

                self.data_path.stack_push(False, False, False, comm_value=val)
                self.step = 0
                self.signal_latch_program_counter(False, True)
                self.tick()
                return
        if opcode is Opcode.JMP:
            value = int.from_bytes(argue, byteorder='big', signed=False)
            self.signal_latch_program_counter(True, False, value)
            self.tick()
            return

        if opcode is Opcode.IF:
            if self.step == 0:

                self.data_path.signal_set_left_ALU(True)
                self.data_path.ALU.pass_through()
                self.step += 1
                self.tick()
                return

            if self.step == 1:

                value = int.from_bytes(argue, byteorder='big', signed=False)

                if self.data_path.ALU.flag_z:
                    self.signal_latch_program_counter(True, False, value)
                else:
                    self.signal_latch_program_counter(False, True)

                self.step = 0
                self.tick()
                return

        if opcode is Opcode.MIF:
            if self.step == 0:

                self.data_path.signal_set_left_ALU(True)
                self.data_path.ALU.pass_through()
                self.step += 1
                self.tick()
                return

            if self.step == 1:

                value = int.from_bytes(argue, byteorder='big', signed=False)

                if not self.data_path.ALU.flag_n:
                    self.signal_latch_program_counter(True, False, value)
                else:
                    self.signal_latch_program_counter(False, True)

                self.step = 0
                self.tick()
                return
        if opcode is Opcode.CALL:
            value = int.from_bytes(argue, byteorder='big', signed=False)
            self.data_path.return_stack_push(from_PC=True, PC_VAL=self.program_counter + 5)
            self.signal_latch_program_counter(True, False, value)
            self.tick()
            return

        if opcode is Opcode.RET:

            self.signal_latch_program_counter(True, True)
            self.tick()
            return

        if opcode is Opcode.RINTOT:

            self.data_path.stack_push(True, False, True)
            self.signal_latch_program_counter(False, False)
            self.tick()
            return

        if opcode is Opcode.TINTOR:

            self.data_path.return_stack_push(from_PC=False)
            self.signal_latch_program_counter(False, False)
            self.tick()
            return

    def debug_print(self, instruction, arg):
        top = 0
        second = 0
        r_top = 0
        bytes = [arg[3], arg[2], arg[1], arg[0]]
        int_atg = int.from_bytes(bytes, byteorder='little', signed=True) #пасхалка
        try:
            top = self.data_path.stack[-1]
        except IndexError:
            pass
        try:
            second = self.data_path.stack[-2]
        except IndexError:
            pass
        try:
            r_top = self.data_path.return_stack[-1]
        except IndexError:
            pass
        print(
            f"Program counter: {self.program_counter}, reg_A: {self.data_path.register_a}, reg_B {self.data_path.register_b}\n"
            f"Stack top: {top}, stack second: {second} r_stack top : {r_top}\n"
            f"Current tick: {self.current_tick() + 1}, current step = {self.step}, {not self.step}\n"
            f"Current command: {instruction.__str__()}, current argument = {int_atg}\n"
            f"<address> - <HEXCODE> - <mnemonic>\n"
            f"{self.program_counter} - {(opcode_to_binary.get(instruction)):02x}{(int_atg):08x} - <mnemonic>\n"
            f"кусочек памяти - {self.data_path.data_memory[:32]}\n"
            f"----------Состояние регистров и памяти на начало такта!----------\n")


def run_cpu(code_file, input_file, config_file):

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    data_mem_size = config["data_memory_size"]
    cmd_mem_size = config["command_memory_size"]
    in_port = config["input_port"]
    out_port = config["output_port"]
    entry_point = config["entry_point"]

    with open(code_file, "rb") as f:
        binary_code = f.read()


    try:
        with open(input_file, "r", encoding="utf-8") as f:
            input_text = f.read()
    except FileNotFoundError:
        input_text = ""


    alu = ALU()
    dp = DataPath(data_mem_size, alu, in_port, out_port, input_text)
    cu = ControlUnit(cmd_mem_size, dp, entry_point=entry_point)


    for i in range(len(binary_code)):
        cu.command_memory[i] = binary_code[i]

    print("=== ЗАПУСК СИМУЛЯЦИИ ===")
    try:

        limit = 100000
        while cu.current_tick() < limit:
            cu.process_next_tick()
        print("Внимание: достигнут лимит тактов!")
    except StopIteration:
        print("Остановка: выполнена инструкция HALT.")
    except EOFError as e:
        print(f"Остановка: {e}")


    print("\n==============================")
    print("ВЫВОД ПРОГРАММЫ:")
    for i in dp.output_buffer:
        print(i, end=" ")
    print()
    print("==============================")
    print(f"Затрачено тактов: {cu.current_tick()}")


def main():

    if len(sys.argv) == 4:
        code_file = sys.argv[1]
        input_file = sys.argv[2]
        config_file = sys.argv[3]
    else:

        code_file = "program.bin"
        input_file = "input.txt"
        config_file = "config.json"

    run_cpu(code_file, input_file, config_file)


if __name__ == "__main__":
    main()
