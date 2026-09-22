from __future__ import annotations

from time import perf_counter

from .branch_price_lite import branch_and_price_lite
from .generator import hub_timetable
from .integer_master import integrality_gap, solve_integer_master
from .resource_column_generation import run_resource_column_generation
from .resource_pricing import CrewRules


def run_final_benchmark(waves: tuple[int, ...] = (1, 2, 3)) -> list[dict[str, float | int]]:
    rows: list[dict[str, float | int]] = []
    rules = CrewRules(require_base_return=False, max_block=300, max_sit=180)
    for wave_count in waves:
        flights = hub_timetable(waves=wave_count)
        start = perf_counter()
        master, columns, history = run_resource_column_generation(flights, rules=rules)
        cg_ms = (perf_counter() - start) * 1000.0

        start = perf_counter()
        integer = solve_integer_master(flights, columns)
        integer_ms = (perf_counter() - start) * 1000.0

        start = perf_counter()
        branch = branch_and_price_lite(flights, rules=rules, max_nodes=60)
        branch_ms = (perf_counter() - start) * 1000.0

        rows.append(
            {
                "waves": wave_count,
                "flights": len(flights),
                "generated_columns": len(columns),
                "cg_iterations": len(history),
                "lp_objective": float(master["objective"]),
                "restricted_integer_objective": float(integer["objective"]),
                "integrality_gap": integrality_gap(master["objective"], integer["objective"]),
                "branch_price_objective": float(branch["objective"]),
                "branch_nodes": int(branch["nodes_explored"]),
                "branch_pricing_iterations": int(branch["pricing_iterations"]),
                "cg_ms": cg_ms,
                "integer_ms": integer_ms,
                "branch_price_ms": branch_ms,
            }
        )
    return rows


def main() -> None:
    print(
        "waves,flights,columns,cg_iterations,lp_obj,restricted_integer_obj,"
        "gap,branch_price_obj,branch_nodes,pricing_iterations,cg_ms,integer_ms,branch_ms"
    )
    for row in run_final_benchmark():
        print(
            f"{row['waves']},{row['flights']},{row['generated_columns']},"
            f"{row['cg_iterations']},{row['lp_objective']:.3f},"
            f"{row['restricted_integer_objective']:.3f},{row['integrality_gap']:.6f},"
            f"{row['branch_price_objective']:.3f},{row['branch_nodes']},"
            f"{row['branch_pricing_iterations']},{row['cg_ms']:.3f},"
            f"{row['integer_ms']:.3f},{row['branch_price_ms']:.3f}"
        )


if __name__ == "__main__":
    main()
