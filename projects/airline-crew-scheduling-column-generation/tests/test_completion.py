import numpy as np

from crew_cg.branch_price_lite import branch_and_price_lite
from crew_cg.integer_master import solve_integer_master
from crew_cg.model import toy_flights
from crew_cg.pairing import enumerate_pairings
from crew_cg.resource_pricing import CrewRules, price_pairing_resource_rcsp


def test_resource_pricing_respects_base_return_and_block_limit():
    flights = toy_flights()
    duals = np.full(len(flights), 200.0)
    rules = CrewRules(base="IST", max_block=180, max_sit=180, require_base_return=True)
    reduced, pairing = price_pairing_resource_rcsp(flights, duals, rules=rules)
    assert reduced < 0.0
    assert pairing is not None
    by_id = {flight.flight_id: flight for flight in flights}
    assert by_id[pairing.flight_ids[0]].origin == "IST"
    assert by_id[pairing.flight_ids[-1]].destination == "IST"
    block = sum(by_id[i].arrival - by_id[i].departure for i in pairing.flight_ids)
    assert block <= rules.max_block


def test_branch_and_price_lite_matches_full_integer_reference_on_toy():
    flights = toy_flights()
    full = enumerate_pairings(flights)
    reference = solve_integer_master(flights, full)
    result = branch_and_price_lite(
        flights,
        rules=CrewRules(require_base_return=False),
        max_nodes=30,
    )
    assert abs(result["objective"] - reference["objective"]) < 1e-7
    covered = {flight_id for pairing in result["selected"] for flight_id in pairing.flight_ids}
    assert covered == {flight.flight_id for flight in flights}
    assert result["nodes_explored"] >= 1
