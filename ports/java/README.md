# Elevator Saga - Java Edition

A Java port of [Elevator Saga](http://play.elevatorsaga.com/), the elevator programming game.

## Overview

Write Java code to control elevators and transport people efficiently! Your strategy implements the `ElevatorStrategy` interface, defining how elevators respond to events and the simulation evaluates performance against various challenges.

## Quick Start

### Build

```bash
mvn package
```

### Run

```bash
# Run challenge #1 with the example strategy
java -cp target/elevatorsaga-1.0.0.jar:examples elevatorsaga.Main --strategy examples.SimpleStrategy --challenge 1

# Run all challenges
java -cp target/elevatorsaga-1.0.0.jar:examples elevatorsaga.Main --strategy examples.SimpleStrategy --all

# Quiet mode
java -cp target/elevatorsaga-1.0.0.jar:examples elevatorsaga.Main -s examples.SimpleStrategy -c 1 -q
```

### Compile and run without Maven

```bash
# Compile
javac -d out src/main/java/elevatorsaga/*.java examples/SimpleStrategy.java

# Run
java -cp out elevatorsaga.Main --strategy examples.SimpleStrategy --challenge 1
```

## Writing a Strategy

Implement the `ElevatorStrategy` interface:

```java
package mystrategy;

import elevatorsaga.*;
import java.util.List;

public class MyStrategy implements ElevatorStrategy {
    @Override
    public void init(List<ElevatorInterface> elevators, List<Floor> floors) {
        for (ElevatorInterface elevator : elevators) {
            final ElevatorInterface elev = elevator;

            elev.on("idle", args -> {
                // Elevator has no destinations - decide where to go
                elev.goToFloor(0);
            });

            elev.on("floor_button_pressed", args -> {
                int floorNum = (Integer) args[0];
                elev.goToFloor(floorNum);
            });

            elev.on("stopped_at_floor", args -> {
                int floorNum = (Integer) args[0];
                // Elevator stopped at a floor
            });

            elev.on("passing_floor", args -> {
                int floorNum = (Integer) args[0];
                String direction = (String) args[1];
                // Elevator is passing a floor
            });
        }
    }

    @Override
    public void update(double dt, List<ElevatorInterface> elevators, List<Floor> floors) {
        // Called each tick - use for polling-based logic
    }
}
```

## ElevatorInterface API

| Method | Description |
|--------|-------------|
| `goToFloor(int n)` | Add floor to destination queue |
| `goToFloor(int n, true)` | Add floor to front of queue |
| `stop()` | Clear queue and stop |
| `currentFloor()` | Get current floor number |
| `getPressedFloors()` | List of pressed floor buttons |
| `maxPassengerCount()` | Max capacity |
| `loadFactor()` | Current load (0.0 to 1.0) |
| `destinationDirection()` | "up", "down", or "stopped" |
| `goingUpIndicator()` | Get up indicator state |
| `setGoingUpIndicator(bool)` | Set up indicator |
| `goingDownIndicator()` | Get down indicator state |
| `setGoingDownIndicator(bool)` | Set down indicator |
| `destinationQueue` | Current destination queue (List) |

### Elevator Events

| Event | Args | Description |
|-------|------|-------------|
| `"idle"` | - | No more destinations |
| `"floor_button_pressed"` | (Integer) floorNum | Passenger pressed button |
| `"stopped_at_floor"` | (Integer) floorNum | Arrived at floor |
| `"passing_floor"` | (Integer) floorNum, (String) direction | Passing a floor |

## Floor API

| Property/Method | Description |
|-----------------|-------------|
| `floor.level` | Floor number (0-indexed) |
| `floor.buttonUp` | Up button state ("" or "activated") |
| `floor.buttonDown` | Down button state ("" or "activated") |

### Floor Events

| Event | Args | Description |
|-------|------|-------------|
| `"up_button_pressed"` | (Floor) floor | Up button pressed |
| `"down_button_pressed"` | (Floor) floor | Down button pressed |

## Challenges

There are 18 challenges of increasing difficulty testing transport speed, efficiency, and responsiveness.

## Project Structure

```
src/main/java/elevatorsaga/
├── Base.java              # Math utilities
├── Observable.java        # Event system
├── Movable.java           # Movement base class
├── Elevator.java          # Elevator physics
├── Floor.java             # Floor logic
├── User.java              # Passenger logic
├── ElevatorInterface.java # Player-facing API
├── World.java             # World simulation
├── Challenge.java         # Challenge definitions
├── ElevatorStrategy.java  # Strategy interface
└── Main.java              # CLI entry point
```
