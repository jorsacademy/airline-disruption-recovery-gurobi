# Aircraft Allocation Under Uncertain Demand

This repository contains a Python/PuLP implementation of the classic aircraft allocation problem under uncertain passenger demand.

The model allocates available aircraft types to routes while minimizing the sum of operating cost and expected passenger bumping cost. Demand is represented through discrete demand states with route-specific probabilities.

Two linear-programming formulations are implemented:

1. **Delta formulation** — uses incremental demand variables together with tail probabilities.
2. **Lambda formulation** — uses explicit carried-passenger and bumped-passenger variables for each demand state.

The implementation is based on the aircraft allocation example discussed by George B. Dantzig in *Linear Programming and Extensions* and mirrors the structure of the corresponding GAMS model.

## Model structure

Aircraft types are indexed by `a`, `b`, `c`, and `d`. Five routes and up to five demand states are represented. Each aircraft-route combination has an operating cost and passenger capacity, while each aircraft type has limited availability.

The optimization objective is

```text
minimize operating cost + expected bumping cost
```

Aircraft allocation variables are continuous because the source GAMS model is solved as an LP rather than a MIP.

## Delta formulation

The delta formulation represents route demand as cumulative increments. For each route, demand increments are computed from consecutive demand levels. The associated tail probability is the probability that realized demand reaches or exceeds a given increment.

The carried-demand variables are bounded by their corresponding demand increments, matching the original GAMS statement:

```text
y.up(j,h) = deltb(j,h)
```

The expected bumping cost is then calculated from expected demand minus the expected amount of demand served across the incremental states.

## Lambda formulation

The lambda formulation works directly with each route-demand state. For each state, the model defines carried passengers and bumped passengers through

```text
bumped passengers = demand - carried passengers
```

Expected bumping cost is the probability-weighted sum of bumped passengers across all route-demand states.

## Installation

Python 3.10 or newer is recommended.

```bash
pip install -r requirements.txt
```

PuLP includes support for the CBC solver in many standard installations. If CBC is not available in your environment, configure another solver supported by PuLP.

## Usage

Run both formulations with:

```bash
python aircraft_allocation.py
```

The script prints:

- solver status,
- objective value,
- operating cost,
- expected bumping cost,
- nonzero aircraft allocation variables,
- carried-passenger variables,
- bumped-passenger variables for the lambda formulation.

The two formulations can also be imported independently:

```python
from aircraft_allocation import solve_delta_formulation, solve_lambda_formulation

result_delta = solve_delta_formulation()
result_lambda = solve_lambda_formulation()
```

Each solver function returns a `ModelResult` dataclass containing the optimization results.

## Notes on the translation

The Python implementation intentionally preserves several details of the source GAMS model:

- missing table entries are interpreted as zero,
- aircraft allocation variables remain continuous,
- the delta model contains only the aircraft-balance, demand-balance, operating-cost, delta bumping-cost, and objective equations,
- the lambda model contains only the aircraft-balance, carried-passenger, bumped-passenger, operating-cost, lambda bumping-cost, and objective equations,
- the two formulations are built as independent PuLP models and do not share decision-variable objects.

These details are important because superficially similar translations can change the feasible region and therefore no longer represent the original model.

## Reference

Dantzig, G. B. (1963). *Linear Programming and Extensions*. Princeton University Press. Chapter 28.

## License

This project is provided under a custom non-commercial license. Personal, academic, educational, and non-commercial research use are permitted subject to the terms in `LICENSE.md`.

Commercial use is not permitted without prior explicit written permission from the copyright holder.
