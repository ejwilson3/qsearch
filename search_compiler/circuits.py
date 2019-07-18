import numpy as np

from . import utils, graphics

class QuantumStep:
    def __init__(self):
        raise NotImplementedError("Subclasses of QuantumStep should declare their own initializers.")
        # NOTE: QuantumStep initializers must set self.num_inputs, self.dits
    
    def matrix(self, v):
        raise NotImplementedError("Subclasses of QuantumStep are required to implement the matrix(v) method.")

    def path(self, v):
        raise NotImplementedError("Subclasses of QuantumStep are required to implement the path(v) method.")

    def assemble(self, v, i=0):
        raise NotImplementedError("Subclasses of QuantumStep are required to implement the assemble(v, i) method.")

    def draw(self):
        gates = self._draw_assemble()
        labels = ["q{}".format(i) for i in range(0, self.dits)]
        return graphics.plot_quantum_circuit(gates, labels=labels, plot_labels=False)

    def _draw_assemble(self, i=0):
        return []

    def copy(self):
        return self

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def __repr__(self):
        return "QuantumStep()"


class IdentityStep(QuantumStep):
    def __init__(self, n=2, dits=1):
        self.num_inputs=0
        self._I = np.matrix(np.eye(n), dtype='complex128')
        self.dits = dits
        self._n = n

    def matrix(self, v):
        return self._I

    def assemble(self, v, i=0):
        return []

    def __repr__(self):
        return "IdentityStep({})".format(self._n)
    


class ZXZXZQubitStep(QuantumStep):
    def __init__(self):
        self.num_inputs = 3
        self.dits = 1

        self._x90 = utils.rot_x(np.pi/2)
        self._rot_z = utils.rot_z(0)
        self._out = np.matrix(np.eye(2), dtype='complex128')
        self._buffer = np.matrix(np.eye(2), dtype = 'complex128')
        # need two buffers due to a bug in some implementations of numpy
        
    def matrix(self, v):
        utils.re_rot_z(v[0]*np.pi*2, self._rot_z)
        self._out = np.dot(self._rot_z, self._x90, out=self._out)
        utils.re_rot_z(v[1]*np.pi*2 + np.pi, self._rot_z)
        self._buffer = np.dot(self._out, self._rot_z, out=self._buffer)
        self._out = np.dot(self._buffer, self._x90, out=self._out)
        utils.re_rot_z(v[2]*np.pi*2-np.pi, self._rot_z)
        return np.dot(self._out, self._rot_z)

    def assemble(self, v, i=0):
        # later use IBM's parameterization and convert to ZXZXZ in post processing
        out = []
        out.append(("gate", "Z", (v[0]*np.pi*2,), (i,)))
        out.append(("gate", "X", (np.pi/2,), (i,)))
        out.append(("gate", "Z", (v[1]*np.pi*2 + np.pi,), (i,)))
        out.append(("gate", "X", (np.pi/2,), (i,)))
        out.append(("gate", "Z", (v[2]*np.pi*2 + np.pi,), (i,)))
        return [("block", out)]

    def _draw_assemble(self, i=0):
        return [("U", "q{}".format(i))] 
    
    def __repr__(self):
        return "ZXZXZQubitStep()"

class XZXZPartialQubitStep(QuantumStep):
    def __init__(self):
        self.num_inputs = 2
        self.dits = 1

        self._x90 = utils.rot_x(np.pi/2)
        self._rot_z = utils.rot_z(0)
        self._out = np.matrix(np.eye(2), dtype='complex128')
        self._buffer = np.matrix(np.eye(2), dtype = 'complex128')
        # need two buffers due to a bug in some implementations of numpy
        
    def matrix(self, v):
        utils.re_rot_z(v[0]*np.pi*2 + np.pi, self._rot_z)
        self._buffer = np.dot(self._x90, self._rot_z, out=self._buffer)
        self._out = np.dot(self._buffer, self._x90, out=self._out)
        utils.re_rot_z(v[1]*np.pi*2-np.pi, self._rot_z)
        return np.dot(self._out, self._rot_z)

    def assemble(self, v, i=0):
        # later use IBM's parameterization and convert to ZXZXZ in post processing
        out = []
        out.append(("gate", "X", (np.pi/2,), (i,)))
        out.append(("gate", "Z", (v[0]*np.pi*2 + np.pi,), (i,)))
        out.append(("gate", "X", (np.pi/2,), (i,)))
        out.append(("gate", "Z", (v[1]*np.pi*2 + np.pi,), (i,)))
        return [("block", out)]

    def _draw_assemble(self, i=0):
        return [("U", "q{}".format(i))] 
    
    def __repr__(self):
        return "ZXZXZQubitStep()"

