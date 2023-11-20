from typing import List

import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


class TSP:

    def __init__(self, distances: np.ndarray, tol=1e-8):

        self.n_points = len(distances)
        self.scale_factor = 1 / (tol * (np.max(distances) - np.min(distances)))
        self.distances = distances
        self._dist = np.round(self.distances * self.scale_factor, decimals=0).astype(int).tolist()

        # Create the routing index manager: number of nodes, number of vehicles, depot node
        self.manager = pywrapcp.RoutingIndexManager(
            self.n_points, 1, 0
        )

        # Create Routing Model
        self.routing = pywrapcp.RoutingModel(self.manager)

        # Same valid for any callback related to arcs/edges
        transit_callback_index = self.routing.RegisterTransitCallback(
            self._distance_callback
        )
        self.routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        self.solution = None

    def _distance_callback(self, from_index, to_index):
        from_node = self.manager.IndexToNode(from_index)
        to_node = self.manager.IndexToNode(to_index)
        dist = self._dist[from_node][to_node]
        return dist

    def solve(self, time_limit=10):

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.SIMULATED_ANNEALING
        )
        search_parameters.time_limit.FromSeconds(time_limit)
        self.solution = self.routing.SolveWithParameters(search_parameters)

        tour = self.get_tour()
        return tour

    def get_tour(self):
        tours = []
        for route_nbr in range(self.routing.vehicles()):
            index = self.routing.Start(route_nbr)
            tour = [self.manager.IndexToNode(index)]
            while not self.routing.IsEnd(index):
                index = self.solution.Value(self.routing.NextVar(index))
                tour.append(self.manager.IndexToNode(index))
            tours.append(tour)
        return tours[0]

    def obj(self):
        return self.solution.ObjectiveValue() / self.scale_factor
