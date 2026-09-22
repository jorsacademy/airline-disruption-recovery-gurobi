# Final Report — Airline Crew Scheduling with Column Generation

## Scope

This repository is a compact research benchmark for airline crew-pairing style set covering. It is designed to expose the decomposition algorithm rather than hide it behind a monolithic solver call.

The implemented stack is now considered feature-complete for this repository:

1. exhaustive pairing enumeration on reference instances;
2. restricted master LP with explicit coverage duals;
3. exhaustive reduced-cost pricing for oracle validation;
4. acyclic label-setting RCSP pricing;
5. resource-rich labels carrying duty, block and sit-time state;
6. optional crew-base return legality;
7. integer restricted-master recovery;
8. column-variable branch-and-price-lite with fresh pricing at every node;
9. deterministic scaling benchmarks with runtime, generated-column and node counts;
10. CI tests that compare decomposed methods against tractable exact references.

## Mathematical model

For legal pairing set P and flight set F:

```text
min  sum_p c_p x_p
s.t. sum_p a_fp x_p >= 1       for every flight f
     x_p in {0,1}
```

Column generation solves the LP relaxation over a restricted pairing set. Coverage duals define the pricing reduced cost

```text
c_bar_p = c_p - sum_f pi_f a_fp.
```

Pricing searches for a legal pairing with negative reduced cost. If none exists within tolerance, the current restricted master solves the full LP relaxation represented by the pricing model.

## Resource-rich pricing

The final RCSP layer tracks:

- duty elapsed time;
- cumulative flight block time;
- cumulative sit time;
- number of legs;
- current airport;
- starting crew base/origin;
- reduced cost.

Extensions enforce minimum connection, maximum individual sit, maximum duty, maximum block, maximum legs and optional return to the configured crew base.

Dominance is only valid when future feasibility is preserved by the compared label state. Small instances retain exhaustive pricing as the correctness oracle.

## Integer recovery and branching

A binary restricted master is retained as a practical recovery baseline. The repository also implements a compact branch-and-price variant.

At a branch node, a fractional generated pairing variable is selected:

- the `x_p = 0` child forbids that pairing from subsequent pricing;
- the `x_p = 1` child fixes its cost and coverage contribution, then solves the residual covering problem;
- both children rerun column generation and therefore obtain node-specific LP bounds.

This is intentionally called **branch-and-price-lite** rather than a production crew-pairing branch-and-price system. Classical Ryan–Foster branching, stabilization, multi-day legality, crew qualifications and industrial-scale preprocessing remain outside this repository's scope.

## Validation contract

A result is accepted only when:

- every flight is covered;
- reduced-cost sign conventions are correct;
- RCSP pricing agrees with exhaustive pricing where enumeration is tractable;
- resource-constrained pairings satisfy the configured legality rules;
- column generation stops only when no negative-reduced-cost column remains within tolerance;
- branch-and-price-lite matches the full enumerated integer optimum on the toy reference;
- LP lower bound, restricted integer result and branch-and-price result are not conflated;
- scaling reports include columns, iterations, nodes and runtimes.

## Reproducibility

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
ruff check src tests
pytest -q
python -m crew_cg.experiment
python -m crew_cg.final_benchmark
```

`configs/final_benchmark.json` freezes the benchmark rules and scaling sizes.

## Interpretation

The purpose of the project is not to claim that column generation always outperforms a monolithic solver. Its research value comes from making decomposition observable: dual prices, pricing, resource feasibility, generated-column growth, LP/integer gaps and branching behavior can be inspected independently.

If integer recovery from root columns already matches the branch-and-price solution, that is a valid negative result for the need for branching on that instance. If branching improves the restricted integer result, the node-wise pricing mechanism explains why.

## Scope boundary

The repository is complete at the methodological benchmark level. Future work such as multi-day pairings, hotel/rest rules, deadheading, fleet/qualification coupling, Ryan–Foster branching, dual stabilization and airline-scale datasets should be separate research extensions rather than silently changing this benchmark's frozen contract.