class QiskitU3QubitStep(QuantumStep):
    def __init__(self):
        self.num_inputs = 3
        self.dits = 1

    def matrix(self, v):
        ct = np.cos(v[0] * np.pi)
        st = np.sin(v[0] * np.pi)
        cp = np.cos(v[1] * np.pi * 2)
        sp = np.sin(v[1] * np.pi * 2)
        cl = np.cos(v[2] * np.pi * 2)
        sl = np.sin(v[2] * np.pi * 2)
        return np.matrix([[ct, -st * (cl + 1j * sl)], [st * (cp + 1j * sp), ct * (cl * cp - sl * sp + 1j * cl * sp + 1j * sl * cp)]], dtype='complex128')

    def assemble(self, v, i=0):
        return [("gate", "qiskit-u3", (v[0]*np.pi*2, v[1]*np.pi*2, v[2]*np.pi*2), (i,))]

    def _draw_assemble(self, i=0):
        return [("U", "q{}".format(i))]

    def __repr__(self):
        return "QiskitU3QubitStep()"

# NOTE: Consider this code DEPRECATED and expect it to be deleted before a real release.  Use QiskitU3QubitStep or ZXZXZQubitStep instead.
class SingleQubitStep(ZXZXZQubitStep):
    def __repr__(self):
        return "SingleQubitStep()"


class SingleQutritStep(QuantumStep):
    def __init__(self):
        self.num_inputs = 8
        self.dits = 1

    def matrix(self, v):
        return utils.qt_arb_rot(*v)

    def assemble(self, v, i=0):
        return [("qutrit", tuple(v), (i,))]
    
    def __repr__(self):
        return "SingleQutritStep()"

class UStep(QuantumStep):
    def __init__(self, U, name=None, dits=1):
        self.name = name
        self.num_inputs = 0
        self._U = U
        self.dits = dits

    def matrix(self, v):
        return self._U

    def assemble(self, v, i=0):
        if self.name is None:
            return [("gate", "UNKNOWN", (), (i,))]
        else:
            return [("gate", self.name, (), (i,))]

    def __repr__(self):
        if self.name is None:
            return "UStep({})".format(repr(self._U))
        elif self.dits == 1:
            return "UStep({}, name={})".format(repr(self._U), repr(self.name))
        else:
            return "UStep({}, name={}, dits={})".format(repr(self._U), repr(self.name), repr(self.dits))

# TODO needs a rewrite or to be deprecated
class CUStep(QuantumStep):
    def __init__(self, U, name=None, flipped=False):
        self.name = name
        self.flipped = flipped
        self.num_inputs = 0
        self._U = U
        n = np.shape(U)[0]
        I = np.matrix(np.eye(n))
        top = np.pad(self._U if flipped else I, [(0,n),(0,n)], 'constant')
        bot = np.pad(I if flipped else self._U, [(n,0),(n,0)], 'constant')
        self._CU = np.matrix(top + bot)
        self.dits = 2

    def matrix(self, v):
        return self._CU

    def assemble(self, v, i=0):
        first = i+1 if self.flipped else i
        second = i if self.flipped else i+1
        if self.name is None:
            return "CONTROLLED-UNKNOWN q{} q{}".format(first, second)
        else:
            return "C{} q{} q{}".format(self.name, first, second)

    def __repr__(self):
        return "CUStep(" + str(repr(self._U)) + ("" if self.name is None else ", name={}".format(repr(self.name))) + ("flipped=True" if self.flipped else "") + ")"

# TODO needs updates or to be deprecated
class InvertStep(QuantumStep):
    def __init__(self, step):
        self._step = step
        self.num_inputs = step.num_inputs
        self.dits = step.dits

    def matrix(self, v):
        return self._step.matrix(v).H

    def assemble(self, v, i=0):
        return "REVERSE {\n" + self._step.assemble(v, i) + "\n}"

    def __repr__(self):
        return "InvertStep({})".format(repr(self._step))


class CSUMStep(QuantumStep):
    _csum =  np.matrix([[1,0,0, 0,0,0, 0,0,0],
                        [0,1,0, 0,0,0, 0,0,0],
                        [0,0,1, 0,0,0, 0,0,0],
                        [0,0,0, 0,0,1, 0,0,0],
                        [0,0,0, 1,0,0, 0,0,0],
                        [0,0,0, 0,1,0, 0,0,0],
                        [0,0,0, 0,0,0, 0,1,0],
                        [0,0,0, 0,0,0, 1,0,0],
                        [0,0,0, 0,0,0, 0,0,1]
                       ], dtype='complex128')
    
    def __init__(self):
        self.num_inputs = 0
        self.dits = 2

    def matrix(self, v):
        return CSUMStep._csum

    def assemble(self, v, i=0):
        return [("gate", "CSUM", (), (i, i+1))]

    def __repr__(self):
        return "CSUMStep()"

