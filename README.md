# TSP

An optimization app for the Traveling Salesman Problem.


## Tutorial

### Python

To run locally, please install Python libraries included in the file `requirements.txt`

```pip install -r requirements.txt```

And include separately google `ortools` lib, which has conflicting dependencies with `streamlit`.

```pip install --no-deps ortools==9.7.2996```

Then, exexcute streamlit via command line:

```streamlit run app.py```

### Docker

To build an image locally, make sure you have docker installed in your computer and run the following command:

```docker build -t tsp_app:latest .```

You can replace `tsp_app` by any repository name you would like and `latest` by any version.

Then you can run your app by running

```docker run -p 8501:8501 tsp_app:latest```


## Solutions

### Heuristic

The heuristic strategies for the TSP provided in google `ortools` are unlikely to prove optimality, but can provide good quality solutions for large instances in a short time. They are based on a greedy constructive phase + local search.


### MIP

The model adopted considers a directed graph $G(V, A)$ connecting nodes $V$ through arcs $A$. The decision variables are binaries that indicate if an arc $i, j$ is part of the solution. Our goal is to minimize the total cost, which for each arc is $c_{i, j}$.

$$
\begin{align}
    \text{min} \quad & \sum_{i, j \in A} c_{i, j} x_{i, j} \\
    \text{s.t.} \quad & \sum_{j \in V \setminus{\{i\}}} x_{i, j} = \sum_{j \in V \setminus{\{i\}}} x_{j, i} = 1 & \forall \; i \in V \\
    & \sum_{i \in S} \sum_{j \in V \setminus{\{S\}}} x_{i, j} \geq 1 & \forall \; S \subseteq V, |S| \leq |V| / 2 \\
    & x_{i, j} \in \{0, 1\} & \forall \; i, j \in A\\
\end{align}
$$


## Contact

You can reach out to me at bruscalia12@gmail.com
