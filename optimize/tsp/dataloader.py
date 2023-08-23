import requests
from typing import List

import numpy as np
import pandas as pd
from scipy.spatial.distance import squareform, pdist


session = requests.Session()


def get_distance_xy(dataframe: pd.DataFrame, metric="euclidean"):
    distances = squareform(
        pdist(dataframe.loc[:, ["x", "y"]].values, metric=metric)
    )
    return distances


def get_request_points(coordinates: pd.DataFrame) -> List[str]:
    return coordinates.apply(lambda x: f"{x['long']},{x['lat']}", axis=1).to_list()


def break_chunks(points: List[int], size=100) -> List[List[int]]:
    points = list(points)
    return [points[i: i + size] for i in range(0, len(points), size)]


def request_matrix_asym(
    points: List[str], sources: List[int], destinations: List[int],
    annotations="duration,distance", timeout=60, verify=False, **kwargs,
) -> dict:
    req = "https://router.project-osrm.org/table/v1/driving/"
    pts_str = ";".join(points)
    sources_str = ";".join([str(x) for x in sources])
    dest_str = ";".join([str(x) for x in destinations])
    req = req + f"{pts_str}?sources={sources_str}&destinations={dest_str}&annotations={annotations}"
    response = session.get(req, timeout=timeout, verify=verify, **kwargs).json()
    return response


def request_matrix(coordinates: pd.DataFrame, timeout=60, **kwargs):
    N = coordinates.shape[0]
    points_req = get_request_points(coordinates)
    chunks = break_chunks(range(N), size=100)
    distances = np.full((N, N), np.nan)
    durations = np.full((N, N), np.nan)
    for i in range(len(chunks)):
        for j in range(len(chunks)):
            sources = chunks[i]
            destinations = chunks[j]
            out = request_matrix_asym(points_req, sources, destinations, timeout=timeout, **kwargs)
            _fill_matrix(distances, sources, destinations, out["distances"])
            _fill_matrix(durations, sources, destinations, out["durations"])
    result = {"distances": distances, "durations": durations}
    return result


def _fill_matrix(matrix, rows, columns, values):
    matrix[np.atleast_2d(rows).T, np.atleast_2d(columns)] = np.array(values)
