from __future__ import annotations

from dataclasses import dataclass
from math import inf

from .model import Flight, Pairing


@dataclass(frozen=True)
class Label:
    flight_ids: tuple[int, ...]
    first_origin: str
    start_departure: int
    last_destination: str
    last_arrival: int
    reduced_cost_without_open_penalty: float


def _partial_reduced_cost(
    flight_ids: tuple[int, ...],
    by_id: dict[int, Flight],
    duals,
) -> float:
    first = by_id[flight_ids[0]]
    last = by_id[flight_ids[-1]]
    duty = last.arrival - first.departure
    pairing_cost_without_open = 80.0 + 0.35 * duty + 8.0 * len(flight_ids)
    return pairing_cost_without_open - sum(float(duals[i]) for i in flight_ids)


def price_pairing_label_setting(
    flights: list[Flight],
    duals,
    existing: list[Pairing] | None = None,
    min_connection: int = 30,
    max_duty: int = 600,
    max_legs: int = 4,
) -> tuple[float, Pairing | None]:
    """Find a negative-reduced-cost pairing with an acyclic label-setting algorithm.

    Flights are naturally time ordered, so the connection graph is acyclic. Labels are
    extended only forward in time. Dominance is exact for labels sharing the same
    first departure/origin and last flight because all future incremental costs are identical.
    """
    by_id = {flight.flight_id: flight for flight in flights}
    ordered = sorted(flights, key=lambda flight: (flight.departure, flight.flight_id))
    existing_keys = {pairing.flight_ids for pairing in existing or []}

    labels_by_last: dict[int, list[Label]] = {}
    all_labels: list[Label] = []
    for flight in ordered:
        ids = (flight.flight_id,)
        label = Label(
            ids,
            flight.origin,
            flight.departure,
            flight.destination,
            flight.arrival,
            _partial_reduced_cost(ids, by_id, duals),
        )
        labels_by_last.setdefault(flight.flight_id, []).append(label)
        all_labels.append(label)

    for flight in ordered:
        current_labels = list(labels_by_last.get(flight.flight_id, []))
        for label in current_labels:
            if len(label.flight_ids) >= max_legs:
                continue
            for nxt in ordered:
                if nxt.departure <= flight.departure:
                    continue
                if label.last_destination != nxt.origin:
                    continue
                if nxt.departure - label.last_arrival < min_connection:
                    continue
                if nxt.arrival - label.start_departure > max_duty:
                    continue

                ids = label.flight_ids + (nxt.flight_id,)
                candidate = Label(
                    ids,
                    label.first_origin,
                    label.start_departure,
                    nxt.destination,
                    nxt.arrival,
                    _partial_reduced_cost(ids, by_id, duals),
                )
                bucket = labels_by_last.setdefault(nxt.flight_id, [])
                signature = (candidate.first_origin, candidate.start_departure, candidate.flight_ids[-1])
                dominated = False
                survivors: list[Label] = []
                for incumbent in bucket:
                    incumbent_signature = (
                        incumbent.first_origin,
                        incumbent.start_departure,
                        incumbent.flight_ids[-1],
                    )
                    if incumbent_signature == signature:
                        if incumbent.reduced_cost_without_open_penalty <= candidate.reduced_cost_without_open_penalty:
                            dominated = True
                            break
                        continue
                    survivors.append(incumbent)
                if dominated:
                    continue
                survivors.append(candidate)
                labels_by_last[nxt.flight_id] = survivors
                all_labels.append(candidate)

    best_reduced_cost = inf
    best_pairing: Pairing | None = None
    for label in all_labels:
        if label.flight_ids in existing_keys:
            continue
        first = by_id[label.flight_ids[0]]
        last = by_id[label.flight_ids[-1]]
        open_penalty = 40.0 if first.origin != last.destination else 0.0
        reduced_cost = label.reduced_cost_without_open_penalty + open_penalty
        if reduced_cost < best_reduced_cost:
            duty = last.arrival - first.departure
            cost = 80.0 + 0.35 * duty + 8.0 * len(label.flight_ids) + open_penalty
            best_reduced_cost = reduced_cost
            best_pairing = Pairing(label.flight_ids, cost)

    return best_reduced_cost, best_pairing
