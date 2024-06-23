from itertools import permutations
from random import randint


class Gate:
    gates = []

    def __init__(self, inputs_list, parent=None, force_state=None, state=False):
        self.idx = len(Gate.gates)
        self.parent = parent
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

    def __repr__(self):
        return f"IO idx: {self.idx}"

class OR(Gate):
    def _get_state(self):
        return any(i.get_state() for i in self.inputs_list)

    def __repr__(self):
        return f"OR idx: {self.idx}"


class AND(Gate):
    def _get_state(self):
        return all(i.get_state() for i in self.inputs_list)

    def __repr__(self):
        return f"AND idx: {self.idx}"

class NOT(Gate):
    def _get_state(self):
        return not self.inputs_list.get_state()

    def __repr__(self):
        return f"NOT idx: {self.idx}"


class XOR(Gate):
    def _get_state(self):

        if sum(i.get_state() for i in self.inputs_list) % 2 == 0:
            return False
        return True

    def __repr__(self):
        return f"XOR idx: {self.idx}"


class FullSumator:
    def __init__(self, a, b, cin, parent=None, force_state=False, state=(False, False)):
        self.parent = parent
        self.a = a
        self.b = b
        self.cin = cin
        self.force_state = force_state
        self.state = state
        xor1 = XOR([self.a, self.b], parent=self)
        xor2 = XOR([xor1, self.cin], parent=self)
        and1 = AND([self.a, self.b], parent=self)
        and2 = AND([xor1, self.cin], parent=self)
        or1 = OR([and1, and2], parent=self)
        self.s = or1
        self.out = xor2

    def get_state(self):
        return self.out.get_state(), self.s.get_state()

    def __repr__(self):
        return f"FullSumator"

class HalfSumator:
    def __init__(self, a, b, parent=None, force_state=False, state=(False, False)):
        self.parent = parent
        self.a = a
        self.b = b
        self.s = XOR([self.a, self.b], parent=self)
        self.out = AND([self.a, self.b], parent=self)

    def get_state(self):
        return self.out.get_state(), self.s.get_state()

    def __repr__(self):
        return f"HalfSumator"


class RCA:
    def __init__(self, io_list_a, io_list_b, parent=None):
        self.parent = parent
        self.io_list_a = io_list_a[::-1]
        self.io_list_b = io_list_b[::-1]
        self.sumators = []
        last_io = IO(parent=self)
        for a, b in zip(self.io_list_a, self.io_list_b):
            self.sumators.append(FullSumator(a, b, last_io, parent=self))
            last_io = self.sumators[-1].s

    def get_state(self):
        return [sumator.get_state()[0] for sumator in self.sumators[::-1]]

    def __repr__(self):
        return f"RCA"

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

    def __repr__(self):
        return f"Mod8Bit3Generator"


class Mod5Bit3Generator:
    def __init__(self, io_list, parent=None):
        assert len(io_list) == 5, "Input must be a 5-bit number"
        self.parent = parent

        # Level One: Handle bits 0, 1, 2
        fa1 = FullSumator(io_list[-3], NOT(io_list[-2], parent=self), io_list[-1], parent=self)

        # Level Two: Combine fa1 output with bits 3 and 4
        fa2 = FullSumator(NOT(io_list[-4], parent=self), NOT(fa1.s, parent=self),  fa1.out, parent=self)

        # Level Three: Combine outputs from fa1 and fa2
        fa3 = FullSumator(io_list[-5], NOT(fa2.s, parent=self), fa2.out, parent=self)


        # Final output
        self.s = NOT(XOR([fa3.s, fa3.out], parent=self), parent=self)
        self.out = AND([fa3.s, NOT(fa3.out, parent=self)], parent=self)

    def get_state(self):
        return [self.s.get_state(), self.out.get_state()]
    
    def __repr__(self):
        return f"Mod5Bit3Generator"


class CompMod3:
    def __init__(self, io_list_a, io_list_b, parent=None):
        self.parent = parent
        x_0 = io_list_a[-2]
        x_1 = io_list_a[-1]
        y_0 = io_list_b[-2]
        y_1 = io_list_b[-1]
        w_1 = XOR([AND([NOT(y_1, parent=self), y_0], parent=self), AND([NOT(x_1, parent=self), x_0], parent=self)], parent=self)
        w_2 = XOR([AND([y_1, NOT(y_0, parent=self)], parent=self), AND([x_1, NOT(x_0, parent=self)], parent=self)], parent=self)
        self.result = OR([w_1, w_2], parent=self)


    def get_state(self):
        return self.result.get_state()

    def __repr__(self):
        return f"CompMod3"

class Mod3Sumator:
    def __init__(self, io_list_a, io_list_b, parent=None):
        self.parent = parent
        static_io = IO(0, parent=self)
        xor_2 = XOR([static_io, io_list_a[-1]], parent=self)
        xor_1 = XOR([static_io, io_list_a[-2]], parent=self)
        fa_1 = FullSumator(xor_2, NOT(io_list_b[-2], parent=self), io_list_b[-1], parent=self)
        fa_2 = FullSumator(NOT(xor_1, parent=self), NOT(fa_1.s, parent=self), fa_1.out, parent=self)
        self.s = fa_2.s
        self.out = fa_2.out

    def get_state(self):
        return [self.s.get_state(), self.out.get_state()]

    def __repr__(self):
        return f"Mod3Sumator"

