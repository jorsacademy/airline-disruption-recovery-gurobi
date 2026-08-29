from __future__ import annotations

from collections import defaultdict

from .data import Aircraft, Flight

Arc = tuple[str, str]


def build_aircraft_networks(
    aircraft: list[Aircraft],
    flights: list[Flight],
    turnaround_minutes: int = 60,
) -> dict[str, list[Arc]]:
    """Build feasible source/flight/sink arcs for a single operational horizon."""
    if turnaround_minutes < 0:
        raise ValueError("turnaround_minutes must be non-negative")

    networks: dict[str, list[Arc]] = {}
    flights_by_origin: dict[str, list[Flight]] = defaultdict(list)
    for flight in flights:
        flights_by_origin[flight.origin].append(flight)

    for ac in aircraft:
        source = f"source_{ac.aircraft_id}"
        sink = f"sink_{ac.aircraft_id}"
        arcs: list[Arc] = [(source, sink)]

        for flight in flights_by_origin.get(ac.start_airport, []):
            arcs.append((source, flight.flight_id))

        for first in flights:
            for second in flights:
                if first.flight_id == second.flight_id:
                    continue
                if first.destination != second.origin:
                    continue
                if second.departure >= first.arrival + turnaround_minutes:
                    arcs.append((first.flight_id, second.flight_id))

        for flight in flights:
            arcs.append((flight.flight_id, sink))

        networks[ac.aircraft_id] = arcs

    return networks


def adjacency(arcs: list[Arc]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, list[str]] = defaultdict(list)
    for start, end in arcs:
        outgoing[start].append(end)
        incoming[end].append(start)
    return dict(outgoing), dict(incoming)
