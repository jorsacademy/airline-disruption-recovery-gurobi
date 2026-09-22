# Validation Protocol

## Purpose

Validate the decomposition algorithm independently of any claim about large-instance speed.

## Reference ladder

For small instances, evaluate in this order:

1. enumerate all legal pairings;
2. solve the full LP relaxation;
3. run column generation with exhaustive pricing;
4. run column generation with label-setting RCSP pricing.

The LP objectives from steps 2-4 must agree within numerical tolerance.

## Pricing correctness

At identical master duals, exhaustive pricing and label-setting pricing must return the same minimum reduced cost on reference instances. The exact pairing may differ only when multiple pairings tie at the same reduced cost.

## Feasibility checks

Every generated pairing must satisfy:

- flight-time order;
- airport continuity;
- minimum connection time;
- maximum duty time;
- maximum leg count;
- no repeated flight within a pairing.

## Convergence condition

Column generation may terminate only when the best available reduced cost is at least `-tolerance`. The final restricted-master LP objective is then the reference LP bound for the implemented pricing resource model.

## Scaling experiments

For larger instances where full pairing enumeration is not attempted, report:

- number of flights;
- initial columns;
- final generated columns;
- number of master iterations;
- pricing calls;
- master solve time;
- pricing time;
- final LP objective.

No claim of global integer optimality should be made from the LP relaxation alone.

## Integer recovery

A later phase should solve an integer restricted master over generated columns and report the gap against the LP lower bound. Branch-and-price claims require branching logic that preserves valid pricing; simply solving the restricted master as a MILP is not branch-and-price.
