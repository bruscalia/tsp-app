import os
from io import BytesIO
import json
from typing import List

import pandas as pd
from pyomo.contrib.appsi.solvers.highs import Highs
import streamlit as st
from streamlit_folium import st_folium

from optimize.tsp import get_distance_xy, build_mip, solve_mip, TSP, plot_tour, request_matrix,\
    plot_map, get_coord_path


# Create current solution as session_state
if "tour" not in st.session_state:
    st.session_state.tour = None

if "dataframe" not in st.session_state:
    st.session_state.dataframe = None

if "sol" not in st.session_state:
    st.session_state.sol = None

if "route_path" not in st.session_state:
    st.session_state.route_path = None


# Finds distance matrix
@st.cache
def driving_distances(dataframe: pd.DataFrame):
    return request_matrix(dataframe)["distances"] / 1000


# Callback uploading a new file
def upload_callback():
    st.session_state.tour = None
    st.session_state.sol = None
    st.session_state.route_path = None


# Update route path after solution
def update_path(tour: List[int], dataframe: pd.DataFrame):
    coord_rt = dataframe.loc[tour, :]
    path = get_coord_path(coord_rt)
    st.session_state.route_path = path


MESSAGES = {
    "xy": "Your file must have columns with 'x' and 'y' coordinates",
    "lat-long": "Your file must have columns with 'lat' and 'long' coordinates",
}

FORMATS = {
    "xy": get_distance_xy,
    "lat-long": driving_distances
}

COORDS = {
    "xy": ["x", "y"],
    "lat-long": ["long", "lat"]
}


# Read section of the README file
def read_section(section):
    capture_content = False
    content = []
    with open("README.md", mode="r", encoding="utf8") as file:
        for line in file:
            if line.startswith("## ") and capture_content:
                break
            if capture_content:
                content.append(line)
            if line.startswith(f"## {section}"):
                capture_content = True
                content.append(line)
    out = "\n".join(content)
    return out


# Path to icon
icon_path = os.path.join("assets", "icon_tsp.png")

# Set the page config to wide mode
st.set_page_config(
    page_title="TSP",
    page_icon=icon_path,
    layout="wide",
)

st.sidebar.image(icon_path)

st.title("TSP")
st.write("Welcome to the Traveling Salesman Problem solver.")

display_tutorial = st.checkbox("Display tutorial")
if display_tutorial:
    section = st.selectbox("Choose a section", ["Execution", "Solutions", "Contact"], index=1)
    tutorial = read_section(section)
    st.markdown(tutorial)

problem_type = st.sidebar.selectbox("Choose an input type:", ["xy", "lat-long"], index=0)
st.write(MESSAGES[problem_type])
file = st.file_uploader("Upload input file", type=["csv"], on_change=upload_callback)

method = st.sidebar.selectbox("Choose a strategy:", ["MIP", "Heuristic"], index=0)
time_limit = st.sidebar.number_input("Time limit", min_value=0, value=5, step=1)

if file is not None:
    dataframe = pd.read_csv(file)
    st.session_state.dataframe = dataframe
    distances = FORMATS[problem_type](dataframe)
    start_button = st.button("Optimize")

    # Run if start is pressed
    if file is not None and start_button:

        # Solve MIP
        if method == "MIP":
            solver = Highs()
            solver.highs_options = {"time_limit": time_limit}
            model = build_mip(distances)
            tour = solve_mip(model, solver)
            st.session_state.tour = tour

        # Solve Heuristic
        elif method == "Heuristic":
            model = TSP(distances)
            tour = model.solve(time_limit=time_limit)
            st.session_state.tour = tour

        # Display the results
        sol = model.obj()
        st.session_state.sol = sol

        # Update path in case of lat-long
        if problem_type == "lat-long":
            update_path(tour, dataframe)

# Compute current state variables
sol = st.session_state.sol
tour = st.session_state.tour
dataframe = st.session_state.dataframe

if sol is not None and tour is not None:
    col_left, col_right = st.columns(2)
    col_left.write(f"Current solution: {sol:.3f}")
    col_right.download_button(
        label="Download Output",
        data=json.dumps(tour),
        file_name='output.json',
        mime='json',
    )

if tour is not None and dataframe is not None:

    # Plot solution
    if problem_type == "xy":
        fig = plot_tour(tour, dataframe[COORDS[problem_type]].values, dpi=100)
        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        st.image(buffer)

    elif problem_type == "lat-long":
        map = plot_map(st.session_state.route_path)
        # map = create_map(tour, dataframe)
        st_folium(map, width=700, height=500, returned_objects=[])
