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

    def mul(self):
        self.alu_output = self.left * self.right
        self.update_flags(self.alu_output)

    def div(self):
        if self.left == 0:
            self.alu_output = 0
        else:
            self.alu_output = self.right // self.left
        self.update_flags(self.alu_output)

    def mod(self):
        if self.left == 0:
            self.alu_output = 0
        else:
            self.alu_output = self.right % self.left
        self.update_flags(self.alu_output)

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

    def get_status(self):
        return (int(self.flag_n) << 1) | int(self.flag_z)

    def set_status(self, val):
        self.flag_n = bool((val >> 1) & 1)
        self.flag_z = bool(val & 1)


class DataPath:
    IE = None
    in_interrupt = None
    pending_interrupt = None
    input_schedule = None
    """
    Для прерываний
    """

    input_port_value = None
    output_buffer = None

    IO_INPUT_ADDR = None
    IO_OUTPUT_ADDR = None
    """ 
    Для MMio
    """

    address_register = None
    "Регистр адреса, туда поступает значение из регистра а"

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


    stack_size = 256
    stack_pointer = 0

    return_stack_size = 256
    return_stack_pointer = 0

    ALU = None

    def __init__(self, data_memory_size, alu, input_port, output_port, input_data=""):
        self.data_memory_size = data_memory_size
        self.data_memory = [0] * data_memory_size


        self.stack = [0] * self.stack_size
        self.stack_pointer = 0

        self.return_stack = [0] * self.return_stack_size
        self.return_stack_pointer = 0

        self.address_register = 0
        self.register_a = 0
        self.ALU = alu

        self.IO_INPUT_ADDR = input_port
        self.IO_OUTPUT_ADDR = output_port
        self.input_port_value = 0
        self.output_buffer = []

    def signal_set_a(self, stack_or_ALU):
        if stack_or_ALU:
            self.register_a = self.stack_pop()
        else:
            self.register_a = self.ALU.alu_output


    def read_from_memory(self):
        """Чтение из памяти с дешифратором адреса (Memory-Mapped I/O)"""
        addr = self.address_register
        if addr == self.IO_INPUT_ADDR:
            val = self.input_port_value
            char_repr = chr(val) if 32 <= val <= 126 else f"\\x{val:02x}"

            return val
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

        elif addr == self.IO_INPUT_ADDR:
            raise KeyError("Cannot write to input!")
        else:
            self.data_memory[addr] = value

    def stack_pop(self):
        """Аппаратное снятие со стека: сдвигаем указатель вниз и читаем память."""
        if self.stack_pointer <= 0:
            raise IndexError("Hardware Exception: Data Stack Underflow")
        self.stack_pointer -= 1
        return self.stack[self.stack_pointer]

    def stack_push(self, first_part, second_part, third_part, comm_value=0):
        """Аппаратная загрузка на стек: пишем в память и сдвигаем указатель вверх."""
        if self.stack_pointer >= self.stack_size:
            raise IndexError("Hardware Exception: Data Stack Overflow")

        val = 0
        if first_part and second_part and not third_part:  # 1 1 0 A->TOP
            val = self.register_a
            self.register_a = 0
        elif not first_part and second_part and not third_part:  # 0 1 0 ALU->TOP
            val = self.ALU.alu_output
        elif not first_part and not second_part and not third_part:  # 0 0 0 MEM->TOP
            val = comm_value
        elif first_part and second_part and third_part:  # 1 1 1 COM_MEM->TOP
            val = comm_value
        elif first_part and not second_part and third_part:  # 1 0 1 R_STAK.POP->TOP
            val = self.return_stack_pop()

        self.stack[self.stack_pointer] = val
        self.stack_pointer += 1

    def stack_dup(self):
        """Копирование вершины стека."""
        if self.stack_pointer <= 0 or self.stack_pointer >= self.stack_size:
            raise IndexError("Hardware Exception: Stack Pointer Out of Bounds")
        val = self.stack[self.stack_pointer - 1]
        self.stack[self.stack_pointer] = val
        self.stack_pointer += 1

    def stack_over(self):
        """
        Примечание: ваша предыдущая реализация работала как SWAP (меняла местами).
        Я сохранил эту логику для совместимости с вашей программой.
        """
        top = self.stack_pop()
        second = self.stack_pop()

        self.stack[self.stack_pointer] = top
        self.stack_pointer += 1
        self.stack[self.stack_pointer] = second
        self.stack_pointer += 1


    def return_stack_pop(self):
        if self.return_stack_pointer <= 0:
            raise IndexError("Hardware Exception: Return Stack Underflow")
        self.return_stack_pointer -= 1
        return self.return_stack[self.return_stack_pointer]

    def return_stack_push(self, from_PC=False, PC_VAL=0):
        if self.return_stack_pointer >= self.return_stack_size:
            raise IndexError("Hardware Exception: Return Stack Overflow")
        if not from_PC:
            val = self.stack_pop()
        else:
            val = PC_VAL
        self.return_stack[self.return_stack_pointer] = val
        self.return_stack_pointer += 1

    def return_stack_push_raw(self, val):
        """Служебный метод для сохранения флагов прерывания аппаратурой."""
        if self.return_stack_pointer >= self.return_stack_size:
            raise IndexError("Hardware Exception: Return Stack Overflow")
        self.return_stack[self.return_stack_pointer] = val
        self.return_stack_pointer += 1

    "Т.к. на входах в АЛУ у меня MUX, то и сигналы, собственно, должны поступать"

    def signal_set_left_ALU(self, is_stack):
        if is_stack:
            self.ALU.left = self.stack_pop()
        else:
            self.ALU.left = self.register_a

    def signal_set_right_ALU(self, is_stack = True):
        if is_stack:
            self.ALU.right = self.stack_pop()

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


    IE = None
    in_interrupt = None
    pending_interrupt = None
    input_schedule = None
    entering_interrupt = None
    int_step = None
    log_limit = 0

    def __init__(self, command_memory_size, data_path, entry_point=0,  input_schedule=None):
        self.command_memory_size = command_memory_size
        self.command_memory = [0] * command_memory_size
        self.data_path = data_path
        self.program_counter = entry_point
        self._tick = 0
        self.step = 0

        self.log_limit = 100
        self.IE = True
        self.in_interrupt = False
        self.pending_interrupt = False
        self.input_schedule = input_schedule if input_schedule else []

        self.entering_interrupt = False
        self.int_step = 0

    def check_interrupts(self):

        while len(self.input_schedule) > 0 and self._tick >= self.input_schedule[0][0]:
            tick_val, char_val = self.input_schedule.pop(0)
            if char_val == "10":
                self.data_path.input_port_value = 10
            else:
                self.data_path.input_port_value = ord(char_val)

            self.pending_interrupt = True

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

        if self.step == 0:
            self.check_interrupts()

        if self.step == 0 and not self.entering_interrupt:
            if self.pending_interrupt and self.IE:
                self.entering_interrupt = True
                self.int_step = 0
                self.pending_interrupt = False
                self.IE = False
                self.in_interrupt = True

        if self.entering_interrupt:
            if self.int_step == 0:
                self.data_path.return_stack_push(from_PC=True, PC_VAL=self.program_counter)
                self.debug_print_interrupt("INT ENTRY: PUSH PC -> RS")
                self.int_step += 1
                self.tick()
                return
            elif self.int_step == 1:
                sr = self.data_path.ALU.get_status()
                self.data_path.return_stack_push_raw(sr)
                self.debug_print_interrupt("INT ENTRY: PUSH SR -> RS")
                self.int_step += 1
                self.tick()
                return
            elif self.int_step == 2:
                self.data_path.signal_latch_addres_register(False, 0)
                self.debug_print_interrupt("INT ENTRY: AR <- 0")
                self.int_step += 1
                self.tick()
                return
            elif self.int_step == 3:
                val = self.data_path.read_from_memory()
                self.data_path.stack_push(False, False, False, comm_value=val)
                self.debug_print_interrupt("INT ENTRY: DS.PUSH( MEM[AR] )")
                self.int_step += 1
                self.tick()
                return
            elif self.int_step == 4:
                self.program_counter = self.data_path.stack_pop()
                self.entering_interrupt = False
                self.debug_print_interrupt("INT ENTRY: PC <- DS.POP()")
                self.tick()
                return

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

        if opcode is Opcode.TOSTACKFROMA:
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

        if opcode is Opcode.ALOAD:
            if self.step == 0:
                self.data_path.signal_latch_addres_register(True)
                self.step += 1
                self.tick()
                return
            if self.step == 1:
                val = self.data_path.read_from_memory()
                self.data_path.stack_push(False, False, False, comm_value=val)
                self.step = 0
                self.signal_latch_program_counter(False, False)
                self.tick()
                return
        if opcode is Opcode.ALOADP:
            if self.step == 0:

                self.data_path.signal_latch_addres_register(True)
                self.step += 1
                self.tick()
                return

            if self.step == 1:

                val = self.data_path.read_from_memory()
                self.data_path.stack_push(False, False, False, comm_value=val)
                self.step += 1
                self.tick()
                return

            if self.step == 2:

                self.data_path.register_a += 1

                self.step = 0
                self.signal_latch_program_counter(False, False)  # PC += 1
                self.tick()
                return
        if opcode is Opcode.IRET:
            if self.step == 0:

                sr = self.data_path.return_stack_pop()

                self.data_path.ALU.set_status(sr)
                self.step += 1
                self.tick()
                return
            if self.step == 1:
                self.signal_latch_program_counter(True, True)  # RS -> PC
                self.IE = True
                self.in_interrupt = False
                self.step = 0
                self.tick()
                return

        if opcode is Opcode.IRET:
            if self.step == 0:
                sr = self.data_path.return_stack.pop()
                self.data_path.ALU.set_status(sr)
                self.step += 1
                self.tick()
                return
            if self.step == 1:
                self.signal_latch_program_counter(True, True)  # RS -> PC
                self.IE = True
                self.in_interrupt = False
                self.step = 0
                self.tick()
                return
        if opcode is Opcode.EI:
            self.IE = True
            self.signal_latch_program_counter(False, False)
            self.tick()
            return

        if opcode is Opcode.DI:
            self.IE = False
            self.signal_latch_program_counter(False, False)
            self.tick()
            return
        if opcode is Opcode.NIF:
            if self.step == 0:
                self.data_path.signal_set_left_ALU(True)
                self.data_path.ALU.pass_through()
                self.step += 1
                self.tick()
                return

            if self.step == 1:
                value = int.from_bytes(argue, byteorder='big', signed=False)
                if not self.data_path.ALU.flag_z:
                    self.signal_latch_program_counter(True, False, value)
                else:
                    self.signal_latch_program_counter(False, True)
                self.step = 0
                self.tick()
                return
        if opcode is Opcode.ASTORE:
            if self.step == 0:
                self.data_path.signal_latch_addres_register(True)
                self.step += 1
                self.tick()
                return
            if self.step == 1:
                self.data_path.write_to_memory()
                self.step = 0
                self.signal_latch_program_counter(False, False)
                self.tick()
                return
        if opcode is Opcode.MUL:
            if self.step == 0:
                self.data_path.signal_set_left_ALU(True)
                self.data_path.signal_set_right_ALU(True)
                self.data_path.ALU.mul()
                self.step += 1
                self.tick()
                return
            if self.step == 1:
                self.data_path.stack_push(False, True, False)
                self.step = 0
                self.signal_latch_program_counter(False, False)
                self.tick()
                return

        if opcode is Opcode.DIV:
            if self.step == 0:
                self.data_path.signal_set_left_ALU(True)
                self.data_path.signal_set_right_ALU(True)
                self.data_path.ALU.div()
                self.step += 1
                self.tick()
                return
            if self.step == 1:
                self.data_path.stack_push(False, True, False)
                self.step = 0
                self.signal_latch_program_counter(False, False)
                self.tick()
                return

        if opcode is Opcode.MOD:
            if self.step == 0:
                self.data_path.signal_set_left_ALU(True)
                self.data_path.signal_set_right_ALU(True)
                self.data_path.ALU.mod()
                self.step += 1
                self.tick()
                return
            if self.step == 1:
                self.data_path.stack_push(False, True, False)
                self.step = 0
                self.signal_latch_program_counter(False, False)
                self.tick()
                return

    def debug_print_interrupt(self, action):
        if self._tick > self.log_limit:
            return
        flags_str = f"{int(self.data_path.ALU.flag_n)}{int(self.data_path.ALU.flag_z)}"
        ei_bit = 1 if self.IE else 0
        intr_bit = 1 if self.pending_interrupt else 0
        in_intr_bit = 1 if self.in_interrupt else 0

        data_stack_snapshot = self.data_path.stack[:self.data_path.stack_pointer]
        return_stack_snapshot = self.data_path.return_stack[:self.data_path.return_stack_pointer]
        output_snapshot = list(self.data_path.output_buffer)

        print(
            f"TICK: {self.current_tick():04d} | "
            f"PC: {self.program_counter:04d} | "
            f"STEP: {self.int_step} | "
            f"IR: ---- ({action}) | "
            f"NZ: {flags_str} | "
            f"EI: {ei_bit} | "
            f"IS INTR: {intr_bit} | "
            f"IN INTR: {in_intr_bit} | "
            f"DS: {data_stack_snapshot} | "
            f"RS: {return_stack_snapshot} | "
            f"OUT: {output_snapshot}"
        )

    def debug_print(self, instruction, arg):
        if self._tick > self.log_limit:
            return
        flags_str = f"{int(self.data_path.ALU.flag_n)}{int(self.data_path.ALU.flag_z)}"


        ei_bit = 1 if self.IE else 0
        intr_bit = 1 if self.pending_interrupt else 0
        in_intr_bit = 1 if self.in_interrupt else 0


        int_arg = int.from_bytes(arg, byteorder='big', signed=True)

        if instruction in [Opcode.LIT, Opcode.LOAD, Opcode.STORE, Opcode.JMP, Opcode.IF, Opcode.MIF, Opcode.CALL]:
            ir_mnemonic = f"{instruction.value} {int_arg}"
        else:
            ir_mnemonic = f"{instruction.value}"


        ir_hex = f"0x{opcode_to_binary.get(instruction, 0):02x}"

        data_stack_snapshot = self.data_path.stack[:self.data_path.stack_pointer]
        return_stack_snapshot = self.data_path.return_stack[:self.data_path.return_stack_pointer]
        output_snapshot = list(self.data_path.output_buffer)


        print(
            f"TICK: {self.current_tick():04d} | "
            f"PC: {self.program_counter:04d} | "
            f"STEP: {self.step} | "
            f"IR: {ir_hex} ({ir_mnemonic}) | "
            f"NZ: {flags_str} | "
            f"EI: {ei_bit} | "
            f"IS INTR: {intr_bit} | "
            f"IN INTR: {in_intr_bit} | "
            f"DS: {data_stack_snapshot} | "
            f"RS: {return_stack_snapshot} | "
            f"OUT: {output_snapshot}"
        )


