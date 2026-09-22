"""Airport check-in counter optimization using the Erlang C queueing model.

This educational example uses synthetic passenger arrival rates and assumes an
M/M/s queue: Poisson arrivals, exponential service times, and s identical
parallel check-in counters.
"""

from math import factorial

import matplotlib.pyplot as plt
import numpy as np


RANDOM_SEED = 42
MAX_COUNTERS = 20
SERVICE_RATE = 5.0  # passengers served per counter per hour
COUNTER_COST_PER_HOUR = 100.0
WAITING_COST_PER_PASSENGER_HOUR = 50.0


def generate_hourly_arrival_rates(seed=RANDOM_SEED):
    """Generate a reproducible 24-hour synthetic airport arrival profile."""
    rng = np.random.default_rng(seed)
    hours = np.arange(24)

    mean_arrivals = np.array(
        [12, 10, 8, 8, 12, 20, 35, 50, 55, 48, 35, 30,
         28, 30, 35, 40, 45, 55, 60, 50, 35, 25, 18, 14],
        dtype=float,
    )

    arrival_rates = rng.poisson(mean_arrivals)
    return hours, arrival_rates


def erlang_c_probability(arrival_rate, service_rate, counters):
    """Return the Erlang C probability that an arriving passenger must wait."""
    offered_load = arrival_rate / service_rate
    utilization = arrival_rate / (counters * service_rate)

    if arrival_rate == 0:
        return 0.0
    if utilization >= 1.0:
        return 1.0

    series_sum = sum(offered_load ** k / factorial(k) for k in range(counters))
    tail_term = (
        offered_load ** counters
        / factorial(counters)
        * (1.0 / (1.0 - utilization))
    )

    return tail_term / (series_sum + tail_term)


def queue_metrics(arrival_rate, service_rate, counters):
    """Compute utilization, waiting probability, Lq, and Wq for an M/M/s queue."""
    if counters < 1:
        raise ValueError("The number of counters must be at least 1.")
    if service_rate <= 0:
        raise ValueError("Service rate must be positive.")
    if arrival_rate < 0:
        raise ValueError("Arrival rate cannot be negative.")

    if arrival_rate == 0:
        return {
            "utilization": 0.0,
            "probability_wait": 0.0,
            "Lq": 0.0,
            "Wq": 0.0,
        }

    utilization = arrival_rate / (counters * service_rate)

    if utilization >= 1.0:
        return {
            "utilization": utilization,
            "probability_wait": 1.0,
            "Lq": np.inf,
            "Wq": np.inf,
        }

    probability_wait = erlang_c_probability(arrival_rate, service_rate, counters)
    wq = probability_wait / (counters * service_rate - arrival_rate)
    lq = arrival_rate * wq

    return {
        "utilization": utilization,
        "probability_wait": probability_wait,
        "Lq": lq,
        "Wq": wq,
    }


def hourly_cost(arrival_rate, service_rate, counters):
    """Return hourly operating, waiting, and total costs for a counter level."""
    metrics = queue_metrics(arrival_rate, service_rate, counters)

    if not np.isfinite(metrics["Wq"]):
        return {
            "operational_cost": np.inf,
            "waiting_cost": np.inf,
            "total_cost": np.inf,
            **metrics,
        }

    operational_cost = COUNTER_COST_PER_HOUR * counters
    waiting_cost = (
        WAITING_COST_PER_PASSENGER_HOUR
        * arrival_rate
        * metrics["Wq"]
    )
    total_cost = operational_cost + waiting_cost

    return {
        "operational_cost": operational_cost,
        "waiting_cost": waiting_cost,
        "total_cost": total_cost,
        **metrics,
    }


def optimize_counters_for_hour(arrival_rate, service_rate=SERVICE_RATE, max_counters=MAX_COUNTERS):
    """Enumerate integer counter counts and return the least-cost feasible choice."""
    candidates = []

    for counters in range(1, max_counters + 1):
        result = hourly_cost(arrival_rate, service_rate, counters)
        if np.isfinite(result["total_cost"]):
            candidates.append((counters, result))

    if not candidates:
        raise ValueError(
            "No stable solution exists within the configured maximum number of counters."
        )

    return min(candidates, key=lambda item: item[1]["total_cost"])


