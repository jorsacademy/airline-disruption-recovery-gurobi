from __future__ import annotations

from .model import Flight


def hub_timetable(
    waves: int = 3,
    destinations: tuple[str, ...] = ("ADB", "ESB", "AYT"),
    hub: str = "IST",
) -> list[Flight]:
    """Generate a deterministic hub-and-spoke timetable with connectable duties."""
    flights: list[Flight] = []
    flight_id = 0
    for wave in range(waves):
        outbound_base = 60 + wave * 240
        for offset, destination in enumerate(destinations):
            departure = outbound_base + offset * 15
            arrival = departure + 60
            flights.append(Flight(flight_id, hub, destination, departure, arrival))
            flight_id += 1

            return_departure = arrival + 60
            return_arrival = return_departure + 60
            flights.append(
                Flight(flight_id, destination, hub, return_departure, return_arrival)
            )
            flight_id += 1
    return sorted(flights, key=lambda flight: flight.flight_id)
