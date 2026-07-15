"""Record Elevator Saga simulations as JSON traces for visualization."""

from __future__ import annotations

import argparse
import importlib.util
import json
import random
from pathlib import Path

from .challenges import CHALLENGES
from .world import World

TIME_STEP = 0.025
DEFAULT_SAMPLE_EVERY = 0.1
MAX_TIME = 3600.0
MAX_FRAMES = 6000


def load_solution(path):
    spec = importlib.util.spec_from_file_location("visualized_solution", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load solution: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "init", None)):
        raise RuntimeError("Solution must define init(elevators, floors)")
    if not callable(getattr(module, "update", None)):
        raise RuntimeError("Solution must define update(dt, elevators, floors)")
    return module


def snapshot(world, user_ids):
    elevators = []
    for index, elevator in enumerate(world.elevators):
        x, y = elevator.get_world_position()
        elevators.append(
            {
                "id": index,
                "x": round(x, 4),
                "y": round(y, 4),
                "floor": elevator.current_floor,
                "load": round(elevator.get_load_factor(), 4),
                "up": elevator.going_up_indicator,
                "down": elevator.going_down_indicator,
            }
        )

    users = []
    for user in world.users:
        if user not in user_ids:
            user_ids[user] = len(user_ids)
        x, y = user.get_world_position()
        users.append(
            {
                "id": user_ids[user],
                "x": round(x, 4),
                "y": round(y, 4),
                "from": user.current_floor,
                "to": user.destination_floor,
                "done": user.done,
                "type": user.display_type,
            }
        )

    return {
        "time": round(world.elapsed_time, 4),
        "elevators": elevators,
        "users": users,
        "stats": {
            "transported": world.transported_counter,
            "moves": world.move_count,
            "maxWaitTime": round(world.max_wait_time, 4),
            "avgWaitTime": round(world.avg_wait_time, 4),
        },
    }


def record_trace(solution_path, challenge_number, sample_every=DEFAULT_SAMPLE_EVERY, seed=1):
    if not 1 <= challenge_number <= len(CHALLENGES):
        raise ValueError(f"Challenge must be between 1 and {len(CHALLENGES)}")
    if sample_every < TIME_STEP:
        raise ValueError(f"Sample interval must be at least {TIME_STEP}")

    random.seed(seed)
    challenge = CHALLENGES[challenge_number - 1]
    world = World(challenge["options"])
    solution = load_solution(solution_path)
    callback_errors = []
    world.on("usercode_error", lambda error: callback_errors.append(error))

    error = None
    result = None
    user_ids = {}
    frames = []
    next_sample = 0.0

    try:
        solution.init(world.elevator_interfaces, world.floors)
        world.init()
        if callback_errors:
            raise callback_errors[0]
    except Exception as exception:
        error = f"Error in solution init: {exception}"

    frames.append(snapshot(world, user_ids))
    next_sample = sample_every

    while error is None and result is None and world.elapsed_time < MAX_TIME:
        try:
            solution.update(TIME_STEP, world.elevator_interfaces, world.floors)
            if callback_errors:
                raise callback_errors.pop(0)
            world.update(TIME_STEP)
            if callback_errors:
                raise callback_errors.pop(0)
        except Exception as exception:
            error = f"Error in solution callback/update: {exception}"
            break

        result = challenge["condition"]["evaluate"](world)
        if world.elapsed_time + 1e-9 >= next_sample and len(frames) < MAX_FRAMES:
            frames.append(snapshot(world, user_ids))
            next_sample += sample_every

    final_frame = snapshot(world, user_ids)
    if not frames or frames[-1]["time"] != final_frame["time"]:
        if len(frames) >= MAX_FRAMES:
            frames[-1] = final_frame
        else:
            frames.append(final_frame)

    passed = result is True and error is None
    return {
        "language": "python",
        "challenge": challenge_number,
        "description": challenge["condition"]["description"],
        "scene": {
            "floorCount": len(world.floors),
            "floorHeight": world.floor_height,
            "elevatorCapacities": [elevator.max_users for elevator in world.elevators],
            "sampleEvery": sample_every,
        },
        "frames": frames,
        "result": {
            "passed": passed,
            "error": error,
            "elapsedTime": round(world.elapsed_time, 4),
            "transported": world.transported_counter,
            "moves": world.move_count,
            "maxWaitTime": round(world.max_wait_time, 4),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Record an Elevator Saga Python trace")
    parser.add_argument("--solution", required=True)
    parser.add_argument("--challenge", type=int, default=1)
    parser.add_argument("--output", required=True)
    parser.add_argument("--sample-every", type=float, default=DEFAULT_SAMPLE_EVERY)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    try:
        trace = record_trace(
            Path(args.solution).resolve(),
            args.challenge,
            sample_every=args.sample_every,
            seed=args.seed,
        )
    except Exception as exception:
        trace = {
            "language": "python",
            "challenge": args.challenge,
            "scene": {},
            "frames": [],
            "result": {"passed": False, "error": str(exception)},
        }

    Path(args.output).write_text(json.dumps(trace, ensure_ascii=False), encoding="utf-8")
    raise SystemExit(0 if trace.get("frames") else 1)


if __name__ == "__main__":
    main()
