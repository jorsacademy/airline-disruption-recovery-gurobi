from __future__ import annotations

from .data import create_sample_data
from .model import solve_flight_planning


def main() -> None:
    aircraft, airports, flights = create_sample_data()
    print("Airline Disruption Recovery — Gurobi")
    print(f"Airports: {len(airports)} | Aircraft: {len(aircraft)} | Flights: {len(flights)}")

    for alpha in (0.0, 0.2, 0.5, 0.8, 1.0):
        result = solve_flight_planning(alpha, aircraft, airports, flights)
        print(
            f"alpha={alpha:.1f} | loss=${result.loss:,.0f} | "
            f"flights={result.operated_flight_count} | "
            f"passengers={result.transported_passengers} | "
            f"aircraft={result.utilized_aircraft}"
        )
        for aircraft_id, assigned in result.operated_flights.items():
            if assigned:
                print(f"  {aircraft_id}: {', '.join(assigned)}")


if __name__ == "__main__":
    main()
