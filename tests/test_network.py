from airline_disruption.data import Aircraft, Flight
from airline_disruption.network import build_aircraft_networks


def test_idle_arc_is_present() -> None:
    aircraft = [Aircraft("A1", "JFK")]
    flights = [Flight("F1", "JFK", "LAX", 60, 120, 100.0, 10)]
    networks = build_aircraft_networks(aircraft, flights)
    assert ("source_A1", "sink_A1") in networks["A1"]


def test_source_respects_aircraft_start_airport() -> None:
    aircraft = [Aircraft("A1", "JFK")]
    flights = [
        Flight("F1", "JFK", "LAX", 60, 120, 100.0, 10),
        Flight("F2", "ORD", "LAX", 60, 120, 100.0, 10),
    ]
    networks = build_aircraft_networks(aircraft, flights)
    assert ("source_A1", "F1") in networks["A1"]
    assert ("source_A1", "F2") not in networks["A1"]


def test_connection_requires_matching_location() -> None:
    aircraft = [Aircraft("A1", "JFK")]
    flights = [
        Flight("F1", "JFK", "LAX", 60, 120, 100.0, 10),
        Flight("F2", "LAX", "ORD", 180, 240, 100.0, 10),
        Flight("F3", "DFW", "ORD", 180, 240, 100.0, 10),
    ]
    networks = build_aircraft_networks(aircraft, flights, turnaround_minutes=60)
    assert ("F1", "F2") in networks["A1"]
    assert ("F1", "F3") not in networks["A1"]
