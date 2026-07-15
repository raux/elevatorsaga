# Elevator Saga - Python Edition

A Python port of [Elevator Saga](http://play.elevatorsaga.com/), the elevator programming game.

## Overview

Write Python code to control elevators and transport people efficiently! Your solution defines how elevators respond to events (people pressing buttons, arriving at floors, etc.) and the simulation evaluates your strategy against various challenges.

## Quick Start

```bash
# Run challenge #1 with the example solution
python -m elevatorsaga --challenge 1 --solution examples/simple_solution.py

# Run all challenges
python -m elevatorsaga --all --solution examples/simple_solution.py

# Quiet mode (less output)
python -m elevatorsaga -c 1 -s my_solution.py -q
```

## Writing a Solution

Your solution file must define two functions:

```python
def init(elevators, floors):
    """Called once at the start. Set up your event handlers here."""
    for elevator in elevators:
        def make_handlers(elev):
            def on_idle():
                # Elevator has no destinations - decide where to go
                elev.go_to_floor(0)

            def on_floor_button_pressed(floor_num):
                # Someone inside pressed a floor button
                elev.go_to_floor(floor_num)

            def on_stopped_at_floor(floor_num):
                # Elevator stopped at a floor
                pass

            def on_passing_floor(floor_num, direction):
                # Elevator is passing a floor without stopping
                pass

            elev.on("idle", on_idle)
            elev.on("floor_button_pressed", on_floor_button_pressed)
            elev.on("stopped_at_floor", on_stopped_at_floor)
            elev.on("passing_floor", on_passing_floor)

        make_handlers(elevator)


def update(dt, elevators, floors):
    """Called each simulation tick. Use for polling-based logic."""
    pass
```

## Elevator API

Each elevator interface provides:

| Method | Description |
|--------|-------------|
| `elevator.go_to_floor(n)` | Add floor to destination queue |
| `elevator.go_to_floor(n, True)` | Add floor to front of queue |
| `elevator.stop()` | Clear queue and stop |
| `elevator.current_floor()` | Get current floor number |
| `elevator.get_pressed_floors()` | List of pressed floor buttons |
| `elevator.max_passenger_count()` | Max capacity |
| `elevator.load_factor()` | Current load (0.0 to 1.0) |
| `elevator.destination_direction()` | "up", "down", or "stopped" |
| `elevator.going_up_indicator(val)` | Get/set up indicator |
| `elevator.going_down_indicator(val)` | Get/set down indicator |
| `elevator.destination_queue` | Current destination queue (list) |

### Elevator Events

| Event | Args | Description |
|-------|------|-------------|
| `"idle"` | - | No more destinations |
| `"floor_button_pressed"` | floor_num | Passenger pressed button |
| `"stopped_at_floor"` | floor_num | Arrived at floor |
| `"passing_floor"` | floor_num, direction | Passing a floor |

## Floor API

Each floor provides:

| Property | Description |
|----------|-------------|
| `floor.level` | Floor number (0-indexed) |
| `floor.button_states` | Dict with "up" and "down" states |

### Floor Events

| Event | Args | Description |
|-------|------|-------------|
| `"up_button_pressed"` | floor | Up button pressed |
| `"down_button_pressed"` | floor | Down button pressed |

## Challenges

There are 18 challenges of increasing difficulty, testing:
- Transport speed (people per second)
- Efficiency (minimum elevator moves)
- Responsiveness (maximum wait time)
- Combinations of the above

## Project Structure

```
elevatorsaga/
├── __init__.py      # Package init
├── __main__.py      # CLI entry point
├── base.py          # Math utilities
├── observable.py    # Event system
├── movable.py       # Movement base class
├── elevator.py      # Elevator physics
├── floor.py         # Floor logic
├── user.py          # Passenger logic
├── interfaces.py    # Player-facing API
├── world.py         # World simulation
└── challenges.py    # Challenge definitions
```
