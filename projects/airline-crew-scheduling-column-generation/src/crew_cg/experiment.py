from .column_generation import run_column_generation
from .column_generation_rcsp import run_column_generation_rcsp
from .generator import hub_timetable
from .integer_master import integrality_gap, solve_integer_master
from .master import solve_master
from .model import toy_flights
from .pairing import enumerate_pairings


def main():
    flights = toy_flights()
    full_pairings = enumerate_pairings(flights)
    full = solve_master(flights, full_pairings)
    exhaustive_cg, exhaustive_active, _ = run_column_generation(flights)
    rcsp_cg, rcsp_active, rcsp_history = run_column_generation_rcsp(flights)
    toy_integer = solve_integer_master(flights, rcsp_active)

    print("toy_instance")
    print(f"full_enumeration_columns={len(full_pairings)}")
    print(f"exhaustive_cg_columns={len(exhaustive_active)}")
    print(f"rcsp_cg_columns={len(rcsp_active)}")
    print(f"full_lp_objective={full['objective']:.3f}")
    print(f"exhaustive_cg_objective={exhaustive_cg['objective']:.3f}")
    print(f"rcsp_cg_objective={rcsp_cg['objective']:.3f}")
    print(f"integer_restricted_master={toy_integer['objective']:.3f}")
    print(
        f"integrality_gap={integrality_gap(rcsp_cg['objective'], toy_integer['objective']):.6f}"
    )

    larger = hub_timetable(waves=3)
    larger_master, larger_active, larger_history = run_column_generation_rcsp(larger)
    larger_integer = solve_integer_master(larger, larger_active)
    print("synthetic_hub_instance")
    print(f"flights={len(larger)}")
    print(f"generated_columns={len(larger_active)}")
    print(f"iterations={len(larger_history)}")
    print(f"lp_objective={larger_master['objective']:.3f}")
    print(f"integer_objective={larger_integer['objective']:.3f}")
    print(
        "integrality_gap="
        f"{integrality_gap(larger_master['objective'], larger_integer['objective']):.6f}"
    )

    print("toy_rcsp_iteration,objective,columns,best_reduced_cost")
    for row in rcsp_history:
        print(
            f"{row['iteration']},{row['objective']:.3f},"
            f"{row['columns']},{row['best_reduced_cost']:.6f}"
        )


if __name__ == "__main__":
    main()
