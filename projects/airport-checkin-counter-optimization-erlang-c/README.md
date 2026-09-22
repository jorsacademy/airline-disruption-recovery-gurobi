# Airport Check-in Counter Optimization with Erlang C

This repository presents an educational operations research model for determining the number of active airport check-in counters required under time-varying passenger demand.

The project replaces a simplified waiting-time approximation with the classical Erlang C formulation for an M/M/s queue. Passenger arrivals are generated synthetically for a 24-hour period, and the model selects the least-cost integer number of check-in counters for each hour.

## Problem Setting

Airport check-in facilities face a capacity trade-off. Opening more counters increases staffing and operating cost, while opening too few counters increases passenger waiting time and congestion.

For each hour, the model minimizes:

```text
Total Cost = Counter Operating Cost + Passenger Waiting Cost
```

The decision variable is the integer number of active counters.

## Queueing Model

The system is modeled as an M/M/s queue with the following assumptions:

- Passenger arrivals follow a Poisson process.
- Check-in service times are exponentially distributed.
- All active counters have the same average service rate.
- Passengers join a common queue and are served by the next available counter.
- The queue is stable only when total service capacity exceeds the passenger arrival rate.

Let:

- `lambda` = passenger arrival rate per hour
- `mu` = service rate per counter per hour
- `s` = number of active counters
- `rho = lambda / (s * mu)` = server utilization

A feasible queue requires:

```text
rho < 1
```

The Erlang C probability that an arriving passenger must wait is:

```text
P(wait) = [a^s / s! * 1/(1-rho)] /
          [sum(k=0 to s-1) a^k/k! + a^s/s! * 1/(1-rho)]
```

where:

```text
a = lambda / mu
```

The expected queueing delay is then:

```text
Wq = P(wait) / (s * mu - lambda)
```

and the expected number of passengers waiting in queue is:

```text
Lq = lambda * Wq
```

## Optimization Approach

Because the number of check-in counters is discrete, the project does not solve a continuous optimization problem and then round the result. Instead, it enumerates all feasible integer counter counts from 1 to the configured maximum and selects the counter count with minimum hourly total cost.

The optimization is performed independently for every hour of the synthetic 24-hour passenger-demand profile.

## Synthetic Data

No real airport operational data are used in this repository. The hourly passenger-demand profile is synthetically generated using Poisson random variables with a fixed random seed for reproducibility.

The parameters are illustrative and should not be interpreted as calibrated estimates for any particular airport.

Default assumptions include:

```text
Maximum counters:                  20
Service rate per counter:           5 passengers/hour
Counter operating cost:           100 cost units/counter/hour
Passenger waiting cost:            50 cost units/passenger-hour
Random seed:                        42
```

These values can be modified directly in the Python file for sensitivity analysis.

## Repository Contents

```text
airport_checkin_erlang_c.py   Main queueing, optimization, reporting, and plotting code
README.md                     Project documentation
LICENSE.md                    Non-commercial educational license
requirements.txt              Python dependencies
.gitignore                    Common Python and Jupyter exclusions
```

## Running the Project

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run the model:

```bash
python airport_checkin_erlang_c.py
```

The script prints an hourly staffing table including passenger demand, optimal counters, utilization, expected queueing delay, and estimated hourly cost.

It also produces two figures:

1. Synthetic hourly passenger arrivals together with the optimized check-in counter schedule.
2. The operating-cost, waiting-cost, and total-cost trade-off for the peak-demand hour.

## Interpretation

The model captures the principal economic trade-off in service-capacity planning. When too few counters are active, utilization approaches one and expected waiting time rises sharply. Additional counters reduce congestion but increase operating expenditure. The optimum occurs where the marginal reduction in passenger waiting cost no longer justifies the cost of an additional counter.

The optimal number of counters may therefore vary across the day as passenger demand changes.

## Limitations

This project is designed as an instructional case study rather than a production airport-planning system. Important real-world features are not modeled, including:

- airline-specific counter allocation
- flight departure schedules
- passenger class differences
- baggage complexity
- priority queues
- self-service kiosks and bag-drop systems
- staff shift scheduling
- counter opening and closing transition costs
- non-exponential service-time distributions
- passenger abandonment
- missed-flight risk
- physical terminal constraints

A production model should be calibrated and validated using airport-specific operational data.

## Educational Purpose

The repository is intended to demonstrate how queueing theory and discrete optimization can be combined in an airport operations setting. It is suitable for teaching topics such as operations research, service systems, capacity planning, queueing theory, and decision analytics.

Commercial use is not permitted under the repository license.
