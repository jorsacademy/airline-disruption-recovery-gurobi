# Airline Crew Scheduling with Column Generation

Research-oriented Operations Research benchmark for crew-pairing style set covering with **Dantzig-Wolfe column generation, resource-constrained pricing and integer recovery**.

## Research question

How far can decomposition scale before pairing enumeration becomes impractical, and when does node-wise pricing materially improve integer recovery beyond a root restricted master?

## Current status

**Feature-complete research benchmark.**

The repository implements:

- flight and pairing data structures;
- exhaustive legal-pairing enumeration for transparent reference instances;
- restricted master LP solved with HiGHS through SciPy;
- explicit coverage-dual extraction;
- exhaustive reduced-cost pricing as an oracle;
- acyclic label-setting RCSP pricing;
- resource-rich labels with duty, block and sit-time state;
- optional crew-base return legality;
- deterministic hub-and-spoke timetable generation;
- binary restricted-master recovery and integrality-gap reporting;
- column-variable **branch-and-price-lite** with fresh pricing at every branch node;
- frozen scaling configuration, tests, final report and CI across Python 3.10–3.12.

## Master formulation

For legal pairing set `P` and flights `F`:

```text
min  sum(c_p x_p)                 p in P
s.t. sum(a_fp x_p) >= 1           f in F
     x_p in {0,1}
```

Column generation solves the LP relaxation over a restricted subset of pairings. Coverage duals `pi_f` define reduced cost

```text
c_bar_p = c_p - sum(pi_f a_fp).
```

Pricing adds a negative-reduced-cost legal pairing until no improving column remains within tolerance.

## Resource-constrained pricing

The final RCSP state tracks:

- starting origin/base and departure time;
- current airport and arrival time;
- cumulative block time;
- cumulative sit time;
- duty elapsed time;
- number of legs;
- reduced cost.

The pricing rules support minimum connection, maximum sit, maximum duty, maximum block, maximum legs and optional return to the configured crew base. Dominance is only applied when the compared labels share the same future-relevant boundary state.

## Integer recovery and branch-and-price-lite

Two integer layers are deliberately reported separately.

**Restricted integer master:** after root LP column generation terminates, the generated columns are frozen and solved as a binary set-covering MILP.

**Branch-and-price-lite:** if a generated pairing variable is fractional, the tree branches on `x_p = 0` versus `x_p = 1`. The zero child forbids that pairing from subsequent pricing. The one child fixes its cost and coverage contribution and solves the residual cover. Column generation is rerun at every node, producing node-specific LP bounds.

This is a real node-wise pricing implementation, but it is intentionally not presented as an airline-production branch-and-price solver. Ryan–Foster branching, multi-day legality, deadheading and stabilization remain outside the frozen scope.

## Reproducible benchmark

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
ruff check src tests
pytest -q
python -m crew_cg.experiment
python -m crew_cg.final_benchmark
```

`configs/final_benchmark.json` freezes crew-resource limits, reduced-cost tolerance, branch-node budget and scaling sizes.

The final benchmark reports:

- flights;
- generated columns;
- column-generation iterations;
- LP lower bound;
- restricted integer objective;
- integrality gap;
- branch-and-price-lite objective;
- branch nodes and pricing iterations;
- CG, MILP recovery and branch-and-price runtimes.

## Repository map

```text
src/crew_cg/
  model.py
  generator.py
  pairing.py
  master.py
  pricing_rcsp.py
  column_generation.py
  column_generation_rcsp.py
  resource_pricing.py
  resource_column_generation.py
  integer_master.py
  branch_price_lite.py
  experiment.py
  final_benchmark.py
tests/
  test_column_generation.py
  test_rcsp_pricing.py
  test_integer_master.py
  test_completion.py
configs/
  experiment.json
  final_benchmark.json
docs/
  final_report.md
.github/workflows/
  ci.yml
```

## Validation contract

A result is accepted only if:

1. every flight is covered;
2. reduced-cost dual signs are correct;
3. RCSP pricing agrees with exhaustive pricing where enumeration is tractable;
4. resource-rich pairings satisfy configured legality rules;
5. column generation terminates only without a negative-reduced-cost column;
6. the toy branch-and-price-lite result matches the full enumerated integer optimum;
7. LP, restricted-integer and branch-and-price results are reported separately;
8. column counts, iteration counts, node counts and runtimes are retained.

See `docs/final_report.md` for the complete methodological contract and scope boundary.

## Scope boundary

This repository is complete as a compact decomposition benchmark. Multi-day pairing, rest/hotel rules, qualifications, deadheading, Ryan–Foster branching, dual stabilization and industrial airline datasets should be separate research extensions rather than hidden changes to this benchmark.

## License

MIT
