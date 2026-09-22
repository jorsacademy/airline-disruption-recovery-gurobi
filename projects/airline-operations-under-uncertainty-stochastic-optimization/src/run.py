from model import default_instance, solve_stochastic_airline


def main() -> None:
    flights, scenarios = default_instance()
    solution = solve_stochastic_airline(flights, scenarios)
    print(f"Optimization status: {solution['status']}")
    print(f"Expected total cost: ${solution['objective']:,.2f}")
    print("Planned flights:", ", ".join(solution["planned"]))
    for name, result in solution["scenarios"].items():
        print(f"\nScenario: {name}")
        print("  Operated:", ", ".join(result["operated"]) or "None")
        print("  Cancelled:", ", ".join(result["cancelled"]) or "None")


if __name__ == "__main__":
    main()
