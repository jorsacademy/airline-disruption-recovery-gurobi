import pytest

from airline_disruption.data import create_sample_data, hhmm_to_minutes, normalize_interval


def test_hhmm_to_minutes() -> None:
    assert hhmm_to_minutes(0) == 0
    assert hhmm_to_minutes(730) == 450
    assert hhmm_to_minutes(2359) == 1439


def test_hhmm_validation() -> None:
    with pytest.raises(ValueError):
        hhmm_to_minutes(1260)


def test_overnight_interval_rolls_arrival_forward() -> None:
    departure, arrival = normalize_interval(2100, 200)
    assert departure == 21 * 60
    assert arrival == 26 * 60


def test_sample_data_is_deterministic() -> None:
    aircraft, airports, flights = create_sample_data()
    assert len(aircraft) == 5
    assert len(airports) == 6
    assert len(flights) == 15
    assert flights[-1].flight_id == "FL015"
    assert flights[-1].arrival > flights[-1].departure
