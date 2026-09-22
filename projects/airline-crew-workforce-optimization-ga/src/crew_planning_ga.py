"""Five-year airline crew workforce planning with a Genetic Algorithm.

This educational model deliberately avoids LP/MILP. Each chromosome encodes
annual hiring and Narrowbody-to-Widebody training decisions. The workforce is
then simulated year by year and scored using business-oriented penalties.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CostParameters:
    narrowbody_hire_cost: float = 85_000.0
    widebody_hire_cost: float = 115_000.0
    training_cost: float = 45_000.0
    narrowbody_shortage_penalty: float = 240_000.0
    widebody_shortage_penalty: float = 300_000.0
    narrowbody_surplus_penalty: float = 24_000.0
    widebody_surplus_penalty: float = 30_000.0
    hiring_volatility_penalty: float = 12_000.0


@dataclass(frozen=True)
class GAParameters:
    population_size: int = 160
    generations: int = 300
    mutation_rate: float = 0.12
    elite_count: int = 8
    tournament_size: int = 4
    seed: int = 42


class AirlineCrewWorkforceGA:
    """Deterministic GA for strategic airline pilot workforce planning."""

    def __init__(
        self,
        planning_data: pd.DataFrame,
        initial_narrowbody_pilots: int = 430,
        initial_widebody_pilots: int = 175,
        costs: CostParameters | None = None,
        ga: GAParameters | None = None,
    ) -> None:
        self.data = planning_data.reset_index(drop=True).copy()
        self.initial_nb = float(initial_narrowbody_pilots)
        self.initial_wb = float(initial_widebody_pilots)
        self.costs = costs or CostParameters()
        self.ga = ga or GAParameters()
        self.rng = np.random.default_rng(self.ga.seed)

        required_columns = {
            "year",
            "narrowbody_demand",
            "widebody_demand",
            "narrowbody_attrition_rate",
            "widebody_attrition_rate",
            "max_narrowbody_hires",
            "max_widebody_hires",
            "max_nb_to_wb_training",
        }
        missing = required_columns.difference(self.data.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        if self.ga.elite_count >= self.ga.population_size:
            raise ValueError("elite_count must be smaller than population_size")

    @property
    def horizon(self) -> int:
        return len(self.data)

    def _limits(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        return (
            self.data["max_narrowbody_hires"].to_numpy(dtype=int),
            self.data["max_widebody_hires"].to_numpy(dtype=int),
            self.data["max_nb_to_wb_training"].to_numpy(dtype=int),
        )

    def _random_chromosome(self) -> np.ndarray:
        max_nb, max_wb, max_training = self._limits()
        return np.column_stack(
            [
                self.rng.integers(0, max_nb + 1),
                self.rng.integers(0, max_wb + 1),
                self.rng.integers(0, max_training + 1),
            ]
        ).astype(int)

    def simulate(self, chromosome: np.ndarray) -> tuple[float, pd.DataFrame]:
        """Simulate one complete workforce plan and return cost plus detail."""
        if chromosome.shape != (self.horizon, 3):
            raise ValueError(
                f"Chromosome must have shape ({self.horizon}, 3), "
                f"received {chromosome.shape}."
            )

        nb_supply = self.initial_nb
        wb_supply = self.initial_wb
        total_cost = 0.0
        previous_total_hires: int | None = None
        records: list[dict[str, float | int]] = []

        for t, row in self.data.iterrows():
            nb_hires = int(chromosome[t, 0])
            wb_hires = int(chromosome[t, 1])
            requested_training = int(chromosome[t, 2])

            nb_hires = min(nb_hires, int(row["max_narrowbody_hires"]))
            wb_hires = min(wb_hires, int(row["max_widebody_hires"]))

            nb_supply *= 1.0 - float(row["narrowbody_attrition_rate"])
            wb_supply *= 1.0 - float(row["widebody_attrition_rate"])

            actual_training = min(
                requested_training,
                int(row["max_nb_to_wb_training"]),
                int(nb_supply),
            )

            nb_supply = nb_supply - actual_training + nb_hires
            wb_supply = wb_supply + actual_training + wb_hires

            nb_demand = float(row["narrowbody_demand"])
            wb_demand = float(row["widebody_demand"])

            nb_shortage = max(nb_demand - nb_supply, 0.0)
            wb_shortage = max(wb_demand - wb_supply, 0.0)
            nb_surplus = max(nb_supply - nb_demand, 0.0)
            wb_surplus = max(wb_supply - wb_demand, 0.0)

            total_cost += nb_hires * self.costs.narrowbody_hire_cost
            total_cost += wb_hires * self.costs.widebody_hire_cost
            total_cost += actual_training * self.costs.training_cost
            total_cost += nb_shortage * self.costs.narrowbody_shortage_penalty
            total_cost += wb_shortage * self.costs.widebody_shortage_penalty
            total_cost += nb_surplus * self.costs.narrowbody_surplus_penalty
            total_cost += wb_surplus * self.costs.widebody_surplus_penalty

            current_total_hires = nb_hires + wb_hires
            if previous_total_hires is not None:
                total_cost += (
                    abs(current_total_hires - previous_total_hires)
                    * self.costs.hiring_volatility_penalty
                )
            previous_total_hires = current_total_hires

            records.append(
                {
                    "year": int(row["year"]),
                    "nb_hires": nb_hires,
                    "wb_hires": wb_hires,
                    "nb_to_wb_training": actual_training,
                    "nb_supply": nb_supply,
                    "nb_demand": nb_demand,
                    "nb_shortage": nb_shortage,
                    "nb_surplus": nb_surplus,
                    "wb_supply": wb_supply,
                    "wb_demand": wb_demand,
                    "wb_shortage": wb_shortage,
                    "wb_surplus": wb_surplus,
                }
            )

        return total_cost, pd.DataFrame.from_records(records)

    def fitness(self, chromosome: np.ndarray) -> float:
        """Return fitness for maximization: lower planning cost is better."""
        planning_cost, _ = self.simulate(chromosome)
        return -planning_cost

    def _tournament_select(
        self, population: np.ndarray, fitness_values: np.ndarray
    ) -> np.ndarray:
        candidate_indices = self.rng.choice(
            len(population), size=self.ga.tournament_size, replace=False
        )
        winner = candidate_indices[np.argmax(fitness_values[candidate_indices])]
        return population[winner].copy()

    def _crossover(self, parent_a: np.ndarray, parent_b: np.ndarray) -> np.ndarray:
        mask = self.rng.random(parent_a.shape) < 0.5
        return np.where(mask, parent_a, parent_b).astype(int)

    def _mutate(self, chromosome: np.ndarray) -> np.ndarray:
        child = chromosome.copy()
        max_nb, max_wb, max_training = self._limits()
        limits = (max_nb, max_wb, max_training)

        for year_index in range(self.horizon):
            for gene_index, upper_bounds in enumerate(limits):
                if self.rng.random() < self.ga.mutation_rate:
                    step = int(self.rng.integers(-10, 11))
                    child[year_index, gene_index] = int(
                        np.clip(
                            child[year_index, gene_index] + step,
                            0,
                            upper_bounds[year_index],
                        )
                    )
        return child

    def optimize(self) -> tuple[np.ndarray, float, pd.DataFrame]:
        """Run the GA and return the best chromosome, cost, and simulation."""
        population = np.array(
            [self._random_chromosome() for _ in range(self.ga.population_size)]
        )

        best_chromosome: np.ndarray | None = None
        best_fitness = -np.inf

        for _ in range(self.ga.generations):
            fitness_values = np.array([self.fitness(x) for x in population])
            order = np.argsort(fitness_values)[::-1]

            if fitness_values[order[0]] > best_fitness:
                best_fitness = float(fitness_values[order[0]])
                best_chromosome = population[order[0]].copy()

            next_population = [
                population[index].copy() for index in order[: self.ga.elite_count]
            ]

            while len(next_population) < self.ga.population_size:
                parent_a = self._tournament_select(population, fitness_values)
                parent_b = self._tournament_select(population, fitness_values)
                child = self._crossover(parent_a, parent_b)
                next_population.append(self._mutate(child))

            population = np.array(next_population[: self.ga.population_size])

        if best_chromosome is None:
            raise RuntimeError("The optimizer did not produce a solution.")

        best_cost, details = self.simulate(best_chromosome)
        return best_chromosome, best_cost, details


def load_planning_data() -> pd.DataFrame:
    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "data" / "crew_planning_data.csv"
    return pd.read_csv(data_path)


def main() -> None:
    planning_data = load_planning_data()
    optimizer = AirlineCrewWorkforceGA(planning_data)
    best_plan, best_cost, details = optimizer.optimize()

    plan = pd.DataFrame(
        best_plan,
        columns=["nb_hires", "wb_hires", "nb_to_wb_training"],
    )
    plan.insert(0, "year", planning_data["year"].to_numpy())

    print("\nOPTIMIZED FIVE-YEAR WORKFORCE PLAN")
    print(plan.to_string(index=False))

    print("\nWORKFORCE BALANCE BY YEAR")
    display_columns = [
        "year",
        "nb_supply",
        "nb_demand",
        "nb_shortage",
        "nb_surplus",
        "wb_supply",
        "wb_demand",
        "wb_shortage",
        "wb_surplus",
    ]
    print(details[display_columns].round(2).to_string(index=False))

    print(f"\nTotal planning cost: ${best_cost:,.2f}")
    print(f"Reproducibility seed: {optimizer.ga.seed}")


if __name__ == "__main__":
    main()
