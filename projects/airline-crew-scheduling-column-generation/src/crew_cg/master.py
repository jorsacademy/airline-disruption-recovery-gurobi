import numpy as np
from scipy.optimize import linprog


def solve_master(flights, pairings):
    n_flights = len(flights)
    n_cols = len(pairings)
    A = np.zeros((n_flights, n_cols))
    for j, pairing in enumerate(pairings):
        for flight_id in pairing.flight_ids:
            A[flight_id, j] = 1.0

    c = np.array([p.cost for p in pairings], dtype=float)
    # Coverage constraints A x >= 1 become -A x <= -1.
    result = linprog(
        c,
        A_ub=-A,
        b_ub=-np.ones(n_flights),
        bounds=[(0.0, None)] * n_cols,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(result.message)

    # HiGHS marginals correspond to -A x <= -1; coverage duals are their negatives.
    duals = -np.asarray(result.ineqlin.marginals)
    return {
        "objective": float(result.fun),
        "x": np.asarray(result.x),
        "duals": duals,
    }
