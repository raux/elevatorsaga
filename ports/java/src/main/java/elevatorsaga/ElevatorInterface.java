package elevatorsaga;

import java.util.*;

/**
 * Player-facing elevator interface with destination queue management.
 */
public class ElevatorInterface extends Observable {
    private final Elevator elevator;
    private final int floorCount;
    private final Floor.ErrorHandler errorHandler;
    public List<Integer> destinationQueue = new ArrayList<>();

    public ElevatorInterface(Elevator elevator, int floorCount, Floor.ErrorHandler errorHandler) {
        this.elevator = elevator;
        this.floorCount = floorCount;
        this.errorHandler = errorHandler;

        elevator.on("stopped", args -> onStopped((Double) args[0]));
        elevator.on("passing_floor", args -> tryTrigger("passing_floor", args));
        elevator.on("stopped_at_floor", args -> tryTrigger("stopped_at_floor", args));
        elevator.on("floor_button_pressed", args -> tryTrigger("floor_button_pressed", args));
    }

    private void tryTrigger(String event, Object... args) {
        try {
            trigger(event, args);
        } catch (Exception e) {
            if (errorHandler != null) errorHandler.handle(e);
        }
    }

    private void onStopped(double position) {
        if (!destinationQueue.isEmpty() && Base.epsilonEquals(destinationQueue.get(0), position)) {
            destinationQueue.remove(0);
            if (elevator.isOnAFloor()) {
                elevator.wait(1, this::checkDestinationQueue);
            } else {
                checkDestinationQueue();
            }
        }
    }

    public void checkDestinationQueue() {
        if (!elevator.isBusy()) {
            if (!destinationQueue.isEmpty()) {
                elevator.goToFloor(destinationQueue.get(0));
            } else {
                tryTrigger("idle");
            }
        }
    }

    public void goToFloor(int floorNum, boolean forceNow) {
        floorNum = Base.limitNumber(floorNum, 0, floorCount - 1);
        if (!destinationQueue.isEmpty()) {
            int adjacent = forceNow ? destinationQueue.get(0) : destinationQueue.get(destinationQueue.size() - 1);
            if (Base.epsilonEquals(floorNum, adjacent)) return;
        }
        if (forceNow) {
            destinationQueue.add(0, floorNum);
        } else {
            destinationQueue.add(floorNum);
        }
        checkDestinationQueue();
    }

    public void goToFloor(int floorNum) {
        goToFloor(floorNum, false);
    }

    public void stop() {
        destinationQueue.clear();
        if (!elevator.isBusy()) {
            elevator.goToFloor((int) elevator.getExactFutureFloorIfStopped());
        }
    }

    public List<Integer> getPressedFloors() {
        return elevator.getPressedFloors();
    }

    public int currentFloor() {
        return elevator.currentFloor;
    }

    public int maxPassengerCount() {
        return elevator.maxUsers;
    }

    public double loadFactor() {
        return elevator.getLoadFactor();
    }

    public String destinationDirection() {
        if (elevator.destinationY == elevator.y) return "stopped";
        return elevator.destinationY > elevator.y ? "down" : "up";
    }

    public boolean goingUpIndicator() {
        return elevator.goingUpIndicator;
    }

    public void setGoingUpIndicator(boolean value) {
        elevator.goingUpIndicator = value;
        elevator.trigger("change:goingUpIndicator", value);
    }

    public boolean goingDownIndicator() {
        return elevator.goingDownIndicator;
    }

    public void setGoingDownIndicator(boolean value) {
        elevator.goingDownIndicator = value;
        elevator.trigger("change:goingDownIndicator", value);
    }
}
