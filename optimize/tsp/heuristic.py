import numpy as np
from tspgrasp import Grasp, SemiGreedyArc


class TSP:

    grasp: Grasp

    def __init__(self, distances: np.ndarray, alpha=0.95, seed=None):

        self.n_points = len(distances)
        self.distances = np.round(distances, decimals=3)
        self.grasp = Grasp(seed=seed, constructive=SemiGreedyArc(seed=seed, alpha=alpha))
        self.tour = None
        self.cost = None

    def solve(self, time_limit=10):
        sol = self.grasp(self.distances, time_limit=time_limit, verbose=True)
        self.tour = sol.tour
        self.cost = sol.cost
        return self.tour

    def obj(self):
        return self.cost
