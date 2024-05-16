from itertools import permutations
from random import randint




class Gate:
    gates = []

    def __init__(self, inputs_list, force_state=None, state=False):
        self.inputs_list = inputs_list
        self.force_state = force_state
        self.state = state
        Gate.gates.append(self)

    def add_input(self, input):
        self.inputs_list.append(input)

    def remove_input(self, input):
        self.inputs_list.remove(input)
    
    def _get_state(self) -> bool:
        pass

    def get_state(self) -> bool:
        if self.force_state is not None:
            return self.force_state
        return self._get_state()

class IO(Gate):
    def __init__(self, state=False, *k, **kw):
        super().__init__(inputs_list=[], *k, **kw)
        self.state = state

    def _get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state

class OR(Gate):
    def _get_state(self):
        return any(i.get_state() for i in self.inputs_list)


class AND(Gate):
    def _get_state(self):
        return all(i.get_state() for i in self.inputs_list)

class NOT(Gate):
    def _get_state(self):
        return not self.inputs_list.get_state()


class XOR(Gate):
    def _get_state(self):

        if sum(i.get_state() for i in self.inputs_list) % 2 == 0:
            return False
        return True


class FullSumator:
    def __init__(self, a, b, cin, force_state=False, state=(False, False)):
        self.a = a
        self.b = b
        self.cin = cin
        self.force_state = force_state
        self.state = state
        xor1 = XOR([self.a, self.b])
        xor2 = XOR([xor1, self.cin])
        and1 = AND([self.a, self.b])
        and2 = AND([xor1, self.cin])
        or1 = OR([and1, and2])
        self.s = or1
        self.out = xor2

    def get_state(self):
        return self.out.get_state(), self.s.get_state()


class RCA:
    def __init__(self, io_list_a, io_list_b):
        self.io_list_a = io_list_a[::-1]
        self.io_list_b = io_list_b[::-1]
        self.sumators = []
        last_io = IO()
        for a, b in zip(self.io_list_a, self.io_list_b):
            self.sumators.append(FullSumator(a, b, last_io))
            last_io = self.sumators[-1].s

    def get_state(self):
        return [sumator.get_state()[0] for sumator in self.sumators[::-1]]

class Mod8Bit3Generator:
    def __init__(self, io_list):
        level_one_2 = FullSumator(io_list[-3], NOT(io_list[-2]), io_list[-1])
        level_one_1 = FullSumator(NOT(io_list[-6]), io_list[-5], NOT(io_list[-4]))

        level_two_2 = FullSumator(level_one_1.out, NOT(level_one_2.s), level_one_2.out)
        level_two_1 = FullSumator(NOT(io_list[-8]), io_list[-7], NOT(level_one_1.s))

        level_three = FullSumator(level_two_1.out, NOT(level_two_2.s), level_two_2.out)

        level_four = FullSumator(NOT(level_two_1.s), NOT(level_three.s), level_three.out)
        self.s = level_four.s
        self.out = level_four.out

    def get_state(self):
        return [self.s.get_state(), self.out.get_state()]

class Mod16Bit3Generator:
    def __init__(self, io_list):
        gen_2 = Mod8Bit3Generator(io_list[8:])
        gen_1 = Mod8Bit3Generator(io_list[:8])
        level_one = FullSumator(gen_1.out, NOT(gen_2.s), gen_2.out)
        level_two = FullSumator(NOT(gen_1.s), NOT(level_one.s), level_one.out)
        self.out = level_two.out
        self.s = level_two.s

    def get_state(self):
        return [self.s.get_state(), self.out.get_state()]

class CompMod3:
    def __init__(self, io_list_a, io_list_b):
        x_0 = io_list_a[-2]
        x_1 = io_list_a[-1]
        y_0 = io_list_b[-2]
        y_1 = io_list_b[-1]
        w_1 = XOR([AND([NOT(y_1), y_0]), AND([NOT(x_1), x_0])])
        w_2 = XOR([AND([y_1, NOT(y_0)]), AND([x_1, NOT(x_0)])])
        self.result = OR([w_1, w_2])


    def get_state(self):
        return self.result.get_state()

class Mod3Sumator:
    def __init__(self, io_list_a, io_list_b):
        static_io = IO(0)
        xor_2 = XOR([static_io, io_list_a[-1]])
        xor_1 = XOR([static_io, io_list_a[-2]])
        fa_1 = FullSumator(xor_2, NOT(io_list_b[-2]), io_list_b[-1])
        fa_2 = FullSumator(NOT(xor_1), NOT(fa_1.s), fa_1.out)
        self.s = fa_2.s
        self.out = fa_2.out

    def get_state(self):
        return [self.s.get_state(), self.out.get_state()]

def get_16bit_io_from_num(a):
    a_bin = bin(a)[2:].rjust(16, "0")
    return [IO(state=int(bit)) for bit in a_bin]

if __name__ == "__main__":
    for i in range(1000):
        a = randint(0, 66535)
        b = randint(0, 66535)
        a_io = get_16bit_io_from_num(a)
        rest_gen_a = Mod16Bit3Generator(a_io)
        b_io = get_16bit_io_from_num(b)
        rest_gen_b = Mod16Bit3Generator(b_io)

        mod3_sum = Mod3Sumator([rest_gen_a.s, rest_gen_a.out], [rest_gen_b.s, rest_gen_b.out])
        
        sumator = RCA(a_io, b_io)
        gate_idx = randint(0, len(Gate.gates))
        Gate.gates[gate_idx].force_state = randint(0, 1)

        rest_gen_sum = Mod16Bit3Generator([s.out for s in sumator.sumators[::-1]])
        comparator = CompMod3([rest_gen_sum.s, rest_gen_sum.out], [mod3_sum.s, mod3_sum.out])
        res = int(''.join([str(int(a)) for a in sumator.get_state()]), 2)
        s = a + b
        print(res != s, comparator.get_state())

        
