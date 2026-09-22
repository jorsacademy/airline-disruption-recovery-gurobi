from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix


@dataclass(frozen=True)
class Flight:
    flight_id: str
    demand: int
    operating_cost: float
    delay_cost_per_min: float
    cancellation_cost: float


@dataclass(frozen=True)
class Scenario:
    name: str
    probability: float
    max_operated_flights: int
    delay_minutes: Dict[str, int]


def default_instance() -> Tuple[List[Flight], List[Scenario]]:
    flights = [
        Flight("F101", 150, 5200, 18, 18000),
        Flight("F102", 132, 4800, 16, 16500),
        Flight("F103", 170, 6100, 20, 21000),
        Flight("F104", 118, 4300, 15, 15000),
        Flight("F105", 145, 5000, 17, 17500),
        Flight("F106", 160, 5700, 19, 19500),
    ]
    scenarios = [
        Scenario("clear", 0.50, 6, {f.flight_id: 0 for f in flights}),
        Scenario("moderate", 0.30, 5, {
            "F101": 20, "F102": 15, "F103": 35, "F104": 10, "F105": 25, "F106": 30
        }),
        Scenario("severe", 0.20, 4, {
            "F101": 60, "F102": 45, "F103": 90, "F104": 40, "F105": 70, "F106": 80
        }),
    ]
    return flights, scenarios


def solve_stochastic_airline(flights: List[Flight], scenarios: List[Scenario]) -> dict:
    """Solve a two-stage stochastic flight-operation model.

    First-stage variable:
        x_f = 1 if flight f is planned/scheduled.

    Second-stage variables by scenario:
        y_fs = 1 if flight f operates in scenario s.
        c_fs = 1 if flight f is cancelled in scenario s.

    Linking: y_fs + c_fs = x_f.
    Scenario capacity limits the number of operated flights.
    The model minimizes planned operating cost plus expected delay/cancellation cost,
    while requiring at least five flights to be scheduled.
    """
    n_f = len(flights)
    n_s = len(scenarios)
    idx_x = {i: i for i in range(n_f)}
    offset_y = n_f
    idx_y = {(i, s): offset_y + s * n_f + i for s in range(n_s) for i in range(n_f)}
    offset_c = n_f + n_f * n_s
    idx_c = {(i, s): offset_c + s * n_f + i for s in range(n_s) for i in range(n_f)}
    n_var = n_f + 2 * n_f * n_s

    c = np.zeros(n_var)
    for i, f in enumerate(flights):
        c[idx_x[i]] = f.operating_cost
    for s, sc in enumerate(scenarios):
        for i, f in enumerate(flights):
            c[idx_y[(i, s)]] = sc.probability * f.delay_cost_per_min * sc.delay_minutes[f.flight_id]
            c[idx_c[(i, s)]] = sc.probability * f.cancellation_cost

    rows = []
    lb = []
    ub = []

    for s in range(n_s):
        for i in range(n_f):
            row = {idx_y[(i, s)]: 1.0, idx_c[(i, s)]: 1.0, idx_x[i]: -1.0}
            rows.append(row)
            lb.append(0.0)
            ub.append(0.0)

    for s, sc in enumerate(scenarios):
        row = {idx_y[(i, s)]: 1.0 for i in range(n_f)}
        rows.append(row)
        lb.append(-np.inf)
        ub.append(float(sc.max_operated_flights))

    row = {idx_x[i]: 1.0 for i in range(n_f)}
    rows.append(row)
    lb.append(5.0)
    ub.append(np.inf)

    A = lil_matrix((len(rows), n_var), dtype=float)
    for r, mapping in enumerate(rows):
        for j, val in mapping.items():
            A[r, j] = val

    constraints = LinearConstraint(A.tocsr(), np.array(lb), np.array(ub))
    result = milp(
        c=c,
        integrality=np.ones(n_var, dtype=int),
        bounds=Bounds(np.zeros(n_var), np.ones(n_var)),
        constraints=constraints,
        options={"disp": False},
    )
    if not result.success:
        raise RuntimeError(f"Optimization failed: {result.message}")

    x = result.x
    planned = [flights[i].flight_id for i in range(n_f) if x[idx_x[i]] > 0.5]
    scenario_results = {}
    for s, sc in enumerate(scenarios):
        operated = [flights[i].flight_id for i in range(n_f) if x[idx_y[(i, s)]] > 0.5]
        cancelled = [flights[i].flight_id for i in range(n_f) if x[idx_c[(i, s)]] > 0.5]
        scenario_results[sc.name] = {
            "operated": operated,
            "cancelled": cancelled,
            "capacity": sc.max_operated_flights,
        }

    return {
        "objective": float(result.fun),
        "planned": planned,
        "scenarios": scenario_results,
        "status": result.message,
    }
