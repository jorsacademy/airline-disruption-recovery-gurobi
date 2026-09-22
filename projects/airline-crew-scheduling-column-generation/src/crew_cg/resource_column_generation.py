from __future__ import annotations

from .master import solve_master
from .model import Pairing
from .resource_pricing import CrewRules, price_pairing_resource_rcsp


def _singleton_pairings(flights, rules: CrewRules) -> list[Pairing]:
    pairings = []
    for flight in flights:
        block = flight.arrival - flight.departure
        if block > rules.max_block:
            continue
        penalty = 40.0 if flight.origin != flight.destination else 0.0
        duty = block
        cost = 80.0 + 0.35 * duty + 8.0 + penalty
        pairings.append(Pairing((flight.flight_id,), cost))
    return pairings


def run_resource_column_generation(
    flights,
    *,
    rules: CrewRules | None = None,
    tolerance: float = 1e-8,
    max_iterations: int = 100,
):
    rules = rules or CrewRules(require_base_return=False)
    active = _singleton_pairings(flights, rules)
    history = []
    for iteration in range(max_iterations):
        master = solve_master(flights, active)
        reduced_cost, pairing = price_pairing_resource_rcsp(
            flights,
            master["duals"],
            existing=active,
            rules=rules,
        )
        history.append(
            {
                "iteration": iteration,
                "objective": master["objective"],
                "columns": len(active),
                "best_reduced_cost": float(reduced_cost),
            }
        )
        if pairing is None or reduced_cost >= -tolerance:
            return master, active, history
        active.append(pairing)
    raise RuntimeError("resource column generation did not converge")
