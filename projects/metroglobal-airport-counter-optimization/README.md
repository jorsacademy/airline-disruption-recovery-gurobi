# MetroGlobal Airport Holdings — Check-in Counter Optimization

This repository contains a synthetic airport operations case study inspired by large-hub check-in counter allocation problems.

The fictional company is **MetroGlobal Airport Holdings**, and the scenario is:

> **Efficiently Allocating Check-in Counters Across Airlines**

## Optimization Approach

This project deliberately does **not** use linear programming, mixed-integer linear programming, PuLP, Gurobi, or another mathematical-programming solver.

Instead, it uses **simulated annealing**, a stochastic metaheuristic.

The model creates synthetic data for:

- 180 airlines
- 120 check-in counters
- daily flight frequency
- airline priority
- passenger demand
- counter-capacity pressure
- preferred counter zones

The objective rewards valuable airline service while penalizing:

- counter overload,
- excessive airline concentration on a single counter,
- assignments far from an airline's preferred operating zone.

## Business Scenario

MetroGlobal Airport Holdings operates a large international airport with 120 check-in counters shared by 180 airlines. Passenger growth has increased pressure on terminal infrastructure, but management wants to postpone expensive physical expansion by using the existing counters more efficiently.

The optimization model therefore seeks high-quality counter assignments while accounting for operational congestion, airline priorities, passenger demand, and preferred terminal zones.

## Why Simulated Annealing?

The assignment space is extremely large, and the user requirement for this case is to avoid linear programming. Simulated annealing provides a practical non-linear-programming alternative that can explore many candidate allocations and occasionally accept worse intermediate solutions to escape local optima.

The method does not guarantee a mathematical global optimum, but it is appropriate for scenario analysis and heuristic operational optimization.

## Run

```bash
python airport_counter_optimization.py
```

Install the required package with:

```bash
pip install -r requirements.txt
```

## Output

The script prints:

- the best objective score found,
- the airline-to-counter allocation vector,
- number of used and unused counters,
- maximum number of airlines sharing one counter,
- average number of airlines per used counter.

## Important Modeling Note

This is a **fictional scenario model**. It is not a reconstruction of Copenhagen Airport's proprietary optimization model or operational data. All airline, passenger, priority, and demand data are synthetically generated.
