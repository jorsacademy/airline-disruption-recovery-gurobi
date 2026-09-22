"""
Aircraft Maintenance Scheduling Optimization
--------------------------------------------
A compact MILP model for scheduling aircraft maintenance while preserving
technician capacity, concurrency limits, fleet readiness, and squadron readiness.

Requires:
    gurobipy
    pandas
    matplotlib
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import gurobipy as gp
from gurobipy import GRB
import matplotlib.pyplot as plt
import pandas as pd


@dataclass(frozen=True)
class MaintenanceType:
    name: str
    duration: int
    technicians: int


@dataclass(frozen=True)
class Aircraft:
    squadron: int
    maintenance_type: int
    priority: int  # smaller number = higher priority


class AircraftMaintenanceOptimizer:
    BLOCK_HOURS = 8

    def __init__(self) -> None:
        self.time_horizon = 168
        self.technicians_available = 30
        self.max_concurrent_maintenance = 8
        self.min_ready_total = 8
        self.min_ready_squadron = 2

        self.maintenance_types: Dict[int, MaintenanceType] = {
            1: MaintenanceType("Phase I", 8, 2),
            2: MaintenanceType("Phase II", 24, 4),
            3: MaintenanceType("Phase III", 48, 6),
        }

        self.aircraft: Dict[int, Aircraft] = {
            1: Aircraft(1, 1, 3),
            2: Aircraft(1, 1, 4),
            3: Aircraft(1, 2, 3),
            4: Aircraft(1, 2, 4),
            5: Aircraft(2, 1, 3),
            6: Aircraft(2, 1, 4),
            7: Aircraft(2, 2, 3),
            8: Aircraft(2, 3, 2),
            9: Aircraft(3, 1, 3),
            10: Aircraft(3, 1, 4),
            11: Aircraft(3, 2, 3),
            12: Aircraft(3, 2, 4),
        }

        self.time_blocks = list(range(0, self.time_horizon, self.BLOCK_HOURS))
        self.model: gp.Model | None = None
        self.x: gp.tupledict | None = None
        self.completion_time: gp.Var | None = None
        self.valid_starts: Dict[int, List[int]] = {}
        self.solution: pd.DataFrame | None = None

        self._validate_input()

    def _duration(self, aircraft_id: int) -> int:
        maintenance_id = self.aircraft[aircraft_id].maintenance_type
        return self.maintenance_types[maintenance_id].duration

    def _technicians(self, aircraft_id: int) -> int:
        maintenance_id = self.aircraft[aircraft_id].maintenance_type
        return self.maintenance_types[maintenance_id].technicians

    def _validate_input(self) -> None:
        if self.time_horizon <= 0 or self.time_horizon % self.BLOCK_HOURS != 0:
            raise ValueError("time_horizon must be a positive multiple of BLOCK_HOURS")

        if self.min_ready_total > len(self.aircraft):
            raise ValueError("min_ready_total cannot exceed fleet size")

        squadron_sizes: Dict[int, int] = {}
        for aircraft_id, data in self.aircraft.items():
            if data.maintenance_type not in self.maintenance_types:
                raise ValueError(
                    f"Aircraft {aircraft_id} references unknown maintenance type "
                    f"{data.maintenance_type}"
                )
            if data.priority <= 0:
                raise ValueError(f"Aircraft {aircraft_id} priority must be positive")
            squadron_sizes[data.squadron] = squadron_sizes.get(data.squadron, 0) + 1

        for squadron, size in squadron_sizes.items():
            if self.min_ready_squadron > size:
                raise ValueError(
                    f"min_ready_squadron={self.min_ready_squadron} exceeds "
                    f"Squadron {squadron} size={size}"
                )

    def _is_active(self, aircraft_id: int, start: int, block: int) -> bool:
        duration = self._duration(aircraft_id)
        return start <= block < start + duration

    def build_model(self) -> None:
        self.model = gp.Model("AircraftMaintenanceScheduling")
        self.model.Params.OutputFlag = 1
        self.model.Params.TimeLimit = 180
        self.model.Params.MIPGap = 1e-4

        for a in self.aircraft:
            duration = self._duration(a)
            starts = [
                b for b in self.time_blocks
                if b + duration <= self.time_horizon
            ]
            if not starts:
                raise ValueError(
                    f"Aircraft {a} maintenance cannot fit inside the planning horizon"
                )
            self.valid_starts[a] = starts

        start_pairs: List[Tuple[int, int]] = [
            (a, b)
            for a, starts in self.valid_starts.items()
            for b in starts
        ]
        self.x = self.model.addVars(start_pairs, vtype=GRB.BINARY, name="start")
        self.completion_time = self.model.addVar(
            lb=0.0,
            ub=float(self.time_horizon),
            vtype=GRB.CONTINUOUS,
            name="makespan",
        )

        for a, starts in self.valid_starts.items():
            self.model.addConstr(
                gp.quicksum(self.x[a, b] for b in starts) == 1,
                name=f"start_once[{a}]",
            )

        for a, starts in self.valid_starts.items():
            duration = self._duration(a)
            for b in starts:
                self.model.addConstr(
                    self.completion_time >= (b + duration) * self.x[a, b],
                    name=f"makespan[{a},{b}]",
                )

        squadrons = sorted({data.squadron for data in self.aircraft.values()})

        for t in self.time_blocks:
            active_expr = {
                a: gp.quicksum(
                    self.x[a, start]
                    for start in self.valid_starts[a]
                    if self._is_active(a, start, t)
                )
                for a in self.aircraft
            }

            self.model.addConstr(
                gp.quicksum(
                    self._technicians(a) * active_expr[a]
                    for a in self.aircraft
                ) <= self.technicians_available,
                name=f"technician_capacity[{t}]",
            )

            self.model.addConstr(
                gp.quicksum(active_expr[a] for a in self.aircraft)
                <= self.max_concurrent_maintenance,
                name=f"concurrency[{t}]",
            )

            self.model.addConstr(
                len(self.aircraft)
                - gp.quicksum(active_expr[a] for a in self.aircraft)
                >= self.min_ready_total,
                name=f"fleet_readiness[{t}]",
            )

            for squadron in squadrons:
                members = [
                    a for a, data in self.aircraft.items()
                    if data.squadron == squadron
                ]
                self.model.addConstr(
                    len(members)
                    - gp.quicksum(active_expr[a] for a in members)
                    >= self.min_ready_squadron,
                    name=f"squadron_readiness[{squadron},{t}]",
                )

        max_priority = max(data.priority for data in self.aircraft.values())
        weighted_start_delay = gp.quicksum(
            (max_priority + 1 - self.aircraft[a].priority) * b * self.x[a, b]
            for a, starts in self.valid_starts.items()
            for b in starts
        )

        self.model.setObjectiveN(
            self.completion_time,
            index=0,
            priority=2,
            weight=1.0,
            name="minimize_makespan",
        )
        self.model.setObjectiveN(
            weighted_start_delay,
            index=1,
            priority=1,
            weight=1.0,
            name="priority_weighted_start_delay",
        )

        self.model.update()

    def solve(self) -> bool:
        if self.model is None:
            self.build_model()

        assert self.model is not None
        self.model.optimize()

        if self.model.SolCount == 0:
            if self.model.Status == GRB.INFEASIBLE:
                self.model.computeIIS()
                self.model.write("aircraft_maintenance_iis.ilp")
                print("Model is infeasible. IIS written to aircraft_maintenance_iis.ilp")
            else:
                print(f"No feasible solution found. Solver status: {self.model.Status}")
            return False

        self._extract_solution()

        if self.model.Status == GRB.OPTIMAL:
            print("Optimal solution found within configured solver tolerances.")
        elif self.model.Status == GRB.TIME_LIMIT:
            print("Time limit reached; returning the best incumbent solution.")
        else:
            print(f"Returning incumbent solution. Solver status: {self.model.Status}")

        return True

    def _extract_solution(self) -> None:
        assert self.x is not None
        assert self.completion_time is not None

        rows = []
        for a, starts in self.valid_starts.items():
            for start in starts:
                if self.x[a, start].X > 0.5:
                    aircraft = self.aircraft[a]
                    maintenance = self.maintenance_types[aircraft.maintenance_type]
                    rows.append(
                        {
                            "Aircraft": f"AC-{a:03d}",
                            "Aircraft_ID": a,
                            "Squadron": aircraft.squadron,
                            "Maintenance_Type": maintenance.name,
                            "Start_Time": start,
                            "End_Time": start + maintenance.duration,
                            "Duration": maintenance.duration,
                            "Priority": aircraft.priority,
                            "Technicians": maintenance.technicians,
                        }
                    )

        self.solution = (
            pd.DataFrame(rows)
            .sort_values(["Start_Time", "Priority", "Aircraft_ID"])
            .reset_index(drop=True)
        )

    def validate_solution(self) -> None:
        if self.solution is None:
            raise RuntimeError("No solution available")

        df = self.solution

        if len(df) != len(self.aircraft):
            raise AssertionError("Not every aircraft was scheduled exactly once")

        if (df["End_Time"] > self.time_horizon).any():
            raise AssertionError("At least one maintenance task exceeds the horizon")

        for t in self.time_blocks:
            active = df[(df["Start_Time"] <= t) & (t < df["End_Time"])]

            if len(active) > self.max_concurrent_maintenance:
                raise AssertionError(f"Concurrency violation at hour {t}")

            if active["Technicians"].sum() > self.technicians_available:
                raise AssertionError(f"Technician capacity violation at hour {t}")

            if len(self.aircraft) - len(active) < self.min_ready_total:
                raise AssertionError(f"Fleet readiness violation at hour {t}")

            for squadron in sorted(df["Squadron"].unique()):
                squad_size = sum(
                    1 for data in self.aircraft.values()
                    if data.squadron == squadron
                )
                squad_active = active[active["Squadron"] == squadron]
                if squad_size - len(squad_active) < self.min_ready_squadron:
                    raise AssertionError(
                        f"Squadron {squadron} readiness violation at hour {t}"
                    )

    def report(self) -> pd.DataFrame:
        if self.solution is None:
            raise RuntimeError("No solution available")

        assert self.completion_time is not None

        self.validate_solution()
        df = self.solution

        print("\nAIRCRAFT MAINTENANCE SCHEDULE")
        print("=" * 72)
        print(f"Aircraft scheduled : {len(df)}")
        print(f"Makespan           : {self.completion_time.X:.1f} hours")
        print(f"Planning horizon   : {self.time_horizon} hours")
        print(f"Solver status      : {self.model.Status if self.model else 'N/A'}")

        print("\nMaintenance breakdown")
        print(
            df.groupby("Maintenance_Type")
            .agg(Aircraft=("Aircraft", "count"), Total_Hours=("Duration", "sum"))
        )

        print("\nSquadron workload")
        print(
            df.groupby("Squadron")
            .agg(Aircraft=("Aircraft", "count"), Total_Hours=("Duration", "sum"))
        )

        print("\nSchedule")
        print(
            df[
                [
                    "Aircraft",
                    "Squadron",
                    "Maintenance_Type",
                    "Start_Time",
                    "End_Time",
                    "Priority",
                    "Technicians",
                ]
            ].to_string(index=False)
        )

        return df

    def plot_schedule(self) -> None:
        if self.solution is None:
            raise RuntimeError("No solution available")

        df = self.solution.sort_values(["Start_Time", "Aircraft_ID"])

        fig, ax = plt.subplots(figsize=(13, 7))
        for _, row in df.iterrows():
            ax.barh(
                row["Aircraft"],
                row["Duration"],
                left=row["Start_Time"],
                alpha=0.8,
            )
            ax.text(
                row["Start_Time"] + row["Duration"] / 2,
                row["Aircraft"],
                row["Maintenance_Type"],
                ha="center",
                va="center",
                fontsize=8,
            )

        ax.set_xlabel("Time (hours)")
        ax.set_ylabel("Aircraft")
        ax.set_title("Aircraft Maintenance Schedule")
        ax.grid(axis="x", alpha=0.3)
        fig.tight_layout()
        plt.show()


def main() -> None:
    optimizer = AircraftMaintenanceOptimizer()

    if optimizer.solve():
        optimizer.report()
        optimizer.plot_schedule()


if __name__ == "__main__":
    main()