def run_cpu(code_file, input_file, config_file):

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    data_mem_size = config["data_memory_size"]
    cmd_mem_size = config["command_memory_size"]
    in_port = config["input_port"]
    out_port = config["output_port"]
    entry_point = config["entry_point"]
    data_image = config.get("data_image", {})

    with open(code_file, "rb") as f:
        binary_code = f.read()

    input_text = ""
    input_schedule = []
    if input_file:
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                input_text = f.read()
        except FileNotFoundError:
            pass

        try:
            with open(input_file, "r", encoding="utf-8") as f:
                for line in f:
                    line_cleared = line.rstrip("\r\n")
                    if line_cleared.strip():
                        parts = line_cleared.split(maxsplit=1)
                        if len(parts) == 2:
                            tick_str, char_val = parts
                            input_schedule.append((int(tick_str), char_val))
                        elif len(parts) == 1 and line_cleared[-1] == " ":

                            input_schedule.append((int(parts[0]), " "))
        except FileNotFoundError:
            pass

    input_schedule.sort(key=lambda x: x[0])

    alu = ALU()
    dp = DataPath(data_mem_size, alu, in_port, out_port, input_text)
    cu = ControlUnit(cmd_mem_size, dp, entry_point=entry_point,  input_schedule=input_schedule)

    for addr_str, val in data_image.items():
        dp.data_memory[int(addr_str)] = val

    for i in range(len(binary_code)):
        cu.command_memory[i] = binary_code[i]

    print("=== Запуск симуляции ===")
    try:
        limit = 50000000
        while cu.current_tick() < limit:
            cu.process_next_tick()
        print("Ошибка: Превышен лимит тактов (Infinite loop?).")
    except StopIteration:
        print("=== Симуляция завершена (HALT) ===")
    except EOFError as e:
        print(f"Ошибка ввода/вывода: {e}")

    print("\n--- Буфер вывода ---")

    output_str = ""
    for val in dp.output_buffer:
        if val > 255:
            output_str += str(val) + " "
        elif 32 <= val <= 126 or val == 10:
            output_str += chr(val)
        else:
            output_str += f"\\x{val:02x}"

    print(output_str)

    print(f"\nЗатрачено тактов: {cu.current_tick()}")
    print("--- Дамп первых 50 ячеек Data Memory ---")
    print(dp.data_memory[:50])



def main():

    if len(sys.argv) == 4:
        code_file = sys.argv[1]
        input_file = sys.argv[2]
        config_file = sys.argv[3]
        run_cpu(code_file, input_file, config_file)
    elif len(sys.argv) == 3:
        code_file = sys.argv[1]
        config_file = sys.argv[2]
        run_cpu(code_file, None, config_file)
    else:

        code_file = "input.bin"
        input_file = "shedule.txt"
        config_file = "input_config.json"
        run_cpu(code_file, input_file, config_file)



if __name__ == "__main__":
    main()
