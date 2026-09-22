from .master import solve_master
from .pairing import enumerate_pairings, price_pairings


def run_column_generation(flights, tolerance=1e-8, max_iterations=100):
    all_pairings = enumerate_pairings(flights)
    # Single-flight duties provide an initial feasible restricted master.
    active = [p for p in all_pairings if len(p.flight_ids) == 1]
    history = []

    for iteration in range(max_iterations):
        master = solve_master(flights, active)
        reduced_cost, pairing = price_pairings(all_pairings, master["duals"], active)
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
