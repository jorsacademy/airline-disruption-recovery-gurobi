"""Aircraft allocation under uncertain demand.

This module implements two linear-programming formulations of the classic
Dantzig aircraft allocation problem. The implementation mirrors the GAMS
model structure while keeping the two formulations independent.

Formulation 1 uses incremental demand variables and tail probabilities.
Formulation 2 uses explicit carried and bumped passenger variables by demand
state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

import pulp


Aircraft = str
Route = str
State = int

AIRCRAFT: tuple[Aircraft, ...] = ("a", "b", "c", "d")
ROUTES: tuple[Route, ...] = (
    "route-1",
    "route-2",
    "route-3",
    "route-4",
    "route-5",
)
STATES: tuple[State, ...] = (1, 2, 3, 4, 5)

DEMAND: Dict[Tuple[Route, State], float] = {
    ("route-1", 1): 200,
    ("route-1", 2): 220,
    ("route-1", 3): 250,
    ("route-1", 4): 270,
    ("route-1", 5): 300,
    ("route-2", 1): 50,
    ("route-2", 2): 150,
    ("route-3", 1): 140,
    ("route-3", 2): 160,
    ("route-3", 3): 180,
    ("route-3", 4): 200,
    ("route-3", 5): 220,
    ("route-4", 1): 10,
    ("route-4", 2): 50,
    ("route-4", 3): 80,
    ("route-4", 4): 100,
    ("route-4", 5): 340,
    ("route-5", 1): 580,
    ("route-5", 2): 600,
    ("route-5", 3): 620,
}

PROBABILITY: Dict[Tuple[Route, State], float] = {
    ("route-1", 1): 0.20,
    ("route-1", 2): 0.05,
    ("route-1", 3): 0.35,
    ("route-1", 4): 0.20,
    ("route-1", 5): 0.20,
    ("route-2", 1): 0.30,
    ("route-2", 2): 0.70,
    ("route-3", 1): 0.10,
    ("route-3", 2): 0.20,
    ("route-3", 3): 0.40,
    ("route-3", 4): 0.20,
    ("route-3", 5): 0.10,
    ("route-4", 1): 0.20,
    ("route-4", 2): 0.20,
    ("route-4", 3): 0.30,
    ("route-4", 4): 0.20,
    ("route-4", 5): 0.10,
    ("route-5", 1): 0.10,
    ("route-5", 2): 0.80,
    ("route-5", 3): 0.10,
}

OPERATING_COST: Dict[Tuple[Aircraft, Route], float] = {
    ("a", "route-1"): 18,
    ("a", "route-2"): 21,
    ("a", "route-3"): 18,
    ("a", "route-4"): 16,
    ("a", "route-5"): 10,
    ("b", "route-2"): 15,
    ("b", "route-3"): 16,
    ("b", "route-4"): 14,
    ("b", "route-5"): 9,
    ("c", "route-2"): 10,
    ("c", "route-4"): 9,
    ("c", "route-5"): 6,
    ("d", "route-1"): 17,
    ("d", "route-2"): 16,
    ("d", "route-3"): 17,
    ("d", "route-4"): 15,
    ("d", "route-5"): 10,
}

CAPACITY: Dict[Tuple[Aircraft, Route], float] = {
    ("a", "route-1"): 16,
    ("a", "route-2"): 15,
    ("a", "route-3"): 28,
    ("a", "route-4"): 23,
    ("a", "route-5"): 81,
    ("b", "route-2"): 10,
    ("b", "route-3"): 14,
    ("b", "route-4"): 15,
    ("b", "route-5"): 57,
    ("c", "route-2"): 5,
    ("c", "route-4"): 7,
    ("c", "route-5"): 29,
    ("d", "route-1"): 9,
    ("d", "route-2"): 11,
    ("d", "route-3"): 22,
    ("d", "route-4"): 17,
    ("d", "route-5"): 55,
}

AVAILABILITY: Dict[Aircraft, float] = {"a": 10, "b": 19, "c": 25, "d": 15}

BUMPING_COST: Dict[Route, float] = {
    "route-1": 13,
    "route-2": 13,
    "route-3": 7,
    "route-4": 7,
    "route-5": 1,
}


@dataclass
class ModelResult:
    status: str
    objective: float
    operating_cost: float
    bumping_cost: float
    aircraft_allocation: Dict[Tuple[Aircraft, Route], float]
    carried: Dict[Tuple[Route, State], float]
    bumped: Dict[Tuple[Route, State], float]


def _defined_route_states(route: Route) -> Iterable[State]:
    return (state for state in STATES if (route, state) in DEMAND)


def expected_demand() -> Dict[Route, float]:
    return {
        route: sum(
            PROBABILITY.get((route, state), 0.0)
            * DEMAND.get((route, state), 0.0)
            for state in STATES
        )
        for route in ROUTES
    }


def tail_probability() -> Dict[Tuple[Route, State], float]:
    return {
        (route, state): sum(
            PROBABILITY.get((route, later_state), 0.0)
            for later_state in STATES
            if later_state >= state
        )
        for route in ROUTES
        for state in STATES
    }


def incremental_demand() -> Dict[Tuple[Route, State], float]:
    increments: Dict[Tuple[Route, State], float] = {}
    for route in ROUTES:
        previous = 0.0
        for state in STATES:
            current = DEMAND.get((route, state), 0.0)
            increments[(route, state)] = current - previous if current != 0 else 0.0
            if current != 0:
                previous = current
    return increments


def _capacity_expression(
    x: Dict[Tuple[Aircraft, Route], pulp.LpVariable], route: Route
) -> pulp.LpAffineExpression:
    return pulp.lpSum(
        CAPACITY[(aircraft, route)] * x[(aircraft, route)]
        for aircraft in AIRCRAFT
        if (aircraft, route) in CAPACITY
    )


def _operating_cost_expression(
    x: Dict[Tuple[Aircraft, Route], pulp.LpVariable]
) -> pulp.LpAffineExpression:
    return pulp.lpSum(
        OPERATING_COST[(aircraft, route)] * x[(aircraft, route)]
        for aircraft, route in OPERATING_COST
    )


def solve_delta_formulation(
    solver: pulp.LpSolver | None = None,
) -> ModelResult:
    """Solve the incremental-demand formulation corresponding to GAMS alloc1."""

    model = pulp.LpProblem("aircraft_allocation_delta", pulp.LpMinimize)

    increments = incremental_demand()
    gamma = tail_probability()
    ed = expected_demand()

    x = {
        (aircraft, route): pulp.LpVariable(
            f"x_{aircraft}_{route}", lowBound=0, cat="Continuous"
        )
        for aircraft in AIRCRAFT
        for route in ROUTES
        if (aircraft, route) in CAPACITY
    }

    y = {
        (route, state): pulp.LpVariable(
            f"y_{route}_{state}",
            lowBound=0,
            upBound=increments[(route, state)],
            cat="Continuous",
        )
        for route in ROUTES
        for state in STATES
    }

    operating_cost = pulp.LpVariable("operating_cost", lowBound=0)
    bumping_cost = pulp.LpVariable("bumping_cost", lowBound=0)
    phi = pulp.LpVariable("phi")

    for aircraft in AIRCRAFT:
        model += (
            pulp.lpSum(
                x[(aircraft, route)]
                for route in ROUTES
                if (aircraft, route) in x
            )
            <= AVAILABILITY[aircraft],
            f"aircraft_balance_{aircraft}",
        )

    for route in ROUTES:
        model += (
            _capacity_expression(x, route)
            >= pulp.lpSum(
                increments[(route, state)] * y[(route, state)]
                for state in STATES
                if increments[(route, state)] != 0
            ),
            f"demand_balance_{route}",
        )

    model += (
        operating_cost == _operating_cost_expression(x),
        "operating_cost_definition",
    )

    model += (
        bumping_cost
        == pulp.lpSum(
            BUMPING_COST[route]
            * (
                ed[route]
                - pulp.lpSum(
                    gamma[(route, state)] * y[(route, state)]
                    for state in STATES
                )
            )
            for route in ROUTES
        ),
        "bumping_cost_definition_delta",
    )

    model += (phi == operating_cost + bumping_cost, "objective_definition")
    model += phi

    model.solve(solver)

    return ModelResult(
        status=pulp.LpStatus[model.status],
        objective=pulp.value(phi),
        operating_cost=pulp.value(operating_cost),
        bumping_cost=pulp.value(bumping_cost),
        aircraft_allocation={key: pulp.value(var) for key, var in x.items()},
        carried={key: pulp.value(var) for key, var in y.items()},
        bumped={},
    )


def solve_lambda_formulation(
    solver: pulp.LpSolver | None = None,
) -> ModelResult:
    """Solve the demand-state formulation corresponding to GAMS alloc2."""

    model = pulp.LpProblem("aircraft_allocation_lambda", pulp.LpMinimize)

    x = {
        (aircraft, route): pulp.LpVariable(
            f"x_{aircraft}_{route}", lowBound=0, cat="Continuous"
        )
        for aircraft in AIRCRAFT
        for route in ROUTES
        if (aircraft, route) in CAPACITY
    }

    y = {
        (route, state): pulp.LpVariable(
            f"y_{route}_{state}", lowBound=0, cat="Continuous"
        )
        for route in ROUTES
        for state in STATES
    }

    bumped = {
        (route, state): pulp.LpVariable(
            f"b_{route}_{state}", lowBound=0, cat="Continuous"
        )
        for route in ROUTES
        for state in STATES
    }

    operating_cost = pulp.LpVariable("operating_cost", lowBound=0)
    bumping_cost = pulp.LpVariable("bumping_cost", lowBound=0)
    phi = pulp.LpVariable("phi")

    for aircraft in AIRCRAFT:
        model += (
            pulp.lpSum(
                x[(aircraft, route)]
                for route in ROUTES
                if (aircraft, route) in x
            )
            <= AVAILABILITY[aircraft],
            f"aircraft_balance_{aircraft}",
        )

    for route in ROUTES:
        capacity = _capacity_expression(x, route)
        for state in STATES:
            model += (
                y[(route, state)] <= capacity,
                f"carried_definition_{route}_{state}",
            )
            model += (
                bumped[(route, state)]
                == DEMAND.get((route, state), 0.0) - y[(route, state)],
                f"bumped_definition_{route}_{state}",
            )

    model += (
        operating_cost == _operating_cost_expression(x),
        "operating_cost_definition",
    )

    model += (
        bumping_cost
        == pulp.lpSum(
            BUMPING_COST[route]
            * PROBABILITY.get((route, state), 0.0)
            * bumped[(route, state)]
            for route in ROUTES
            for state in STATES
        ),
        "bumping_cost_definition_lambda",
    )

    model += (phi == operating_cost + bumping_cost, "objective_definition")
    model += phi

    model.solve(solver)

    return ModelResult(
        status=pulp.LpStatus[model.status],
        objective=pulp.value(phi),
        operating_cost=pulp.value(operating_cost),
        bumping_cost=pulp.value(bumping_cost),
        aircraft_allocation={key: pulp.value(var) for key, var in x.items()},
        carried={key: pulp.value(var) for key, var in y.items()},
        bumped={key: pulp.value(var) for key, var in bumped.items()},
    )


def print_result(name: str, result: ModelResult) -> None:
    print(f"\n{name}")
    print("=" * len(name))
    print(f"Status: {result.status}")
    print(f"Objective value: {result.objective:.6f}")
    print(f"Operating cost: {result.operating_cost:.6f}")
    print(f"Expected bumping cost: {result.bumping_cost:.6f}")

    print("\nAircraft allocation")
    for (aircraft, route), value in sorted(result.aircraft_allocation.items()):
        if abs(value) > 1e-9:
            print(f"  x[{aircraft}, {route}] = {value:.6f}")

    print("\nCarried-passenger variables")
    for (route, state), value in sorted(result.carried.items()):
        if abs(value) > 1e-9:
            print(f"  y[{route}, {state}] = {value:.6f}")

    if result.bumped:
        print("\nBumped passengers")
        for (route, state), value in sorted(result.bumped.items()):
            if abs(value) > 1e-9:
                print(f"  b[{route}, {state}] = {value:.6f}")


if __name__ == "__main__":
    delta_result = solve_delta_formulation()
    lambda_result = solve_lambda_formulation()

    print_result("Delta formulation", delta_result)
    print_result("Lambda formulation", lambda_result)
