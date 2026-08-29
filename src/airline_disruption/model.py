from __future__ import annotations

from dataclasses import dataclass

import gurobipy as gp
from gurobipy import GRB

from .data import Aircraft, Flight
from .network import adjacency, build_aircraft_networks


@dataclass(frozen=True)
class RecoveryResult:
    alpha: float
    loss: float
    operated_flights: dict[str, list[str]]
    operated_flight_count: int
    transported_passengers: int
    utilized_aircraft: int


def build_model(
    alpha: float,
    aircraft: list[Aircraft],
    airports: list[str],
    flights: list[Flight],
    turnaround_minutes: int = 60,
    verbose: bool = False,
) -> tuple[gp.Model, dict[tuple[str, str], gp.Var], dict[tuple[str, str, str], gp.Var]]:
    """Build the disruption-recovery MILP without solving it."""
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be between 0 and 1")

    networks = build_aircraft_networks(aircraft, flights, turnaround_minutes)

    model = gp.Model("airline_disruption_recovery")
    model.Params.OutputFlag = 1 if verbose else 0

    x: dict[tuple[str, str], gp.Var] = {}
    y: dict[tuple[str, str, str], gp.Var] = {}

    for ac in aircraft:
        for flight in flights:
            x[ac.aircraft_id, flight.flight_id] = model.addVar(
                vtype=GRB.BINARY,
                name=f"x[{ac.aircraft_id},{flight.flight_id}]",
            )
        for start, end in networks[ac.aircraft_id]:
            y[ac.aircraft_id, start, end] = model.addVar(
                vtype=GRB.BINARY,
                name=f"y[{ac.aircraft_id},{start},{end}]",
            )

    model.setObjective(
        gp.quicksum(
            flight.revenue
            * (1 - gp.quicksum(x[ac.aircraft_id, flight.flight_id] for ac in aircraft))
            for flight in flights
        ),
        GRB.MINIMIZE,
    )

    for flight in flights:
        model.addConstr(
            gp.quicksum(x[ac.aircraft_id, flight.flight_id] for ac in aircraft) <= 1,
            name=f"unique[{flight.flight_id}]",
        )

    for ac in aircraft:
        ac_id = ac.aircraft_id
        source = f"source_{ac_id}"
        sink = f"sink_{ac_id}"
        outgoing, incoming = adjacency(networks[ac_id])

        model.addConstr(
            gp.quicksum(y[ac_id, source, node] for node in outgoing[source]) == 1,
            name=f"source_flow[{ac_id}]",
        )
        model.addConstr(
            gp.quicksum(y[ac_id, node, sink] for node in incoming[sink]) == 1,
            name=f"sink_flow[{ac_id}]",
        )

        for flight in flights:
            f_id = flight.flight_id
            inflow = gp.quicksum(y[ac_id, node, f_id] for node in incoming.get(f_id, []))
            outflow = gp.quicksum(y[ac_id, f_id, node] for node in outgoing.get(f_id, []))
            model.addConstr(inflow == x[ac_id, f_id], name=f"in_link[{ac_id},{f_id}]")
            model.addConstr(outflow == x[ac_id, f_id], name=f"out_link[{ac_id},{f_id}]")

    for airport in airports:
        departing = [f.flight_id for f in flights if f.origin == airport]
        arriving = [f.flight_id for f in flights if f.destination == airport]
        if departing:
            model.addConstr(
                gp.quicksum(x[ac.aircraft_id, f_id] for ac in aircraft for f_id in departing)
                <= alpha * len(departing),
                name=f"departure_capacity[{airport}]",
            )
        if arriving:
            model.addConstr(
                gp.quicksum(x[ac.aircraft_id, f_id] for ac in aircraft for f_id in arriving)
                <= alpha * len(arriving),
                name=f"arrival_capacity[{airport}]",
            )

    model.update()
    return model, x, y


def solve_flight_planning(
    alpha: float,
    aircraft: list[Aircraft],
    airports: list[str],
    flights: list[Flight],
    turnaround_minutes: int = 60,
    verbose: bool = False,
) -> RecoveryResult:
    model, x, _ = build_model(
        alpha,
        aircraft,
        airports,
        flights,
        turnaround_minutes=turnaround_minutes,
        verbose=verbose,
    )
    model.optimize()
    if model.Status != GRB.OPTIMAL:
        raise RuntimeError(f"Optimization did not reach optimality; status={model.Status}")

    operated: dict[str, list[str]] = {}
    flight_by_id = {flight.flight_id: flight for flight in flights}
    for ac in aircraft:
        ac_id = ac.aircraft_id
        operated[ac_id] = [
            flight.flight_id
            for flight in flights
            if x[ac_id, flight.flight_id].X > 0.5
        ]

    operated_ids = [f_id for assigned in operated.values() for f_id in assigned]
    return RecoveryResult(
        alpha=alpha,
        loss=float(model.ObjVal),
        operated_flights=operated,
        operated_flight_count=len(operated_ids),
        transported_passengers=sum(flight_by_id[f_id].passengers for f_id in operated_ids),
        utilized_aircraft=sum(bool(assigned) for assigned in operated.values()),
    )
