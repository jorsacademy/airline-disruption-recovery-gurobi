import numpy as np


class AirportCounterOptimizer:
    """
    Simulated annealing model for assigning airlines to check-in counters.

    This is intentionally a non-linear-programming / metaheuristic approach.
    No LP/MILP solver is used.
    """

    def __init__(
        self,
        num_airlines=180,
        num_counters=120,
        seed=42,
        counter_capacity=450.0,
        overload_penalty=8.0,
        congestion_penalty=2.5,
    ):
        self.num_airlines = num_airlines
        self.num_counters = num_counters
        self.counter_capacity = float(counter_capacity)
        self.overload_penalty = float(overload_penalty)
        self.congestion_penalty = float(congestion_penalty)
        self.rng = np.random.default_rng(seed)

        # Synthetic airline data
        self.flights = self.rng.poisson(lam=9, size=num_airlines) + 1
        self.priority = self.rng.uniform(1.0, 3.0, size=num_airlines)
        self.avg_passengers_per_flight = self.rng.integers(90, 221, size=num_airlines)

        # Daily passenger demand proxy
        self.passenger_demand = self.flights * self.avg_passengers_per_flight

        # Number of counters an airline ideally needs.
        self.required_counter_equivalents = np.maximum(
            1.0, self.passenger_demand / 1400.0
        )

        # Preferred counter zone for each airline, representing terminal familiarity,
        # alliance proximity, staff convenience, etc.
        self.preferred_zone = self.rng.integers(0, num_counters, size=num_airlines)

    def score(self, allocation):
        """
        Higher is better.

        Components:
        - reward high-priority airlines for being assigned
        - penalize passenger-capacity overload at counters
        - penalize excessive concentration of airlines at the same counter
        - penalize distance from each airline's preferred counter zone
        """
        allocation = np.asarray(allocation, dtype=int)

        # Base service value is airline-specific.
        service_value = np.sum(
            self.flights * self.priority * np.log1p(self.passenger_demand)
        )

        load = np.zeros(self.num_counters, dtype=float)
        airline_count = np.zeros(self.num_counters, dtype=int)

        for i, counter in enumerate(allocation):
            load[counter] += self.required_counter_equivalents[i] * 100.0
            airline_count[counter] += 1

        overload = np.clip(load - self.counter_capacity, 0.0, None)
        overload_cost = self.overload_penalty * np.sum(overload**2)

        # More than 3 airlines sharing one counter creates operational congestion.
        excessive_sharing = np.clip(airline_count - 3, 0, None)
        congestion_cost = self.congestion_penalty * np.sum(excessive_sharing**2)

        # Circular distance because counters are treated as a long bank / zone sequence.
        raw_distance = np.abs(allocation - self.preferred_zone)
        circular_distance = np.minimum(
            raw_distance, self.num_counters - raw_distance
        )
        zone_cost = np.sum(
            circular_distance * self.priority * self.required_counter_equivalents
        )

        return service_value - overload_cost - congestion_cost - zone_cost

    def random_initial_solution(self):
        return self.rng.integers(
            0, self.num_counters, size=self.num_airlines, dtype=int
        )

    def neighbor(self, allocation):
        new_solution = allocation.copy()

        move_type = self.rng.choice(["move", "swap"], p=[0.7, 0.3])

        if move_type == "move":
            airline = self.rng.integers(0, self.num_airlines)
            new_counter = self.rng.integers(0, self.num_counters)
            new_solution[airline] = new_counter
        else:
            a, b = self.rng.choice(self.num_airlines, size=2, replace=False)
            new_solution[a], new_solution[b] = new_solution[b], new_solution[a]

        return new_solution

    def simulated_annealing(
        self,
        initial_temperature=5000.0,
        final_temperature=0.5,
        cooling_rate=0.997,
        iterations_per_temperature=20,
    ):
        current = self.random_initial_solution()
        current_score = self.score(current)

        best = current.copy()
        best_score = current_score

        temperature = initial_temperature
        iteration = 0
        history = []

        while temperature > final_temperature:
            for _ in range(iterations_per_temperature):
                candidate = self.neighbor(current)
                candidate_score = self.score(candidate)
                delta = candidate_score - current_score

                if delta >= 0:
                    accept = True
                else:
                    accept_probability = np.exp(delta / temperature)
                    accept = self.rng.random() < accept_probability

                if accept:
                    current = candidate
                    current_score = candidate_score

                    if current_score > best_score:
                        best = current.copy()
                        best_score = current_score

                iteration += 1

            history.append((iteration, temperature, best_score))
            temperature *= cooling_rate

        return best, best_score, history

    def summarize(self, allocation):
        allocation = np.asarray(allocation, dtype=int)
        counts = np.bincount(allocation, minlength=self.num_counters)

        used_counters = int(np.sum(counts > 0))
        max_airlines_on_counter = int(np.max(counts))
        mean_airlines_on_used_counter = float(
            np.mean(counts[counts > 0]) if used_counters else 0.0
        )

        return {
            "used_counters": used_counters,
            "unused_counters": self.num_counters - used_counters,
            "max_airlines_on_one_counter": max_airlines_on_counter,
            "mean_airlines_per_used_counter": mean_airlines_on_used_counter,
        }


if __name__ == "__main__":
    optimizer = AirportCounterOptimizer(
        num_airlines=180,
        num_counters=120,
        seed=42,
    )

    best_allocation, best_score, history = optimizer.simulated_annealing()

    print("Best objective score:", round(best_score, 3))
    print("Allocation:")
    print(best_allocation)

    print("\nSummary:")
    for key, value in optimizer.summarize(best_allocation).items():
        print(f"{key}: {value}")
