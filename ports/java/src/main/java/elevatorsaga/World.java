package elevatorsaga;

import java.util.*;

/**
 * The game world containing elevators, floors, and users.
 */
public class World extends Observable {
    public final double floorHeight;
    public int transportedCounter = 0;
    public double transportedPerSec = 0.0;
    public int moveCount = 0;
    public double elapsedTime = 0.0;
    public double maxWaitTime = 0.0;
    public double avgWaitTime = 0.0;
    public boolean challengeEnded = false;
    public List<User> users = new ArrayList<>();
    public List<Floor> floors;
    public List<Elevator> elevators;
    public List<ElevatorInterface> elevatorInterfaces;

    private final double spawnRate;
    private double elapsedSinceSpawn;
    private final int floorCount;
    private final Random random = new Random();

    public World(Map<String, Object> options) {
        Map<String, Object> defaults = new HashMap<>();
        defaults.put("floor_height", 50.0);
        defaults.put("floor_count", 4);
        defaults.put("elevator_count", 2);
        defaults.put("spawn_rate", 0.5);
        defaults.put("elevator_capacities", new int[]{4});

        if (options != null) defaults.putAll(options);

        this.floorHeight = ((Number) defaults.get("floor_height")).doubleValue();
        this.floorCount = ((Number) defaults.get("floor_count")).intValue();
        int elevatorCount = ((Number) defaults.get("elevator_count")).intValue();
        this.spawnRate = ((Number) defaults.get("spawn_rate")).doubleValue();
        int[] elevatorCapacities = (int[]) defaults.get("elevator_capacities");
        this.elapsedSinceSpawn = 1.001 / spawnRate;

        Floor.ErrorHandler errorHandler = e -> trigger("usercode_error", e);

        // Create floors
        floors = new ArrayList<>();
        for (int i = 0; i < floorCount; i++) {
            double yPos = (floorCount - 1 - i) * floorHeight;
            floors.add(new Floor(i, yPos, errorHandler));
        }

        // Create elevators
        elevators = new ArrayList<>();
        double currentX = 200.0;
        for (int i = 0; i < elevatorCount; i++) {
            int cap = elevatorCapacities[i % elevatorCapacities.length];
            Elevator elevator = new Elevator(2.6, floorCount, floorHeight, cap);
            elevator.moveTo(currentX, null);
            elevator.setFloorPosition(0);
            elevator.updateDisplayPosition();
            currentX += 20 + elevator.width;
            elevators.add(elevator);
        }

        // Create interfaces
        elevatorInterfaces = new ArrayList<>();
        for (Elevator e : elevators) {
            elevatorInterfaces.add(new ElevatorInterface(e, floorCount, errorHandler));
        }

        // Bind elevator entrance events
        for (Elevator elevator : elevators) {
            elevator.on("entrance_available", args -> handleElevAvailability((Elevator) args[0]));
        }

        // Bind floor button repressing
        for (Floor floor : floors) {
            floor.on("up_button_pressed", args -> handleButtonRepressing("up_button_pressed", (Floor) args[0]));
            floor.on("down_button_pressed", args -> handleButtonRepressing("down_button_pressed", (Floor) args[0]));
        }
    }

    private void handleElevAvailability(Elevator elevator) {
        for (int i = 0; i < floors.size(); i++) {
            if (elevator.currentFloor == i) {
                floors.get(i).elevatorAvailable(elevator);
            }
        }
        for (User user : new ArrayList<>(users)) {
            if (user.currentFloor == elevator.currentFloor) {
                user.elevatorAvailable(elevator, floors.get(elevator.currentFloor));
            }
        }
    }

    private void handleButtonRepressing(String eventName, Floor floor) {
        int offset = random.nextInt(elevators.size());
        for (int i = 0; i < elevators.size(); i++) {
            int elevIndex = (i + offset) % elevators.size();
            Elevator elevator = elevators.get(elevIndex);
            if ((eventName.equals("up_button_pressed") && elevator.goingUpIndicator) ||
                (eventName.equals("down_button_pressed") && elevator.goingDownIndicator)) {
                if (elevator.currentFloor == floor.level && elevator.isOnAFloor() &&
                    !elevator.isMoving && !elevator.isFull()) {
                    elevatorInterfaces.get(elevIndex).goToFloor(floor.level, true);
                    return;
                }
            }
        }
    }

    private void recalculateStats() {
        if (elapsedTime > 0) {
            transportedPerSec = transportedCounter / elapsedTime;
        }
        moveCount = 0;
        for (Elevator e : elevators) moveCount += e.moveCount;
        trigger("stats_changed");
    }

    private void registerUser(User user) {
        users.add(user);
        user.updateDisplayPosition(true);
        user.spawnTimestamp = elapsedTime;
        trigger("new_user", user);

        user.on("exited_elevator", args -> {
            transportedCounter++;
            maxWaitTime = Math.max(maxWaitTime, elapsedTime - user.spawnTimestamp);
            avgWaitTime = (avgWaitTime * (transportedCounter - 1) + (elapsedTime - user.spawnTimestamp)) / transportedCounter;
            recalculateStats();
        });
        user.updateDisplayPosition(true);
    }

    private User spawnUserRandomly() {
        double weight = 55 + random.nextInt(46);
        User user = new User(weight);
        if (random.nextInt(41) == 0) {
            user.displayType = "child";
        } else if (random.nextInt(2) == 0) {
            user.displayType = "female";
        } else {
            user.displayType = "male";
        }

        user.moveTo(105.0 + random.nextInt(41), null);
        int currentFloor = random.nextInt(2) == 0 ? 0 : random.nextInt(floorCount);
        int destinationFloor;
        if (currentFloor == 0) {
            destinationFloor = 1 + random.nextInt(floorCount - 1);
        } else {
            if (random.nextInt(11) == 0) {
                destinationFloor = (currentFloor + 1 + random.nextInt(floorCount - 1)) % floorCount;
            } else {
                destinationFloor = 0;
            }
        }
        user.appearOnFloor(floors.get(currentFloor), destinationFloor);
        return user;
    }

    public void update(double dt) {
        elapsedTime += dt;
        elapsedSinceSpawn += dt;

        while (elapsedSinceSpawn > 1.0 / spawnRate) {
            elapsedSinceSpawn -= 1.0 / spawnRate;
            registerUser(spawnUserRandomly());
        }

        for (Elevator e : elevators) {
            e.update(dt);
            e.updateElevatorMovement(dt);
        }

        for (User u : new ArrayList<>(users)) {
            u.update(dt);
            maxWaitTime = Math.max(maxWaitTime, elapsedTime - u.spawnTimestamp);
        }

        users.removeIf(u -> u.removeMe);
        recalculateStats();
    }

    public void init() {
        for (ElevatorInterface ei : elevatorInterfaces) {
            ei.checkDestinationQueue();
        }
    }

    public void unwind() {
        for (Observable obj : new ArrayList<>(elevators)) obj.off("*");
        for (Observable obj : new ArrayList<>(elevatorInterfaces)) obj.off("*");
        for (Observable obj : new ArrayList<>(users)) obj.off("*");
        for (Observable obj : new ArrayList<>(floors)) obj.off("*");
        off("*");
        challengeEnded = true;
        elevators = new ArrayList<>();
        elevatorInterfaces = new ArrayList<>();
        users = new ArrayList<>();
        floors = new ArrayList<>();
    }
}