def get_16bit_io_from_num(a):
    a_bin = bin(a)[2:].rjust(16, "0")
    return [IO(state=int(bit)) for bit in a_bin]


def get_4bit_io_from_num(a):
    a_bin = bin(a)[2:].rjust(4, "0")
    return [IO(state=int(bit)) for bit in a_bin]

class DotOperator:
    def __init__(self, G1, P1, G2, P2, parent=None):
        self.parent = parent
        self.G = OR([G1, AND([P1, G2], parent=self)], parent=self)
        self.P = AND([P1, P2], parent=self)

    def get_state(self):
        return self.G.get_state(), self.P.get_state()

    def __repr__(self):
        return "Dot"

class CLA5Bit:
    def __init__(self, io_list_a, io_list_b, parent=None):
        self.parent = parent
        self.io_list_a = io_list_a[::-1]  # Reverse to start from LSB
        self.io_list_b = io_list_b[::-1]  # Reverse to start from LSB
        self.cin = IO(state=False, parent=self)  # Initial carry-in is 0
        self.generate_propagate()
        self.calculate_carries()
        self.calculate_sum()

    def generate_propagate(self):
        # Calculate initial generate (G) and propagate (P) for each bit
        self.G = [AND([a, b], parent=self) for a, b in zip(self.io_list_a, self.io_list_b)]
        self.P = [XOR([a, b], parent=self) for a, b in zip(self.io_list_a, self.io_list_b)]

    def calculate_carries(self):
        # First level of prefix computation
        dot_1_0 = DotOperator(self.G[1], self.P[1], self.G[0], self.P[0], parent=self)
        dot_3_2 = DotOperator(self.G[3], self.P[3], self.G[2], self.P[2], parent=self)

        # Second level of prefix computation
        dot_3_0 = DotOperator(dot_3_2.G, dot_3_2.P, dot_1_0.G, dot_1_0.P, parent=self)

        # Compute carries
        self.C = [self.cin]
        self.C.append(OR([self.G[0], AND([self.P[0], self.cin], parent=self)], parent=self))
        self.C.append(OR([dot_1_0.G, AND([dot_1_0.P, self.cin], parent=self)], parent=self))
        self.C.append(OR([self.G[2], AND([self.P[2], self.C[2]], parent=self)], parent=self))
        self.C.append(OR([dot_3_2.G, AND([dot_3_2.P, self.C[2]], parent=self)], parent=self))
        self.C.append(OR([dot_3_0.G, AND([dot_3_0.P, self.cin], parent=self)], parent=self))

    def calculate_sum(self):
        # Calculate sum bits
        self.S = [XOR([p, c], parent=self) for p, c in zip(self.P, self.C[:-1])]

    def get_state(self):
        # Return the sum bits and the final carry-out
        return [self.C[-1].get_state()] + [s.get_state() for s in self.S[::-1]]

    def __repr__(self):
        return f"CLA5Bit_Sklansky"

def check_gate(gate, sumator, a, b, state):
    gate.force_state = state
    res = int(''.join([str(int(a)) for a in sumator.get_state()]), 2)
    s = a + b
    parent = gate
    row = [a, b, state, s, res]
    path = []
    while True:
        path.append(str(parent))
        if parent.parent is None:
            break
        parent = parent.parent
    row +=[ " -> ".join(path)]
    correct = (res == s)
    detected = comparator.get_state()
    row += [correct, detected]
    print("|".join(map(str, row)))
    gate.force_state = None
    return detected, correct

if __name__ == "__main__":
    total_tests = 0
    total_correct = 0
    total_detected = 0
    print("A|B|wymuszony stan|Oczekiwany wynik|Otrzymany wynik|bramka|Czy poprawny wynik|Czy wykryty")
    for a in range(0, 2**4):
        for b in range(0, 2**4):
            a_io = get_4bit_io_from_num(a)
            rest_gen_a = Mod5Bit3Generator([IO(0)] + a_io)
            b_io = get_4bit_io_from_num(b)
            rest_gen_b = Mod5Bit3Generator([IO(0)] + b_io)

            mod3_sum = Mod3Sumator([rest_gen_a.s, rest_gen_a.out], [rest_gen_b.s, rest_gen_b.out])
            
            sumator = CLA5Bit(a_io, b_io)

            rest_gen_sum = Mod5Bit3Generator([sumator.C[-1]] + [s for s in sumator.S[::-1]])
            comparator = CompMod3([rest_gen_sum.s, rest_gen_sum.out], [mod3_sum.s, mod3_sum.out])

            for gate in Gate.gates:
                d, c = check_gate(gate, sumator, a, b, True)
                total_correct += c
                total_detected += d
                d, c = check_gate(gate, sumator, a, b, False)
                total_correct += c
                total_detected += d
                total_tests += 2
            Gate.gates.clear()

