from __future__ import annotations

from dataclasses import dataclass
from math import inf

from .model import Flight, Pairing


@dataclass(frozen=True)
class CrewRules:
    base: str = "IST"
    min_connection: int = 30
    max_duty: int = 600
    max_block: int = 300
    max_sit: int = 240
    max_legs: int = 4
    require_base_return: bool = True


@dataclass(frozen=True)
class ResourceLabel:
    flight_ids: tuple[int, ...]
    start_origin: str
    start_departure: int
    last_destination: str
    last_arrival: int
    block_time: int
    sit_time: int
    reduced_cost: float


def pairing_cost(flight_ids: tuple[int, ...], by_id: dict[int, Flight]) -> float:
    first = by_id[flight_ids[0]]
    last = by_id[flight_ids[-1]]
    duty = last.arrival - first.departure
    open_penalty = 40.0 if first.origin != last.destination else 0.0
    return 80.0 + 0.35 * duty + 8.0 * len(flight_ids) + open_penalty


def _reduced_cost(ids: tuple[int, ...], by_id: dict[int, Flight], duals) -> float:
    return pairing_cost(ids, by_id) - sum(float(duals[i]) for i in ids)


def _same_future_state(a: ResourceLabel, b: ResourceLabel) -> bool:
    return (
        a.start_origin == b.start_origin
        and a.start_departure == b.start_departure
        and a.last_destination == b.last_destination
        and a.last_arrival == b.last_arrival
    )


def price_pairing_resource_rcsp(
    flights: list[Flight],
    duals,
    *,
    existing: list[Pairing] | None = None,
    forbidden: set[tuple[int, ...]] | None = None,
    rules: CrewRules | None = None,
) -> tuple[float, Pairing | None]:
    """Price a legal pairing with explicit duty, block, sit and base resources."""
    rules = rules or CrewRules()
    by_id = {flight.flight_id: flight for flight in flights}
    ordered = sorted(flights, key=lambda flight: (flight.departure, flight.flight_id))
    excluded = {pairing.flight_ids for pairing in existing or []} | (forbidden or set())

    labels_by_last: dict[int, list[ResourceLabel]] = {}
    all_labels: list[ResourceLabel] = []
    for flight in ordered:
        if rules.require_base_return and flight.origin != rules.base:
            continue
        block = flight.arrival - flight.departure
        if block > rules.max_block:
            continue
        ids = (flight.flight_id,)
        label = ResourceLabel(
            ids,
            flight.origin,
            flight.departure,
            flight.destination,
            flight.arrival,
            block,
            0,
            _reduced_cost(ids, by_id, duals),
        )
        labels_by_last.setdefault(flight.flight_id, []).append(label)
        all_labels.append(label)

    for flight in ordered:
        for label in list(labels_by_last.get(flight.flight_id, [])):
            if len(label.flight_ids) >= rules.max_legs:
                continue
            for nxt in ordered:
                if nxt.departure <= label.last_arrival:
                    continue
                if nxt.origin != label.last_destination:
                    continue
                sit = nxt.departure - label.last_arrival
                if sit < rules.min_connection or sit > rules.max_sit:
                    continue
                duty = nxt.arrival - label.start_departure
                block = label.block_time + (nxt.arrival - nxt.departure)
                if duty > rules.max_duty or block > rules.max_block:
                    continue
                ids = label.flight_ids + (nxt.flight_id,)
                candidate = ResourceLabel(
                    ids,
                    label.start_origin,
                    label.start_departure,
                    nxt.destination,
                    nxt.arrival,
                    block,
                    label.sit_time + sit,
                    _reduced_cost(ids, by_id, duals),
                )
                bucket = labels_by_last.setdefault(nxt.flight_id, [])
                dominated = any(
                    _same_future_state(incumbent, candidate)
                    and incumbent.block_time <= candidate.block_time
                    and incumbent.sit_time <= candidate.sit_time
                    and incumbent.reduced_cost <= candidate.reduced_cost
                    for incumbent in bucket
                )
                if dominated:
                    continue
                bucket[:] = [
                    incumbent
                    for incumbent in bucket
                    if not (
                        _same_future_state(incumbent, candidate)
                        and candidate.block_time <= incumbent.block_time
                        and candidate.sit_time <= incumbent.sit_time
                        and candidate.reduced_cost <= incumbent.reduced_cost
                    )
                ]
                bucket.append(candidate)
                all_labels.append(candidate)

    best = inf
    best_pairing: Pairing | None = None
    for label in all_labels:
        if label.flight_ids in excluded:
            continue
        if rules.require_base_return and label.last_destination != rules.base:
            continue
        if label.reduced_cost < best:
            best = label.reduced_cost
            best_pairing = Pairing(label.flight_ids, pairing_cost(label.flight_ids, by_id))
    return best, best_pairing