class CPIStep(QuantumStep):
    _cpi = np.matrix([[1,0,0, 0,0,0, 0,0,0],
                      [0,1,0, 0,0,0, 0,0,0],
                      [0,0,1, 0,0,0, 0,0,0],
                      [0,0,0, 0,1,0,0,0,0],
                      [0,0,0, 1,0,0, 0,0,0],
                      [0,0,0, 0,0,1, 0,0,0],
                      [0,0,0, 0,0,0, 1,0,0],
                      [0,0,0, 0,0,0, 0,1,0],
                      [0,0,0, 0,0,0, 0,0,1]
                     ], dtype='complex128')
    
    def __init__(self):
        self.num_inputs = 0
        self.dits = 2

    def matrix(self, v):
        return CPIStep._cpi

    def assemble(self, v, i=0):
        return [("gate", "CPI", (), (i, i+1))]

    def __repr__(self):
        return "CPIStep()"

class CPIPhaseStep(QuantumStep):
    def __init__(self):
        self.num_inputs = 0
        self._cpi = np.matrix([[1,0,0, 0,0,0, 0,0,0],
                               [0,1,0, 0,0,0, 0,0,0],
                               [0,0,1, 0,0,0, 0,0,0],
                               [0,0,0, 0,-1,0,0,0,0],
                               [0,0,0, 1,0,0, 0,0,0],
                               [0,0,0, 0,0,1, 0,0,0],
                               [0,0,0, 0,0,0, 1,0,0],
                               [0,0,0, 0,0,0, 0,1,0],
                               [0,0,0, 0,0,0, 0,0,1]
                              ], dtype='complex128')
        diag_mod = np.matrix(np.diag([1]*4 + [np.exp(2j * np.random.random()*np.pi) for _ in range(0,5)]))
        self._cpi = np.matmul(self._cpi, diag_mod)
        self.dits = 2

    def matrix(self, v):
        return self._cpi

    def assemble(self, v, i=0):
        return [("gate", "CPI-", (), (i, i+1))]

    def __repr__(self):
        return "CPIPhaseStep()"

class CNOTStep(QuantumStep):
    _cnot = np.matrix([[1,0,0,0],
                       [0,1,0,0],
                       [0,0,0,1],
                       [0,0,1,0]], dtype='complex128')
    def __init__(self):
        self.num_inputs = 0
        self.dits = 2

    def matrix(self, v):
        return CNOTStep._cnot

    def assemble(self, v, i=0):
        return [("gate", "CNOT", (), (i, i+1))]

    def _draw_assemble(self, i=0):
        return [("CNOT", "q{}".format(i+1), "q{}".format(i))]

    def __repr__(self):
        return "CNOTStep()"

class NonadjacentCNOTStep(QuantumStep):
    def __init__(self, n, control, target):
        self.dits = n
        self.num_inputs = 0
        self.control = control
        self.target = target
        self._U = gates.arbitrary_cnot(n, control, target)

    def matrix(self, v):
        return self._U

    def assemble(self, v, i=0):
        return [("gate", "CNOT", (), (control, target))]

    def _draw_assemble(self, i=0):
        return [("CNOT", "q{}".format(target), "q{}".format(control))]

    def __repr__(self):
        return "NonadjacentCNOTStep({}, {}, {})".format(self.dits, self.control, self.target)

class CRZStep(QuantumStep):
    _cnr = np.matrix([[1,0,0,0],
                       [0,1,0,0],
                       [0,0,0.5+0.5j,0.5-0.5j],
                       [0,0,0.5-0.5j,0.5+0.5j]])
    _I = np.matrix(np.eye(2))
    def __init__(self):
        self.num_inputs = 1
        self.dits = 2

    def matrix(self, v):
        U = np.dot(CRZStep._cnr, np.kron(CRZStep._I, utils.rot_z(v[0]))) # TODO fix this line
        return np.dot(U, CRZStep._cnr)

    def assemble(self, v, i=0):
        raise NotImplementedError("I haven't implemented CRZ assemble.  Probably just delete and rely on sqrtcnot and z as separate gates.")
        #return "CNOTROOT q{} q{}\nZ({}) q{}\nCNOTROOT q{} q{}".format(i, i+1, v[0], i+1, i, i+1)

    def _draw_assemble(Self, i=0):
        return [("CRZ", "q{}".format(i+1), "q{}".format(i))]

    def __repr__(self):
        return "CQubitStep()"


