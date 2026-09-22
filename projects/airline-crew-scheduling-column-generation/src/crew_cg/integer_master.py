from __future__ import annotations

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


def solve_integer_master(flights, pairings):
    """Solve the set-covering restricted master with binary pairing decisions."""
    n_flights = len(flights)
    n_cols = len(pairings)
    coverage = np.zeros((n_flights, n_cols), dtype=float)
    for column, pairing in enumerate(pairings):
        for flight_id in pairing.flight_ids:
            coverage[flight_id, column] = 1.0

    objective = np.asarray([pairing.cost for pairing in pairings], dtype=float)
    constraints = LinearConstraint(
        coverage,
        lb=np.ones(n_flights, dtype=float),
        ub=np.full(n_flights, np.inf, dtype=float),
    )
    result = milp(
        c=objective,
        integrality=np.ones(n_cols, dtype=int),
        bounds=Bounds(np.zeros(n_cols), np.ones(n_cols)),
        constraints=constraints,
        options={"disp": False},
    )
    if not result.success:
        raise RuntimeError(result.message)
    selected = [pairings[index] for index, value in enumerate(result.x) if value > 0.5]
    return {
        "objective": float(result.fun),
        "x": np.asarray(result.x),
        "selected": selected,
    }


def integrality_gap(lp_objective: float, integer_objective: float) -> float:
    if integer_objective <= 0:
        return 0.0
    return float((integer_objective - lp_objective) / integer_objective)
