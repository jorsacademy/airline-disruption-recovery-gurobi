# Airline Operations Under Uncertainty: Stochastic Optimization

A compact Operations Research project for airline schedule planning under uncertain disruption scenarios. The model is implemented as a mixed-integer stochastic optimization problem in Python using `scipy.optimize.milp`.

## Problem

An airline chooses which flights to plan before operational uncertainty is known. After a disruption scenario is realized, each planned flight is either operated or cancelled. Weather-dependent capacity limits and delay penalties vary by scenario.

The model minimizes:

- first-stage planned operating cost,
- expected delay cost,
- expected cancellation cost.

## Uncertainty scenarios

The synthetic instance contains three scenarios:

- `clear` with probability 0.50,
- `moderate` disruption with probability 0.30,
- `severe` disruption with probability 0.20.

Each scenario has a maximum number of flights that can operate and scenario-specific delay minutes.

## Mathematical structure

First-stage binary variable:

- `x_f = 1` if flight `f` is included in the planned schedule.

Second-stage binary variables for each scenario `s`:

- `y_fs = 1` if planned flight `f` operates,
- `c_fs = 1` if planned flight `f` is cancelled.

Core linking constraint:

`y_fs + c_fs = x_f`

Scenario capacity:

`sum_f y_fs <= capacity_s`

The example requires at least five flights to be scheduled so that disruption trade-offs are non-trivial.

## Installation

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
python src/run.py
```

## Test

```bash
pytest -q
```

The tests verify linking consistency, scenario capacity feasibility, and a valid positive objective value.

## Why SciPy MILP instead of PuLP/CBC?

This project uses `scipy.optimize.milp`, backed by HiGHS, to avoid the common Windows configuration problem where PuLP cannot locate an external `cbc.exe` executable. No separate CBC installation is required.

## Data

The current dataset is synthetic and generated directly in `src/model.py`. It is intentionally small enough to inspect manually while still representing a genuine two-stage stochastic mixed-integer optimization model.

## Verified result

On the included synthetic instance, the model solves to optimality with an expected total cost of `$29,425.50` and plans flights `F101, F102, F104, F105, F106`.

## License

Non-commercial use only. See `LICENSE`.
