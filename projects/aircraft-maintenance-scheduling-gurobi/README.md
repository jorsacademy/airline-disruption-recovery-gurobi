# Aircraft Maintenance Scheduling with Gurobi

A mixed-integer linear programming (MILP) example for scheduling aircraft maintenance while preserving operational readiness.

The model assigns one maintenance start time to each aircraft and enforces technician capacity, maximum concurrent maintenance, total fleet readiness, and squadron-level readiness. It uses lexicographic optimization: first minimize total makespan, then prefer earlier starts for higher-priority aircraft.

## Model overview

- 12 aircraft across 3 squadrons
- 7-day / 168-hour planning horizon
- 8-hour scheduling blocks
- 3 maintenance types
  - Phase I: 8 hours, 2 technicians
  - Phase II: 24 hours, 4 technicians
  - Phase III: 48 hours, 6 technicians
- 30 technicians available
- Maximum 8 simultaneous maintenance operations
- Minimum 8 aircraft ready fleet-wide
- Minimum 2 aircraft ready per squadron

Priority values use the convention `smaller number = higher priority`.

## Optimization objectives

The model uses Gurobi multi-objective optimization:

1. Minimize makespan.
2. Among equivalent makespan solutions, minimize priority-weighted start delay so higher-priority aircraft tend to be scheduled earlier.

This avoids mixing the two goals with an arbitrary single weighted objective.

## Implementation notes

The formulation creates binary variables only for feasible aircraft/start-time combinations. Maintenance activity at each time block is derived directly from those start decisions, so no separate maintenance-state binary variable is required.

The code also includes:

- input validation
- post-solve schedule validation
- infeasibility diagnosis through Gurobi IIS output
- schedule reporting with pandas
- a Gantt-style visualization with matplotlib

## Installation

Python 3.10+ is recommended.

```bash
pip install -r requirements.txt
```

Gurobi requires a valid license. See the official Gurobi documentation for license setup.

## Run

```bash
python aircraft_maintenance_optimizer.py
```

If the model is feasible, the script prints the optimized schedule, maintenance breakdown, squadron workload, and displays a schedule chart.

If the model is infeasible, an IIS file named `aircraft_maintenance_iis.ilp` is written for diagnosis.

## Important note on results

This repository intentionally does not hard-code legacy claims such as a specific objective value or completion time. Solver results should be generated from the current formulation and the installed Gurobi version/license environment. `GRB.OPTIMAL` should be interpreted according to the configured solver tolerances.

## Why this version differs from the original prototype

The original prototype used redundant maintenance-state variables, a relatively loose MIP gap, and a priority term whose coefficient direction conflicted with the stated priority convention. This version simplifies the formulation and aligns the secondary objective with the intended priority semantics.

## Files

- `aircraft_maintenance_optimizer.py` — MILP model, solver workflow, validation, reporting, and visualization
- `requirements.txt` — Python dependencies
- `.gitignore` — common Python/Gurobi-generated files

## Disclaimer

This is an educational operations-research example using synthetic aircraft and maintenance data. It is not an operational military maintenance system and should not be treated as production deployment guidance.
