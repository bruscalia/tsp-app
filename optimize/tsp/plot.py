from typing import List, Tuple, Union
from itertools import cycle

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
import folium

from optimize.tsp.dataloader import get_request_points


session = requests.Session()
COLORS = cycle(['beige', 'black', 'blue', 'cadetblue',
                'darkblue', 'darkgreen', 'darkpurple',
                'darkred', 'gray', 'green', 'lightblue',
                'lightgray', 'lightgreen', 'lightred',
                'orange', 'pink', 'purple', 'red', 'white'])


def plot_tour(
    tour: List[int],
    coordinates: np.ndarray,
    color="navy",
    figsize=[6, 5],
    dpi=100,
    **kwargs
):
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi, **kwargs)
    t = np.array(tour)
    x = coordinates[t, 0]
    y = coordinates[t, 1]
    ax.scatter(x, y, color=color)
    ax.plot(x, y, color=color)

    fig.tight_layout()
    return fig


def get_coord_path(coordinates: pd.DataFrame) -> List[Tuple[float, float]]:
    pts = get_request_points(coordinates)
    pts_req = ";".join(pts)
    r = session.get(
        f"http://router.project-osrm.org/route/v1/car/{pts_req}?overview=false&steps=true"
    )
    result = r.json()
    first_route = result["routes"][0]
    coords = [(p["location"][1], p["location"][0])
              for l in first_route["legs"]
              for s in l["steps"]
              for p in s["intersections"]]
    return coords


def create_map(
    tour: List[int],
    coordinates: pd.DataFrame,
    color:Union[str, tuple] = "darkblue",
    zoom_start=8,
    **kwargs
):

    # Create map
    m = folium.Map(zoom_start=zoom_start)
    coord_rt = coordinates.loc[tour, :]
    path = get_coord_path(coord_rt)
    new_line = folium.PolyLine(
        path, weight=4, opacity=1.0,
        color=color, tooltip=f"Route",
        **kwargs
    )
    new_line.add_to(m)

    # Trim zoom
    sw = coordinates[["lat", "long"]].min(axis=0).to_list()
    ne = coordinates[["lat", "long"]].max(axis=0).to_list()

    m.fit_bounds([sw, ne])
    return m


def plot_map(
    path: List[Tuple[float, float]],
    color: Union[str, tuple] = "darkblue",
    zoom_start=8,
    **kwargs
):
    # Coordinates from path
    lat, long = zip(*path)

    # Create map
    m = folium.Map(zoom_start=zoom_start)
    new_line = folium.PolyLine(
        path, weight=4, opacity=1.0,
        color=color, tooltip=f"Route",
        **kwargs
    )
    new_line.add_to(m)

    # Trim zoom
    sw = [min(lat), min(long)]
    ne = [max(lat), max(long)]

    m.fit_bounds([sw, ne])
    return m
