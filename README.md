# Airline Disruption Recovery with Gurobi

A mixed-integer optimization model for airline disruption recovery using aircraft-flow networks and airport-capacity degradation scenarios.

The model assigns flights to aircraft, enforces feasible aircraft rotations, handles overnight flights, permits aircraft to remain idle, and evaluates disruption levels through an airport-capacity factor `alpha` in `[0, 1]`.

## Model highlights

- Binary flight-operation decisions with at-most-one-aircraft assignment.
- Aircraft-specific source/sink flow networks.
- Location and turnaround-time-compatible flight connections.
- Explicit idle arcs so aircraft are not forced to operate.
- Minute-based time normalization, including next-day arrivals.
- Revenue-loss minimization without double-counting cancelled-flight revenue.
- Airport departure and arrival capacity constraints controlled by `alpha`.

## Installation

```bash
python -m pip install -e .
```

A working Gurobi installation and license are required to solve optimization instances. The structural unit tests do not require an active solver license.

## Run

```bash
python -m airline_disruption.cli
```

## Tests

```bash
pytest
```

To run the solver integration test when a Gurobi license is available:

```bash
RUN_GUROBI_INTEGRATION=1 pytest -m integration
```

## License

This repository is source-available for noncommercial purposes only under the PolyForm Noncommercial License 1.0.0. Commercial use is prohibited. See `LICENSE` for the full terms.
