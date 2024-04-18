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
    def __init__(self,io_list_a,io_list_b):
        self.io_list_a = io_list_a
        self.io_list_b = io_list_b
        self.sumators = [FullSumator(a, b, IO()) for a, b in zip(self.io_list_a, self.io_list_b)]
        for i in range(1, len(self.sumators)):
            self.sumators[i].cin = self.sumators[i-1].s


    def get_state(self):
        return [sumator.get_state()[0] for sumator in self.sumators]

if __name__ == '__main__':
    a = [IO() for i in range(4)]
    b = [IO() for i in range(4)]
    rca = RCA(a,b)
    for i in range(4):
        a[i].set_state(False)
        b[i].set_state(True)
    print(rca.get_state())
    print(Gate.gates)

    for perm in permutations(Gate.gates, 4):



        for gate in perm:




            gate.force_state = True






            print(rca.get_state())




            gate.force_state = False


