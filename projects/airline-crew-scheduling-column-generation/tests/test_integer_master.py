from crew_cg.column_generation_rcsp import run_column_generation_rcsp
from crew_cg.integer_master import integrality_gap, solve_integer_master
from crew_cg.model import toy_flights


def test_integer_master_covers_all_flights():
    flights = toy_flights()
    lp, active, _ = run_column_generation_rcsp(flights)
    integer = solve_integer_master(flights, active)
    assert integer["objective"] + 1e-8 >= lp["objective"]
    assert integrality_gap(lp["objective"], integer["objective"]) >= -1e-10
    selected = integer["selected"]
    for flight in flights:
        assert any(flight.flight_id in pairing.flight_ids for pairing in selected)
