"""Challenge definitions for Elevator Saga."""


def require_user_count_within_time(user_count, time_limit):
    """Challenge: transport N people within time limit."""
    return {
        "description": f"Transport {user_count} people in {time_limit:.0f} seconds or less",
        "evaluate": lambda world: (
            None if world.elapsed_time < time_limit and world.transported_counter < user_count
            else world.elapsed_time <= time_limit and world.transported_counter >= user_count
        ),
    }


def require_user_count_with_max_wait_time(user_count, max_wait_time):
    """Challenge: transport N people with max individual wait time."""
    return {
        "description": f"Transport {user_count} people and let no one wait more than {max_wait_time:.1f} seconds",
        "evaluate": lambda world: (
            None if world.max_wait_time < max_wait_time and world.transported_counter < user_count
            else world.max_wait_time <= max_wait_time and world.transported_counter >= user_count
        ),
    }


def require_user_count_within_time_with_max_wait_time(user_count, time_limit, max_wait_time):
    """Challenge: transport N people within time with max wait."""
    return {
        "description": (
            f"Transport {user_count} people in {time_limit:.0f} seconds or less "
            f"and let no one wait more than {max_wait_time:.1f} seconds"
        ),
        "evaluate": lambda world: (
            None if (world.elapsed_time < time_limit and
                     world.max_wait_time < max_wait_time and
                     world.transported_counter < user_count)
            else (world.elapsed_time <= time_limit and
                  world.max_wait_time <= max_wait_time and
                  world.transported_counter >= user_count)
        ),
    }


def require_user_count_within_moves(user_count, move_limit):
    """Challenge: transport N people within move limit."""
    return {
        "description": f"Transport {user_count} people using {move_limit} elevator moves or less",
        "evaluate": lambda world: (
            None if world.move_count < move_limit and world.transported_counter < user_count
            else world.move_count <= move_limit and world.transported_counter >= user_count
        ),
    }


def require_demo():
    """Perpetual demo mode - never ends."""
    return {
        "description": "Perpetual demo",
        "evaluate": lambda world: None,
    }


CHALLENGES = [
    {"options": {"floor_count": 3, "elevator_count": 1, "spawn_rate": 0.3}, "condition": require_user_count_within_time(15, 60)},
    {"options": {"floor_count": 5, "elevator_count": 1, "spawn_rate": 0.4}, "condition": require_user_count_within_time(20, 60)},
    {"options": {"floor_count": 5, "elevator_count": 1, "spawn_rate": 0.5, "elevator_capacities": [6]}, "condition": require_user_count_within_time(23, 60)},
    {"options": {"floor_count": 8, "elevator_count": 2, "spawn_rate": 0.6}, "condition": require_user_count_within_time(28, 60)},
    {"options": {"floor_count": 6, "elevator_count": 4, "spawn_rate": 1.7}, "condition": require_user_count_within_time(100, 68)},
    {"options": {"floor_count": 4, "elevator_count": 2, "spawn_rate": 0.8}, "condition": require_user_count_within_moves(40, 60)},
    {"options": {"floor_count": 3, "elevator_count": 3, "spawn_rate": 3.0}, "condition": require_user_count_within_moves(100, 63)},
    {"options": {"floor_count": 6, "elevator_count": 2, "spawn_rate": 0.4, "elevator_capacities": [5]}, "condition": require_user_count_with_max_wait_time(50, 21)},
    {"options": {"floor_count": 7, "elevator_count": 3, "spawn_rate": 0.6}, "condition": require_user_count_with_max_wait_time(50, 20)},
    {"options": {"floor_count": 13, "elevator_count": 2, "spawn_rate": 1.1, "elevator_capacities": [4, 10]}, "condition": require_user_count_within_time(50, 70)},
    {"options": {"floor_count": 9, "elevator_count": 5, "spawn_rate": 1.1}, "condition": require_user_count_with_max_wait_time(60, 19)},
    {"options": {"floor_count": 9, "elevator_count": 5, "spawn_rate": 1.1}, "condition": require_user_count_with_max_wait_time(80, 17)},
    {"options": {"floor_count": 9, "elevator_count": 5, "spawn_rate": 1.1, "elevator_capacities": [5]}, "condition": require_user_count_with_max_wait_time(100, 15)},
    {"options": {"floor_count": 9, "elevator_count": 5, "spawn_rate": 1.0, "elevator_capacities": [6]}, "condition": require_user_count_with_max_wait_time(110, 15)},
    {"options": {"floor_count": 8, "elevator_count": 6, "spawn_rate": 0.9}, "condition": require_user_count_with_max_wait_time(120, 14)},
    {"options": {"floor_count": 12, "elevator_count": 4, "spawn_rate": 1.4, "elevator_capacities": [5, 10]}, "condition": require_user_count_within_time(70, 80)},
    {"options": {"floor_count": 21, "elevator_count": 5, "spawn_rate": 1.9, "elevator_capacities": [10]}, "condition": require_user_count_within_time(110, 80)},
    {"options": {"floor_count": 21, "elevator_count": 8, "spawn_rate": 1.5, "elevator_capacities": [6, 8]}, "condition": require_user_count_within_time_with_max_wait_time(2675, 1800, 45)},
    {"options": {"floor_count": 21, "elevator_count": 8, "spawn_rate": 1.5, "elevator_capacities": [6, 8]}, "condition": require_demo()},
]
