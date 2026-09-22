# Airline Crew Workforce Optimization with a Genetic Algorithm

## Optimization to Navigate a Turbulent Planning Horizon

This project demonstrates a non-linear-programming approach to long-term airline crew workforce planning. It is inspired by strategic airline planning problems in which fleet transitions, pilot demand, hiring, training, attrition, and workforce balance must be coordinated over several years.

The implementation uses a deterministic Genetic Algorithm (GA), not LP or MILP. A fixed random seed is used so that the same inputs and parameters produce reproducible results for teaching and demonstration.

## Business scenario

An airline is planning its pilot workforce over a five-year horizon while its fleet mix changes. Demand for pilots varies by aircraft family and year. At the same time, the airline must decide how many pilots to hire and how many existing pilots to retrain from Narrowbody to Widebody qualification.

The planning challenge includes:

- changing pilot demand by fleet type,
- retirements and voluntary attrition,
- limited annual hiring capacity,
- limited annual training capacity,
- fleet-driven qualification changes,
- understaffing risk,
- overstaffing cost,
- hiring and training cost,
- year-to-year hiring volatility.

The GA searches for a five-year hiring-and-training plan that minimizes the total planning penalty.

## Why a Genetic Algorithm?

This repository intentionally avoids LP/MILP. Each chromosome represents a complete multi-year workforce plan. The fitness function evaluates that plan by simulating workforce evolution year by year.

This makes the project suitable for teaching:

- metaheuristic optimization,
- simulation-based decision models,
- strategic workforce planning,
- scenario evaluation,
- reproducibility in stochastic algorithms.

## Project structure

```text
airline-crew-workforce-optimization-ga/
├── README.md
├── LICENSE
├── requirements.txt
├── data/
│   └── crew_planning_data.csv
└── src/
    └── crew_planning_ga.py
```

## Decision variables

For each year, the GA determines:

- external Narrowbody pilot hires,
- external Widebody pilot hires,
- Narrowbody pilots trained into Widebody qualification.

## Objective

The model minimizes a total planning cost composed of:

- severe understaffing penalties,
- moderate overstaffing penalties,
- hiring costs,
- training costs,
- hiring-volatility penalties.

The optimizer internally maximizes fitness, where fitness is the negative of total planning cost. For user-facing reporting, the code prints the positive planning cost instead of presenting a confusing negative fitness value.

## Reproducibility

The optimizer uses a fixed seed (`42`) by default. Repeated runs with the same code, data, and parameters therefore produce the same result.

## Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Then run:

```bash
python src/crew_planning_ga.py
```

The script prints:

- the optimized hiring plan,
- the optimized training plan,
- workforce supply by year,
- workforce demand by year,
- shortages and surpluses,
- total planning cost.

## Educational scope

This is a synthetic teaching model. It is not an operational airline crew-planning system and does not encode every labor agreement, aviation regulation, seniority rule, licensing requirement, or aircraft qualification pathway used by real airlines.

## License

This repository is source-available for non-commercial educational, academic, and personal use only. Commercial use is prohibited. See `LICENSE` for the complete terms.
