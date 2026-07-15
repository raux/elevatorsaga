package elevatorsaga;

import java.util.Random;

/**
 * A passenger that travels between floors.
 */
public class User extends Movable {
    public final double weight;
    public int currentFloor = 0;
    public int destinationFloor = 0;
    public boolean done = false;
    public boolean removeMe = false;
    public String displayType = "male";
    public double spawnTimestamp = 0.0;
    private Observable.EventListener exitAvailableHandler;

    public User(double weight) {
        this.weight = weight;
    }

    public void appearOnFloor(Floor floor, int destinationFloorNum) {
        double floorPosY = floor.getSpawnPosY();
        this.currentFloor = floor.level;
        this.destinationFloor = destinationFloorNum;
        moveTo(null, floorPosY);
        pressFloorButton(floor);
    }

    private void pressFloorButton(Floor floor) {
        if (destinationFloor < currentFloor) {
            floor.pressDownButton();
        } else {
            floor.pressUpButton();
        }
    }

    private void handleExit(int floorNum, Elevator elevator) {
        if (elevator.currentFloor == destinationFloor) {
            elevator.userExiting(this);
            currentFloor = elevator.currentFloor;
            setParent(null);
            double destination = x + 100;
            done = true;
            trigger("exited_elevator", elevator);
            trigger("new_state");
            trigger("new_display_state");

            Random rand = new Random();
            moveToOverTime(destination, null, 1 + rand.nextDouble() * 0.5, Base::linearInterpolate, () -> {
                removeMe = true;
                trigger("removed");
                off("*");
            });

            elevator.off("exit_available", exitAvailableHandler);
        }
    }

    public void elevatorAvailable(Elevator elevator, Floor floor) {
        if (done || parent != null || isBusy()) return;
        if (!elevator.isSuitableForTravelBetween(currentFloor, destinationFloor)) return;

        int[] pos = elevator.userEntering(this);
        if (pos != null) {
            setParent(elevator);
            trigger("entered_elevator", elevator);

            final User self = this;
            moveToOverTime((double) pos[0], (double) pos[1], 1, null, () -> {
                elevator.pressFloorButton(self.destinationFloor);
            });

            exitAvailableHandler = (args) -> {
                Elevator elev = (Elevator) args[1];
                self.handleExit(elev.currentFloor, elev);
            };
            elevator.on("exit_available", exitAvailableHandler);
        } else {
            pressFloorButton(floor);
        }
    }
}
