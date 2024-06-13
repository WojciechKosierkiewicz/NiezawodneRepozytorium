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

class HalfSumator:
    def __init__(self, a, b, force_state=False, state=(False, False)):
        self.a = a
        self.b = b
        self.s = XOR([self.a, self.b])
        self.out = AND([self.a, self.b])

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



# class Mod5Bit3Generator:
#     def __init__(self, io_list):
#         # Ensure we have 5 bits
#         assert len(io_list) == 5, "Input must be a 5-bit number"
# 
#         # Reverse the list to start from LSB
#         io_list = io_list[::-1]
# 
#         # Level One: Handle bits 0, 1, 2
#         level_one = FullSumator(io_list[0], NOT(io_list[1]), io_list[2])
# 
#         # Level Two: Combine level_one with bits 3 and 4
#         level_two = FullSumator(NOT(io_list[3]), io_list[4], NOT(level_one.s))
# 
#         # Level Three: Final combination
#         level_three = FullSumator(level_one.out, NOT(level_two.s), level_two.out)
# 
#         self.s = level_three.s
#         self.out = level_three.out
# 
#     def get_state(self):
#         return [self.s.get_state(), self.out.get_state()]

class Mod5Bit3Generator:
    def __init__(self, io_list):
        assert len(io_list) == 5, "Input must be a 5-bit number"

        # Level One: Handle bits 0, 1, 2
        fa1 = FullSumator(io_list[-3], NOT(io_list[-2]), io_list[-1])

        # Level Two: Combine fa1 output with bits 3 and 4
        ha = HalfSumator(io_list[-5], NOT(io_list[-4]))

        # Level Three: Combine outputs from fa1 and fa2
        fa2 = FullSumator(ha.s, NOT(fa1.out), fa1.s)

        fa3 = FullSumator(ha.out, NOT(fa2.out), fa2.s)

        # Final output
        self.s = fa3.s
        self.out = fa3.out

    def get_state(self):
        return [self.out.get_state(), self.s.get_state()]

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


def get_4bit_io_from_num(a):
    a_bin = bin(a)[2:].rjust(4, "0")
    return [IO(state=int(bit)) for bit in a_bin]

class CLA5Bit:
    def __init__(self, io_list_a, io_list_b):
        self.io_list_a = io_list_a[::-1]  # Reverse to start from LSB
        self.io_list_b = io_list_b[::-1]  # Reverse to start from LSB
        self.cin = IO(state=False)  # Initial carry-in is 0
        self.generate_propagate()
        self.calculate_carries()
        self.calculate_sum()

    def generate_propagate(self):
        # Calculate generate (G) and propagate (P) for each bit
        self.G = [AND([a, b]) for a, b in zip(self.io_list_a, self.io_list_b)]
        self.P = [XOR([a, b]) for a, b in zip(self.io_list_a, self.io_list_b)]

    def calculate_carries(self):
        # Calculate carries using carry lookahead logic
        self.C = [self.cin]  # C[0] is the initial carry-in
        for i in range(4):
            term1 = self.G[i]
            term2 = AND([self.P[i], self.C[i]])
            self.C.append(OR([term1, term2]))

    def calculate_sum(self):
        # Calculate sum bits
        self.S = [XOR([p, c]) for p, c in zip(self.P, self.C)]

    def get_state(self):
        # Return the sum bits and the final carry-out
        return  [self.C[-1].get_state()] + [s.get_state() for s in self.S[::-1]]

class TestResult:
    def __init__(self):
        self.inputs = []
        self.outputs = []
        self.broken_gate = None
        self.failed = False

class TestResults:
    def __init__(self):
        self.results = []

    def add_result(self, result: TestResult):
        self.results.append(result)

    def print_results(self):
        for i, result in enumerate(self.results):
            if result.failed:
                if result.broken_gate is not None:
                    print(f"Test {i+1}")
                    print(f"Inputs: {result.inputs}")
                    print(f"Outputs: {result.outputs}")
                    if result.failed:
                        print(f"Failed at gate {result.broken_gate}")
                    print()
        for i, result in enumerate(self.results):
            if result.failed:
                if result.broken_gate is None:
                    print(f"Test {i+1}")
                    print(f"Inputs: {result.inputs}")
                    print(f"Outputs: {result.outputs}")
                    if result.failed:
                        print(f"Failed at gate {result.broken_gate}")
                    print()
        for i, result in enumerate(self.results):
            if not result.failed:
                if result.broken_gate is not None:
                    print(f"Test {i+1}")
                    print(f"Inputs: {result.inputs}")
                    print(f"Outputs: {result.outputs}")
                    if result.failed:
                        print(f"Failed at gate {result.broken_gate}")
                    print()
        for i, result in enumerate(self.results):
            if not result.failed:
                if result.broken_gate is None:
                    print(f"Test {i+1}")
                    print(f"Inputs: {result.inputs}")
                    print(f"Outputs: {result.outputs}")
                    if result.failed:
                        print(f"Failed at gate {result.broken_gate}")
                    print()


if __name__ == "__main__":
    a = randint(0, 2**4-1)
    b = randint(0, 2**4-1)
    a_io = get_4bit_io_from_num(a)
    rest_gen_a = Mod5Bit3Generator([IO(0)] + a_io)
    b_io = get_4bit_io_from_num(b)
    rest_gen_b = Mod5Bit3Generator([IO(0)] + b_io)
    print(a, rest_gen_a.get_state())
    print(b, rest_gen_b.get_state())

    mod3_sum = Mod3Sumator([rest_gen_a.s, rest_gen_a.out], [rest_gen_b.s, rest_gen_b.out])
    
    sumator = CLA5Bit(a_io, b_io)

    rest_gen_sum = Mod5Bit3Generator([sumator.C[-1]] + [s for s in sumator.S[::-1]])
    comparator = CompMod3([rest_gen_sum.s, rest_gen_sum.out], [mod3_sum.s, mod3_sum.out])
    res = int(''.join([str(int(a)) for a in sumator.get_state()]), 2)
    s = a + b
    print(res != s, comparator.get_state())
    print(res, s)

