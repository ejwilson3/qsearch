from multiprocessing import Pool, cpu_count
from functools import partial
from timeit import default_timer as timer
import heapq

from .circuits import *

from . import gatesets as gatesets
from .solver import CMA_Solver
from . import utils as utils
from .logging import logprint
from . import checkpoint

class Compiler():
    def compile(self, U, depth):
        return (U, None, None)

def evaluate_step(step, U, error_func, solver, initial_guess=None):
    return (step, solver.solve_for_unitary(step, U, error_func, initial_guess))

class SearchCompiler(Compiler):
    def __init__(self, threshold=0.01, d=2, error_func=util.matrix_distance_squared, gateset=gatesets.Default(), solver=CMA_Solver()):
        self.threshold = threshold
        self.error_func = error_func
        self.d = d
        self.gateset = gateset
        self.solver = solver

    def compile(self, U, depth=None, statefile=None):
        n = np.log(np.shape(U)[0])/np.log(self.d)

        if self.d**n != np.shape(U)[0]:
            raise ValueError("The target matrix of size {} is not compatible with qudits of size {}.".format(np.shape(U)[0], self.d))
        n = int(n)

        initial_layer = self.gateset.initial_layer(n, self.d)
        search_layers = self.gateset.search_layers(n, self.d)

        logprint("There are {} processors available to Pool.".format(cpu_count()))
        logprint("The branching factor is {}.".format(len(search_layers)))
        pool = Pool(min(len(search_layers),cpu_count()))
        logprint("Creating a pool of {} workers".format(pool._processes))

        recovered_state = checkpoint.recover(statefile)
        queue = []
        best_depth = 0
        best_value = 0
        best_pair  = 0
        tiebreaker = 0
        if recovered_state == None:
            root = ProductStep(initial_layer)
            root.index = 0
            result = self.solver.solve_for_unitary(root, U, self.error_func)
            best_value = self.error_func(U, result[0])
            best_pair = (result[0], root, result[1])
            logprint("New best! {} at depth 0".format(best_value/10))
            if depth == 0:
                return best_pair

            queue = [(best_value, 0, -1, result[1], root)]
            checkpoint.save((queue, best_depth, best_value, best_pair, tiebreaker), statefile)
        else:
            queue, best_depth, best_value, best_pair, tiebreaker = recovered_state
            logprint("Recovered state with best result {} at depth {}".format(best_value/10, best_depth))

        while len(queue) > 0:
            popped_value, current_depth, _, current_vector, current_step = heapq.heappop(queue)
            then = timer()
            logprint("Popped a node with score: {} at depth: {} with branch index: {}".format((popped_value - current_depth)/10, current_depth, current_step.index))
            new_steps = [current_step.appending(search_layer) for search_layer in search_layers]
            for i in range(0, len(new_steps)):
                new_steps[i].index = i

            for step, result in pool.imap_unordered(partial(evaluate_step, U=U, error_func=self.error_func, solver=self.solver, initial_guess=current_vector), new_steps):
                current_value = self.error_func(U, result[0])
                logprint("{}\t{}".format(current_value, current_depth+1), custom="heuristic-test")
                if current_value < best_value:
                    best_value = current_value
                    best_pair = (result[0], step, result[1])
                    best_depth = current_depth + 1
                    logprint("New best! score: {} at depth: {} with branch index: {}".format(best_value/10, current_depth + 1, step.index))
                    if best_value < self.threshold:
                        pool.close()
                        pool.terminate()
                        queue = []
                        break
                if depth is None or current_depth + 1 < depth:
                    heapq.heappush(queue, (current_value+current_depth+1, current_depth+1, tiebreaker, result[1], step))
                    tiebreaker+=1
            logprint("Layer completed after {} seconds".format(timer() - then))
            checkpoint.save((queue, best_depth, best_value, best_pair, tiebreaker), statefile)


        pool.close()
        pool.terminate()
        pool.join()
        logprint("Finished compilation at depth {} with score {}.".format(best_depth, best_value/10))
        logprint("final depth: {}".format(best_depth), custom="heuristic-depth")
        if statefile == None:
            checkpoint.delete()
        return best_pair


