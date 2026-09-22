from dataclasses import dataclass


@dataclass(frozen=True)
class Flight:
    flight_id: int
    origin: str
    destination: str
    departure: int
    arrival: int


@dataclass(frozen=True)
class Pairing:
    flight_ids: tuple[int, ...]
    cost: float


def toy_flights():
    return [
        Flight(0, "IST", "ADB", 60, 120),
        Flight(1, "ADB", "IST", 180, 240),
        Flight(2, "IST", "ESB", 90, 150),
        Flight(3, "ESB", "IST", 210, 270),
        Flight(4, "IST", "AYT", 300, 360),
        Flight(5, "AYT", "IST", 420, 480),
    ]
