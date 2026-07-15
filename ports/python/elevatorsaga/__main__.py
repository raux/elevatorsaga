"""Main entry point for running Elevator Saga simulations."""

import sys
import importlib.util
import argparse

from .world import World
from .challenges import CHALLENGES


def load_solution(path):
    """Load a solution module from a file path."""
    spec = importlib.util.spec_from_file_location("solution", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "init"):
        raise RuntimeError("Solution must define an init(elevators, floors) function")
    if not hasattr(module, "update"):
        raise RuntimeError("Solution must define an update(dt, elevators, floors) function")
    return module


def run_challenge(challenge_index, solution_module, time_step=0.025, max_time=3600, verbose=True):
    """Run a single challenge with the given solution.
    
    Returns True if challenge passed, False if failed.
    """
    if challenge_index < 0 or challenge_index >= len(CHALLENGES):
        print(f"Error: Challenge {challenge_index + 1} does not exist. Available: 1-{len(CHALLENGES)}")
        return False

    challenge = CHALLENGES[challenge_index]
    condition = challenge["condition"]
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"  Challenge #{challenge_index + 1}")
        print(f"  {condition['description']}")
        print(f"{'='*60}")

    world = World(challenge["options"])
    
    # Initialize user code
    try:
        solution_module.init(world.elevator_interfaces, world.floors)
        world.init()
    except Exception as e:
        print(f"Error in solution init: {e}")
        return False

    # Run simulation
    result = None
    last_report_time = 0.0
    
    while result is None and world.elapsed_time < max_time:
        try:
            solution_module.update(time_step, world.elevator_interfaces, world.floors)
        except Exception as e:
            print(f"Error in solution update: {e}")
            return False

        world.update(time_step)
        result = condition["evaluate"](world)

        # Periodic status report
        if verbose and world.elapsed_time - last_report_time >= 5.0:
            last_report_time = world.elapsed_time
            print(f"  [{world.elapsed_time:6.1f}s] Transported: {world.transported_counter:4d} | "
                  f"Moves: {world.move_count:4d} | Max wait: {world.max_wait_time:.1f}s | "
                  f"Waiting: {len(world.users):3d}")

    if verbose:
        print(f"\n  Final: {world.elapsed_time:.1f}s elapsed, "
              f"{world.transported_counter} transported, "
              f"{world.move_count} moves, "
              f"max wait {world.max_wait_time:.1f}s")

    if result is True:
        if verbose:
            print(f"  ✓ CHALLENGE PASSED!")
        return True
    elif result is False:
        if verbose:
            print(f"  ✗ CHALLENGE FAILED")
        return False
    else:
        if verbose:
            print(f"  ⚠ Challenge timed out (max simulation time reached)")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Elevator Saga - The elevator programming game (Python edition)"
    )
    parser.add_argument(
        "--challenge", "-c", type=int, default=1,
        help="Challenge number (1-indexed, default: 1)"
    )
    parser.add_argument(
        "--solution", "-s", required=True,
        help="Path to solution Python file"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="Minimal output"
    )
    parser.add_argument(
        "--all", "-a", action="store_true",
        help="Run all challenges"
    )
    args = parser.parse_args()

    solution = load_solution(args.solution)

    if args.all:
        passed = 0
        for i in range(len(CHALLENGES)):
            if CHALLENGES[i]["condition"]["description"] == "Perpetual demo":
                continue
            if run_challenge(i, solution, verbose=not args.quiet):
                passed += 1
        total = len(CHALLENGES) - 1  # Exclude demo
        print(f"\nResults: {passed}/{total} challenges passed")
        sys.exit(0 if passed == total else 1)
    else:
        success = run_challenge(args.challenge - 1, solution, verbose=not args.quiet)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
