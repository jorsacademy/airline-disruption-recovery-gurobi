from __future__ import annotations

from .master import solve_master
from .pairing import enumerate_pairings
from .pricing_rcsp import price_pairing_label_setting


def run_column_generation_rcsp(
    flights,
    tolerance: float = 1e-8,
    max_iterations: int = 100,
    min_connection: int = 30,
    max_duty: int = 600,
    max_legs: int = 4,
):
    """Run Dantzig-Wolfe column generation with label-setting pricing."""
    active = [
        pairing
        for pairing in enumerate_pairings(flights, max_legs=1)
        if len(pairing.flight_ids) == 1
    ]
    history = []

    for iteration in range(max_iterations):
        master = solve_master(flights, active)
        reduced_cost, pairing = price_pairing_label_setting(
            flights,
            master["duals"],
            existing=active,
            min_connection=min_connection,
            max_duty=max_duty,
            max_legs=max_legs,
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

    raise RuntimeError("column generation reached max_iterations without convergence")