# TODO fix this code or deprecate it
class RemapStep(QuantumStep):

    def __init__(self, step, dits, source, target, name=None, d=2):
        self._step = step
        self._source = source
        self._target = target
        self.dits = dits
        self._d = d
        self._name = name
        self.num_inputs = step.num_inputs
        def g(a,b):
            def f(i,j):
                i_v = []
                j_v = []
                for k in range(0, dits):
                    i_v.append(i%d)
                    j_v.append(j%d)
                    i = i // d
                    j = j // d
                j_v[b], j_v[a] = j_v[a], j_v[b]
                eq = np.equal(i_v, j_v)
                return np.all(eq, axis=0)
            return f
        targetswap = target if source == 1 else 1
        swap_source = np.matrix(np.fromfunction(g(0,source), (d**dits,d**dits)), dtype='complex128')
        swap_target = np.matrix(np.fromfunction(g(targetswap, target), (d**dits,d**dits)), dtype='complex128')
        self._prefix = np.dot(swap_source, swap_target)
        self._postfix = np.dot(swap_target, swap_source)


    def matrix(self, v):
       return utils.matrix_product(self._prefix, np.kron(self._step.matrix(v), np.eye(self._d**(self.dits-2))), self._postfix)

    def assemble(self, v, i=0):
        raise NotImplementedError("This whole class should probably be redone, and this can be rewritten then")
        if self._name == None:
            return "REMAP q{} q{} [{}]".format(self._source, self._target, self._step.assemble(v, i))
        else:
            return "{} q{} q{}".format(self._name, self._source, self._target)

    def __repr__(self):
        return "RemapStep({}, {}, {}, {}, name={}, d={})".format(self._step, self.dits, self._source, self._target, self._name, self._d)



class CNOTRootStep(QuantumStep):
    _cnr = np.matrix([[1,0,0,0],
                       [0,1,0,0],
                       [0,0,0.5+0.5j,0.5-0.5j],
                       [0,0,0.5-0.5j,0.5+0.5j]])
    def __init__(self):
        self.num_inputs = 0
        self.dits = 2

    def matrix(self, v):
        return CNOTRootStep._cnr

    def assemble(self, v, i=0):
        return [("gate", "sqrt(CNOT)", (), (i, i+1))]

    def __repr__(self):
        return "CNOTRootStep()"

class KroneckerStep(QuantumStep):
    def __init__(self, *substeps):
        self.num_inputs = sum([step.num_inputs for step in substeps])
        self._substeps = substeps
        self.dits = sum([step.dits for step in substeps])

    def matrix(self, v):
        matrices = []
        index = 0
        for step in self._substeps:
            U = step.matrix(v[index:index+step.num_inputs])
            matrices.append(U)
            index += step.num_inputs
        U = matrices[0]
        for matrix in matrices[1:]:
            U = np.kron(U, matrix)
        return U

    def assemble(self, v, i=0):
        out = []
        index = 0
        for step in self._substeps:
            out += step.assemble(v[index:index+step.num_inputs], i)
            index += step.num_inputs
            i += step.dits
        return [("block", out)]

    def appending(self, step):
        return KroneckerStep(*self._substeps, step)

    def _draw_assemble(self, i=0):
        endlist = []
        for step in self._substeps:
            endlist += step._draw_assemble(i)
            i += step.dits
        return endlist

    def __deepcopy__(self, memo):
        return KroneckerStep(self._substeps.__deepcopy__(memo))

    def __repr__(self):
        return "KroneckerStep({})".format(repr(self._substeps)[1:-1])

class ProductStep(QuantumStep):
    def __init__(self, *substeps):
        self.num_inputs = sum([step.num_inputs for step in substeps])
        self._substeps = substeps
        self.dits = 0 if len(substeps) == 0 else substeps[0].dits

    def matrix(self, v):
        matrices = []
        index = 0
        for step in self._substeps:
            U = step.matrix(v[index:index+step.num_inputs])
            matrices.append(U)
            index += step.num_inputs
        U = matrices[0]
        for matrix in matrices[1:]:
            U = np.matmul(U, matrix)
        return U

    def assemble(self, v, i=0):
        out = []
        index = 0
        for step in self._substeps:
            out += step.assemble(v[index:index+step.num_inputs], i)
            index += step.num_inputs
        return out

    def _draw_assemble(self, i=0):
        endlist = []
        for step in self._substeps:
            endlist += step._draw_assemble(i)
        return endlist

    def appending(self, *steps):
        return ProductStep(*self._substeps, *steps)

    def __deepcopy__(self, memo):
        return ProductStep(self._substeps.__deepcopy__(memo))

    def __repr__(self):
        return "ProductStep({})".format(repr(self._substeps)[1:-1])

