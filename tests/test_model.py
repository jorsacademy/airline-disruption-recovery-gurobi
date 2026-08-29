import os

import pytest

from airline_disruption.data import create_sample_data
from airline_disruption.model import build_model, solve_flight_planning


def test_alpha_validation_happens_before_solver_creation() -> None:
    aircraft, airports, flights = create_sample_data()
    with pytest.raises(ValueError, match="alpha"):
        build_model(-0.01, aircraft, airports, flights)
    with pytest.raises(ValueError, match="alpha"):
        build_model(1.01, aircraft, airports, flights)


@pytest.mark.integration
def test_full_capacity_solver_smoke_test() -> None:
    if os.getenv("RUN_GUROBI_INTEGRATION") != "1":
        pytest.skip("Set RUN_GUROBI_INTEGRATION=1 when an active Gurobi license is available")

    aircraft, airports, flights = create_sample_data()
    result = solve_flight_planning(1.0, aircraft, airports, flights)
    assert result.loss >= 0
    assert 0 <= result.operated_flight_count <= len(flights)
    assigned = [flight for rotation in result.operated_flights.values() for flight in rotation]
    assert len(assigned) == len(set(assigned))
