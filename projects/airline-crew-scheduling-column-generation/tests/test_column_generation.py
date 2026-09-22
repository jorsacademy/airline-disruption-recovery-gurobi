from crew_cg.column_generation import run_column_generation
from crew_cg.master import solve_master
from crew_cg.model import toy_flights
from crew_cg.pairing import enumerate_pairings


def test_column_generation_matches_full_lp():
    flights = toy_flights()
    full = solve_master(flights, enumerate_pairings(flights))
    cg, active, history = run_column_generation(flights)
    assert abs(full["objective"] - cg["objective"]) < 1e-7
    assert len(active) <= len(enumerate_pairings(flights))
    assert history[-1]["best_reduced_cost"] >= -1e-8


def test_all_flights_covered_fractionally():
    flights = toy_flights()
    master, active, _ = run_column_generation(flights)
    for flight in flights:
        coverage = sum(
            x for x, pairing in zip(master["x"], active) if flight.flight_id in pairing.flight_ids
        )
        assert coverage >= 1.0 - 1e-8
