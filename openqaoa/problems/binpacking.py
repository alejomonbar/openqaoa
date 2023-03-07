#   Copyright 2022 Entropica Labs
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import numpy as np

from typing import Union
from docplex.mp.model import Model
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import itertools


from .problem import Problem
from .converters import FromDocplex2IsingModel
from .qubo import QUBO
from openqaoa.workflows.optimizer import QAOA




class BinPacking(Problem):
    """
    Creates an instance of the Bin Packing problem.
    https://en.wikipedia.org/wiki/Bin_packing_problem
    
    Parameters
    ----------
    weights: List[int]
        The weight of the items that must be placed in the bins.
    weight_capacity: int
        The maximum weight the bin can hold.
    penalty: float
        Penalty for the weight constraint.
        
    Returns
    -------
        An instance of the Bin PAcking problem.
    """

    __name__ = "binpacking"
    
    def __init__(self, weights:list=[], weight_capacity:int=0, penalty:Union[float, list]=[],
                 n_bins:int = None, simplifications=True, method="slack"):
        #include_ineqs: True if including the inequalities

        self.weights = weights
        self.weight_capacity = weight_capacity
        self.penalty = penalty
        self.n_items = len(weights)
        self.method = method
        self.simplifications = simplifications
        self.eq_constraints = {}
        self.ineq_constraints = {}
        if n_bins is None:
            self.n_bins = self.n_items
        else:
            self.n_bins = n_bins
        if len(weights) > 0:
            self.solution = self.solution_dict()
            self.cplex_model = self.docplex_model()
            self.n_vars = self.cplex_model.number_of_binary_variables
            
    def solution_dict(self):
        solution = {f"y_{i}":None for i in range(self.n_bins)}
        for i in range(self.n_items):
            for j in range(self.n_bins):
                solution[f"x_{i}_{j}"] = None
        if self.simplifications:
            # First simplification: we know the minimum number of bins
            self.min_bins = int(np.ceil(np.sum(self.weights) / self.weight_capacity))
            for j in range(self.n_bins):
                if j < self.min_bins:
                    solution[f"y_{j}"] = 1
            solution["x_0_0"] = 1
            for j in range(1, self.n_bins):
                solution[f"x_0_{j}"] = 0
        return solution

    def random_instance(self, n_items:int=3, min_weight:int=1, max_weight:int=5,
                        weight_capacity:int=10, simplification=True, seed:int=1):
        np.random.seed(seed)
        self.weight_capacity = weight_capacity
        self.n_items = n_items
        self.n_bins = n_items
        if min_weight >= max_weight:
            raise ValueError(f"min_weight: {min_weight} must be < max_weight:{max_weight}")
        self.weights = list(np.random.randint(min_weight, max_weight, n_items))
        self.simplifications = simplification
        self.solution = self.solution_dict()
        self.cplex_model = self.docplex_model()
        self.n_vars = self.cplex_model.number_of_binary_variables

    def docplex_model(self):
        mdl = Model("bin_packing")
        vars_ = {}
        for var in self.solution.keys():
            if self.solution[var] is None:
                vars_[var] = mdl.binary_var(var)
            else:
                vars_[var] = self.solution[var]
        objective = mdl.sum([vars_[y] for y in vars_.keys() if y[0] == "y"])
        self.vars_pos = {var.name:n for n, var in enumerate(mdl.iter_binary_vars())}

        mdl.minimize(objective)
        if self.simplifications:
            list_items = range(1, self.n_items)
        else:
            list_items = range(self.n_items)

        for i in list_items:
            # First set of constraints: the items must be in any bin
            self.eq_constraints[f"eq_{i}"] = [[self.vars_pos[f"x_{i}_{j}"] for j in range(self.n_bins)], [1]]
            mdl.add_constraint(mdl.sum(vars_[f"x_{i}_{j}"] for j in range(self.n_bins)) == 1)

        for j in range(self.n_bins):
            # Second set of constraints: weight constraints
            mdl.add_constraint(
                mdl.sum((self.weights[i]/self.weight_capacity) * vars_[f"x_{i}_{j}"] for i in range(self.n_items)) <=  vars_[f"y_{j}"]
            )
            if self.simplifications and j < self.min_bins:
                if j == 0:
                    self.ineq_constraints[f"ineq_{j}"] = [[self.vars_pos[f"x_{i}_{j}"] for i in list_items], [self.weight_capacity - self.weights[0]]]
                else:
                    self.ineq_constraints[f"ineq_{j}"] = [[self.vars_pos[f"x_{i}_{j}"] for i in list_items], [self.weight_capacity]]
                    
            else:
                self.ineq_constraints[f"ineq_{j}"] = [[self.vars_pos[f"x_{i}_{j}"] for i in list_items], [self.vars_pos[f"y_{j}"]]]

        return mdl

    def get_qubo_problem(self):
        """
        Returns the QUBO encoding of this problem.
        
        Returns
        -------
            The QUBO encoding of this problem.
        """
        if len(self.penalty) > 0:
            if self.method == "slack":
                qubo = FromDocplex2IsingModel(self.cplex_model, multipliers=self.penalty)
            elif self.method == "unbalanced":
                qubo = FromDocplex2IsingModel(self.cplex_model, multipliers=self.penalty[0], unbalanced_const=True, strength_ineq=self.penalty[1:])
        else:
            if self.method == "slack":
                qubo = FromDocplex2IsingModel(self.cplex_model)
            elif self.method == "unbalanced":
                qubo = FromDocplex2IsingModel(self.cplex_model, unbalanced_const=True)
            
        return qubo.ising_model
    
    def classical_solution(self, string=False):
        docplex_sol = self.cplex_model.solve()
        if string:
            solution = ""
        else:
            solution = self.solution.copy()
        for var in self.cplex_model.iter_binary_vars():
            if string:
                solution += str(int(np.round(docplex_sol.get_value(var), 1)))
            else:
                solution[var.name] = int(np.round(docplex_sol.get_value(var), 1))
        if not docplex_sol.is_valid_solution():
            raise ValueError("The Cplex solver does not find a solution.")
        return solution
    
    def plot_solution(self, solution:Union[dict, str], ax=None):
        if isinstance(solution, str):
            sol = self.solution.copy()
            for n, var in enumerate(self.cplex_model.iter_binary_vars()):
                sol[var.name] = int(solution[n])
            solution = sol
        colors = plt.cm.get_cmap("jet", len(self.weights))
        if ax is None:
            fig, ax = plt.subplots()
        for j in range(self.n_bins):
            sum_items = 0
            if solution[f"y_{j}"]:
                for i in range(self.n_items):
                    if solution[f"x_{i}_{j}"]:
                        ax.bar(j, self.weights[i], bottom=sum_items, label=f"item {i}", color=colors(i), alpha=0.7, edgecolor="black")
                        sum_items += self.weights[i]
        ax.hlines(self.weight_capacity, -0.5, self.n_bins - 0.5, linestyle="--", color="black", label="Max Weight")
        ax.set_xticks(np.arange(self.n_bins), fontsize=14)
        ax.set_xlabel("bin", fontsize=14)
        ax.set_ylabel("weight", fontsize=14)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2 + 0.011*self.n_items), ncol=5, fancybox=True, shadow=True)
        return fig 
    
    def find_penalty_terms(self, penalty0:list=[0.1], n_items:int=3, n_mdls:int=3):
        """
        Tuning the penalization terms for an instance of the bin packing problem

        Parameters
        ----------
        penalty0 : List, optional
            Initial condition of the penalization terms. The default is [0.1].
        n_items : Int, optional
            number of items for what the optimal parameters are looked. The default is 3.
            Note: more items is a trade-off between better performance and time spent in tuning the parameters
        n_mdls: Int, optional
            number of different random problem to find the parameters (best for generalization)
        Raises
        ------
        ValueError
            Is there is a value of max weight that does not make sense?.

        Returns
        -------
        tuple
            (penalization terms, results on the specific problem).

        """
        # n_items: the number of items to optimize from
        min_weight = min(self.weights)
        max_weight = max(self.weights)
        
        if min_weight == max_weight and max_weight > 1:
            if max_weight > 1:
                min_weight -= 1
            else:
                raise ValueError(f"max weight cannot be {max_weight}")
        
        def get_penalty(penalty, problems, sol_str, callback=False):
            probability = 0
            const_not = 0
            for n_problem in problems.keys():
                problem = problems[n_problem]
                if self.method == "unbalanced":
                    if len(penalty) != 3:
                        raise ValueError(f"The penalization term must include 3 terms. 1 for the equality constraint and 2 for the unbalanced, given {len(penalty)}")
                    ising = FromDocplex2IsingModel(
                                problem.cplex_model,
                                multipliers=penalty[0],
                                unbalanced_const=True,
                                strength_ineq=penalty[1:]
                                ).ising_model
                elif self.method == "slack":
                    if len(penalty) != 1:
                        raise ValueError(f"The penalization term must include 1 term for the equality and inequality constraints , given {len(penalty)}")
                    ising = FromDocplex2IsingModel(
                                problem.cplex_model,
                                multipliers=penalty[0],
                                unbalanced_const=False,
                                ).ising_model
                
                qaoa = QAOA()
                params = {'betas': [-np.pi/8], 'gammas': [-np.pi/4]} 
                qaoa.set_circuit_properties(p=1, init_type="custom", variational_params_dict=params)
                qaoa.set_classical_optimizer(maxiter=100)
                qaoa.compile(ising)
                qaoa.optimize()
                results = qaoa.results.lowest_cost_bitstrings(2**problem.n_vars)
                pos = results["solutions_bitstrings"].index(sol_str[n_problem])
    
                probability += results["probabilities"][pos]
                # probability = self.optimal_prob([beta_opt, gamma_opt], qaoa, sol_str)
                const_not += problem.constraints_not_fulfilled(results["solutions_bitstrings"][0])
                if callback:
                    return {"result":results, "pos":pos, "CoP":probability * 2**problem.n_vars,
                            "probability":probability, "n_vars":problem.n_vars, "x0":penalty,
                            "constraints_not_fulfilled":const_not}
    
                print(f"lambda0: {penalty} | not fulfilled {const_not}| pos:{pos} | CoP:{probability*2**problem.n_vars}")
            return const_not - probability
        mdls = {}
        sol_str = {}
        for n_mdl in range(n_mdls):
            mdls[n_mdl] = BinPacking(method=self.method)
            mdls[n_mdl].random_instance(n_items, min_weight, max_weight, self.weight_capacity, seed=n_mdl)
            sol_str[n_mdl] = mdls[n_mdl].classical_solution(string=True)
        print("----------------------  Finding Inequalities -------------------")
        bounds = ((0,10),(0,5),(0,5))
        sol_ineq = minimize(get_penalty, x0=penalty0, bounds=bounds, method="Nelder-Mead", args=(mdls, sol_str), options={"maxiter":100,"maxfeval":100})#, options={"maxfev":100})
        x = sol_ineq.x
        self.penalty = x
        return x, get_penalty(x, mdls, sol_str, callback=True)
    
    def landscape_energy(self, qaoa_mdl, betas, gammas):
        n_betas = len(betas)
        n_gammas = len(gammas)
        landscape =[ ]
        for params in itertools.product(betas, gammas):
            landscape.append(self.cost_energy(params, qaoa_mdl))
        landscape = np.array(landscape)
        landscape = landscape.reshape((n_betas, n_gammas))
        return landscape

    def cost_energy(self, params, qaoa):
       varational_params = qaoa.variate_params
       varational_params.update_from_raw(params)
       return qaoa.backend.expectation(varational_params) 

    def optimal_prob(self, params, qaoa, optimal):
        varational_params = qaoa.variate_params
        varational_params.update_from_raw(params)
        probs_set = qaoa.backend.probability_dict(varational_params)[optimal]
        return probs_set        
    
    def normalizing(self, problem, normalized=-1):
        abs_weights = np.unique(np.abs(problem.weights))
        arg_sort = np.argsort(abs_weights)
        max_weight = abs_weights[arg_sort[normalized]]
        weights = [weight / max_weight for weight in problem.weights]
        terms = problem.terms
        terms.append([])
        weights.append(problem.constant/ max_weight)
        return QUBO(self.n_vars, terms, weights)
    
    def constraints_not_fulfilled(self, solution):
        check = 0
        for constraint in self.eq_constraints.values():
            vec = np.zeros(self.n_vars)
            vec[constraint[0]] = 1
            lh = np.sum(vec * np.array([int(i) for i in solution]))
            if lh != constraint[1][0]:
                check += 1
        for ii, constraint in enumerate(self.ineq_constraints.values()):
            vec = np.zeros(self.n_vars)
            if self.simplifications:
                weights = self.weights[1:]
                if ii < self.min_bins:
                    rhs = constraint[1][0]
                else:
                    rhs = self.weight_capacity * int(solution[constraint[1][0]])
            else:
                weights = self.weights
                rhs = self.weight_capacity * int(solution[constraint[1]])
            vec[constraint[0]] = weights
            lh = np.sum(vec * np.array([int(i) for i in solution]))
            if lh > rhs:
                check += 1 
        return check