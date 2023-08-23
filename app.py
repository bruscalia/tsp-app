import os
from io import BytesIO
import json

import streamlit as st
import pandas as pd
from pyomo.contrib.appsi.solvers.highs import Highs
from streamlit_folium import st_folium

from optimize.tsp import get_distance_xy, build_mip, solve_mip, TSP, plot_tour, request_matrix,\
    create_map


# Converts dataframe to csv to download
@st.cache
def convert_df(dataframe: pd.DataFrame):
    return dataframe.to_csv().encode('utf-8')


# Finds distance matrix
@st.cache
def driving_distances(dataframe: pd.DataFrame):
    return request_matrix(dataframe)["distances"] / 1000


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


# Creates MIP paramters
def mip_parameters():
    params = {}
    params["time_limit"] = st.sidebar.number_input("Time limit:", min_value=0, step=10, value=10)
    json_file = st.sidebar.file_uploader("Solver config", type=["json"])
    if json_file is not None:
        custom_params = json.load(json_file)
        for key, value in custom_params.items():
            params[key] = value
    return params


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

problem_type = st.sidebar.selectbox("Choose an input type:", ["xy", "lat-long"], index=0)
st.write(MESSAGES[problem_type])
file = st.file_uploader("Upload input file", type=["csv"])

method = st.sidebar.selectbox("Choose a strategy:", ["MIP", "Heuristic"], index=0)
time_limit = st.sidebar.number_input("time limit", min_value=0, value=5, step=1)

if file is not None:
    dataframe = pd.read_csv(file)
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

        # Solve Heuristic
        elif method == "Heuristic":
            model = TSP(distances)
            tour = model.solve(time_limit=time_limit)

        # Display the results
        col_left, col_right = st.columns(2)
        sol = model.obj()
        col_left.write(f"Current solution: {sol:.3f}")
        col_right.download_button(
            label="Download Output",
            data=json.dumps(tour),
            file_name='output.json',
            mime='json',
        )

        # Plot solution
        if problem_type == "xy":
            fig = plot_tour(tour, dataframe[COORDS[problem_type]].values, dpi=100)
            buffer = BytesIO()
            fig.savefig(buffer, format="png")
            st.image(buffer)

        elif problem_type == "lat-long":
            map = create_map(tour, dataframe)
            st_folium(map, width=700, height=500, returned_objects=[])
