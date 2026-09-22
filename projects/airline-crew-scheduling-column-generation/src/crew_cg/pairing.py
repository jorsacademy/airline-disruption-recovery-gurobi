from itertools import combinations, pairwise

from .model import Pairing


def is_legal(sequence, by_id, min_connection=30, max_duty=600):
    flights = [by_id[i] for i in sequence]
    for a, b in pairwise(flights):
        if a.destination != b.origin or b.departure - a.arrival < min_connection:
            return False
    return flights[-1].arrival - flights[0].departure <= max_duty


def pairing_cost(sequence, by_id):
    flights = [by_id[i] for i in sequence]
    duty = flights[-1].arrival - flights[0].departure
    # Fixed crew activation + duty-time + open-duty penalty.
    open_penalty = 40.0 if flights[0].origin != flights[-1].destination else 0.0
    return 80.0 + 0.35 * duty + 8.0 * len(flights) + open_penalty


def enumerate_pairings(flights, max_legs=4):
    by_id = {f.flight_id: f for f in flights}
    ids = [f.flight_id for f in sorted(flights, key=lambda x: x.departure)]
    pairings = []
    for r in range(1, min(max_legs, len(ids)) + 1):
        for seq in combinations(ids, r):
            ordered = tuple(sorted(seq, key=lambda i: by_id[i].departure))
            if is_legal(ordered, by_id):
                pairings.append(Pairing(ordered, pairing_cost(ordered, by_id)))
    return pairings


def price_pairings(pairings, duals, existing):
    existing_keys = {p.flight_ids for p in existing}
    candidates = []
    for pairing in pairings:
        if pairing.flight_ids in existing_keys:
            continue
        reduced_cost = pairing.cost - sum(duals[i] for i in pairing.flight_ids)
        candidates.append((reduced_cost, pairing))
    return min(candidates, default=(float("inf"), None), key=lambda x: x[0])
