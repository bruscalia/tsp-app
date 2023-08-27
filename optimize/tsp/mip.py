import time

import numpy as np
import networkx as nx
import pyomo.environ as pyo


def arcs_in(model, i):
    return sum(model.x[:, i]) == 1.0


def arcs_out(model, i):
    return sum(model.x[i, :]) == 1.0


def subtour_elimination(model, S, Sout):
    nodes_out = sum(model.x[i, j] for i in S for j in Sout)
    return 1 <= nodes_out


def build_mip(distances: np.ndarray):

    # MIP model
    model = pyo.ConcreteModel()

    # Sets
    model.V = pyo.Set(initialize=range(len(distances)))
    model.A = pyo.Set(initialize=[(i, j) for i in model.V for j in model.V if i != j])

    # Parameters
    model.c = pyo.Param(model.A, initialize={(i, j): distances[i, j] for (i, j) in model.A})

    # Variables
    model.x = pyo.Var(model.A, within=pyo.Binary)

    # Constraints
    model.arcs_in = pyo.Constraint(model.V, rule=arcs_in)
    model.arcs_out = pyo.Constraint(model.V, rule=arcs_out)
    model.subtour_elimination = pyo.ConstraintList()

    # Objective
    model.obj = pyo.Objective(
        expr=sum(
            model.x[i, j] * model.c[i, j]
            for (i, j) in model.A
        ),
        sense=pyo.minimize,
    )

    return model


def find_arcs(model):
    arcs = []
    for i, j in model.A:
        if np.isclose(model.x[i, j].value, 1, atol=1e-1):
            arcs.append((i, j))
    return arcs


def find_subtours(arcs):
    G = nx.DiGraph(arcs)
    subtours = list(nx.strongly_connected_components(G))
    return subtours


def eliminate_subtours(model, subtours):
    proceed = False
    for S in subtours:
        if len(S) <= len(model.V) // 2:
            proceed = True
            Sout = {i for i in model.V if i not in S}
            model.subtour_elimination.add(subtour_elimination(model, S, Sout))
    return proceed


def _solve_step(model, solver, verbose=True):
    sol = solver.solve(model)
    arcs = find_arcs(model)
    subtours = find_subtours(arcs)
    if verbose:
        print(f"Current subtours: {subtours}")
    time.sleep(0.1)
    proceed = eliminate_subtours(model, subtours)
    return sol, proceed


def solve_mip(model, solver, verbose=False):
    proceed = True
    while proceed:
        sol, proceed = _solve_step(model, solver, verbose=verbose)
    tour = find_tour(model)
    return tour


def find_tour(model):
    node = 0
    tour = [node]
    while True:
        for j in model.V:
            if (node, j) in model.A:
                if np.isclose(model.x[node, j].value, 1):
                    node = j
                    tour.append(node)
                    break
        if node == 0:
            break
    return tour