def optimize_full_day(arrival_rates, service_rate=SERVICE_RATE, max_counters=MAX_COUNTERS):
    """Optimize the integer number of active counters separately for each hour."""
    schedule = []

    for hour, arrival_rate in enumerate(arrival_rates):
        counters, result = optimize_counters_for_hour(
            arrival_rate=arrival_rate,
            service_rate=service_rate,
            max_counters=max_counters,
        )
        schedule.append(
            {
                "hour": hour,
                "arrival_rate": int(arrival_rate),
                "counters": counters,
                **result,
            }
        )

    return schedule


def print_schedule(schedule):
    """Print a compact hourly optimization table."""
    print("Hour | Arrivals/hr | Counters | Utilization | Wq (min) | Hourly cost")
    print("-" * 72)

    for row in schedule:
        print(
            f"{row['hour']:>4} | "
            f"{row['arrival_rate']:>11} | "
            f"{row['counters']:>8} | "
            f"{row['utilization']:>11.2%} | "
            f"{row['Wq'] * 60:>8.2f} | "
            f"{row['total_cost']:>11.2f}"
        )

    daily_total_cost = sum(row["total_cost"] for row in schedule)
    print(f"\nEstimated total cost over 24 hours: {daily_total_cost:.2f}")


def plot_arrivals_and_counters(hours, arrival_rates, schedule):
    """Plot synthetic passenger arrivals and the optimized counter schedule."""
    optimized_counters = [row["counters"] for row in schedule]

    fig, ax1 = plt.subplots(figsize=(11, 6))
    ax1.plot(hours, arrival_rates, marker="o", label="Passenger arrivals per hour")
    ax1.set_xlabel("Hour of day")
    ax1.set_ylabel("Passenger arrivals per hour")
    ax1.set_title("Synthetic Airport Demand and Optimized Check-in Counter Schedule")
    ax1.set_xticks(hours)
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.step(hours, optimized_counters, where="mid", label="Optimal active counters")
    ax2.set_ylabel("Number of active counters")

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")

    plt.tight_layout()
    plt.show()


def plot_peak_hour_cost_curve(schedule, service_rate=SERVICE_RATE, max_counters=MAX_COUNTERS):
    """Visualize the cost trade-off for the hour with the highest arrival rate."""
    peak_row = max(schedule, key=lambda row: row["arrival_rate"])
    arrival_rate = peak_row["arrival_rate"]
    optimal_counters = peak_row["counters"]

    counters = np.arange(1, max_counters + 1)
    total_costs = []
    operational_costs = []
    waiting_costs = []

    for counter_count in counters:
        result = hourly_cost(arrival_rate, service_rate, int(counter_count))
        total_costs.append(result["total_cost"])
        operational_costs.append(
            COUNTER_COST_PER_HOUR * counter_count
            if np.isfinite(result["total_cost"])
            else np.nan
        )
        waiting_costs.append(
            result["waiting_cost"] if np.isfinite(result["waiting_cost"]) else np.nan
        )

    total_costs = np.array(total_costs, dtype=float)
    total_costs[~np.isfinite(total_costs)] = np.nan

    plt.figure(figsize=(10, 6))
    plt.plot(counters, total_costs, marker="o", label="Total cost")
    plt.plot(counters, operational_costs, marker="o", label="Operational cost")
    plt.plot(counters, waiting_costs, marker="o", label="Passenger waiting cost")
    plt.axvline(optimal_counters, linestyle="--", label=f"Optimal counters: {optimal_counters}")
    plt.xlabel("Number of check-in counters")
    plt.ylabel("Cost per hour")
    plt.title(
        f"Peak-Hour Cost Trade-off: Hour {peak_row['hour']} "
        f"({arrival_rate} passengers/hour)"
    )
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def main():
    hours, arrival_rates = generate_hourly_arrival_rates()
    schedule = optimize_full_day(arrival_rates)

    print_schedule(schedule)
    plot_arrivals_and_counters(hours, arrival_rates, schedule)
    plot_peak_hour_cost_curve(schedule)


if __name__ == "__main__":
    main()
