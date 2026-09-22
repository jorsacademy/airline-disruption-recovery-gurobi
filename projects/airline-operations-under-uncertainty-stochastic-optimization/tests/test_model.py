import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from model import default_instance, solve_stochastic_airline


def test_solution_is_feasible():
    flights, scenarios = default_instance()
    sol = solve_stochastic_airline(flights, scenarios)
    assert len(sol["planned"]) >= 5
    for sc in scenarios:
        result = sol["scenarios"][sc.name]
        assert len(result["operated"]) <= sc.max_operated_flights
        assert set(result["operated"]).isdisjoint(result["cancelled"])
        assert set(result["operated"]) | set(result["cancelled"]) == set(sol["planned"])


def test_objective_positive():
    flights, scenarios = default_instance()
    sol = solve_stochastic_airline(flights, scenarios)
    assert sol["objective"] > 0
