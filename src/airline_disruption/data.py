from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Flight:
    flight_id: str
    origin: str
    destination: str
    departure: int
    arrival: int
    revenue: float
    passengers: int


@dataclass(frozen=True)
class Aircraft:
    aircraft_id: str
    start_airport: str


def hhmm_to_minutes(value: int) -> int:
    """Convert HHMM integer notation to minutes after midnight."""
    hours, minutes = divmod(value, 100)
    if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
        raise ValueError(f"Invalid HHMM time: {value}")
    return hours * 60 + minutes


def normalize_interval(departure_hhmm: int, arrival_hhmm: int) -> tuple[int, int]:
    """Return departure/arrival minutes, rolling arrival into the next day when needed."""
    departure = hhmm_to_minutes(departure_hhmm)
    arrival = hhmm_to_minutes(arrival_hhmm)
    if arrival < departure:
        arrival += 24 * 60
    return departure, arrival


def create_sample_data() -> tuple[list[Aircraft], list[str], list[Flight]]:
    airports = ["JFK", "LAX", "ORD", "DFW", "ATL", "MIA"]
    aircraft = [
        Aircraft("AC001", "JFK"),
        Aircraft("AC002", "LAX"),
        Aircraft("AC003", "ORD"),
        Aircraft("AC004", "DFW"),
        Aircraft("AC005", "ATL"),
    ]

    raw = [
        ("FL001", "JFK", "LAX", 800, 1100),
        ("FL002", "LAX", "ORD", 1200, 1700),
        ("FL003", "ORD", "DFW", 900, 1100),
        ("FL004", "DFW", "ATL", 1300, 1500),
        ("FL005", "ATL", "MIA", 1600, 1800),
        ("FL006", "MIA", "JFK", 1900, 2200),
        ("FL007", "JFK", "ORD", 700, 1000),
        ("FL008", "ORD", "LAX", 1100, 1400),
        ("FL009", "LAX", "DFW", 1500, 1800),
        ("FL010", "DFW", "MIA", 1900, 2200),
        ("FL011", "MIA", "ATL", 600, 800),
        ("FL012", "ATL", "JFK", 900, 1200),
        ("FL013", "JFK", "DFW", 1300, 1600),
        ("FL014", "DFW", "LAX", 1700, 2000),
        ("FL015", "LAX", "ATL", 2100, 200),
    ]

    # Deterministic demonstration data.
    revenues = [64592, 187498, 145026, 71960, 152611, 170394, 137337, 137498, 94131, 171221, 123742, 65311, 69325, 114858, 138692]
    passengers = [179, 151, 210, 229, 117, 181, 271, 268, 137, 109, 283, 207, 144, 192, 141]

    flights: list[Flight] = []
    for index, (flight_id, origin, destination, dep_hhmm, arr_hhmm) in enumerate(raw):
        departure, arrival = normalize_interval(dep_hhmm, arr_hhmm)
        flights.append(
            Flight(
                flight_id=flight_id,
                origin=origin,
                destination=destination,
                departure=departure,
                arrival=arrival,
                revenue=float(revenues[index]),
                passengers=passengers[index],
            )
        )
    return aircraft, airports, flights
