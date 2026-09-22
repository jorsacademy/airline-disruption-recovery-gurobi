from crew_cg.column_generation_rcsp import run_column_generation_rcsp
from crew_cg.master import solve_master
from crew_cg.model import toy_flights
from crew_cg.pairing import enumerate_pairings, price_pairings
from crew_cg.pricing_rcsp import price_pairing_label_setting


def test_label_setting_matches_exhaustive_best_reduced_cost():
    flights = toy_flights()
    all_pairings = enumerate_pairings(flights)
    active = [pairing for pairing in all_pairings if len(pairing.flight_ids) == 1]
    master = solve_master(flights, active)

    exhaustive_cost, _ = price_pairings(all_pairings, master["duals"], active)
    rcsp_cost, _ = price_pairing_label_setting(flights, master["duals"], existing=active)
    assert abs(exhaustive_cost - rcsp_cost) < 1e-8


def test_rcsp_column_generation_matches_full_lp():
    flights = toy_flights()
    full = solve_master(flights, enumerate_pairings(flights))
    master, active, history = run_column_generation_rcsp(flights)
    assert abs(full["objective"] - master["objective"]) < 1e-7
    assert len(active) <= len(enumerate_pairings(flights))
    assert history[-1]["best_reduced_cost"] >= -1e-8
