from itertools import permutations


class IO:
    def __init__(self, state=False):
        self.state = state

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state


class Gate:
    gates = []

    def __init__(self, inputs_list, force_state=False, state=False):
        self.inputs_list = inputs_list
        self.force_state = force_state
        self.state = state
        Gate.gates.append(self)

    def add_input(self, input):
        self.inputs_list.append(input)

    def remove_input(self, input):
        self.inputs_list.remove(input)

    def get_state(self) -> bool:
        pass


class OR(Gate):
    def get_state(self):
        if self.force_state == True:
            return self.state
        return any(i.get_state() for i in self.inputs_list)


class AND(Gate):
    def get_state(self):
        if self.force_state == True:
            return self.state
        return all(i.get_state() for i in self.inputs_list)

class NOT(Gate):
    def get_state(self):
        return not self.inputs_list.get_state()


class XOR(Gate):
    def get_state(self):
        if self.force_state == True:
            return self.state

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
        if self.force_state == True:
            return self.state
        return self.out.get_state(), self.s.get_state()


class RCA:
    def __init__(self, io_list_a, io_list_b):
        self.io_list_a = io_list_a
        self.io_list_b = io_list_b
        self.sumators = []
        last_io = IO()
        for a, b in zip(self.io_list_a, self.io_list_b):
            self.sumators.append(FullSumator(a, b, last_io))
            last_io = self.sumators[-1].s

    def get_state(self):
        return [sumator.get_state()[0] for sumator in self.sumators]

class Mod3Generator:
    def __init__(self, io_list):
        level_one_2 = FullSumator(io_list[-3], NOT(io_list[-2]), io_list[-1])
        level_one_1 = FullSumator(NOT(io_list[-6]), io_list[-5], NOT(io_list[-4]))

        level_two_2 = FullSumator(level_one_1.out, NOT(level_one_2.s), level_one_2.out)
        level_two_1 = FullSumator(NOT(io_list[-8]), io_list[-7], NOT(level_one_1.s))

        level_three = FullSumator(level_two_1.out, NOT(level_two_2.s), level_two_2.out)

        level_four = FullSumator(NOT(level_two_1.s), NOT(level_three.s), level_three.out)
        self.s = level_four.out
        self.out = level_four.s

    def get_state(self):
        return [self.out.get_state(), self.s.get_state()]


if __name__ == "__main__":
    a = [IO() for i in range(8)]
    num = "01111110"
    for i, b in enumerate(num):
        a[i].set_state(int(b))

    gen = Mod3Generator(a)
    print(gen.get_state())
    
