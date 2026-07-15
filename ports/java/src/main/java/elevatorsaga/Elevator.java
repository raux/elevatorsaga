package elevatorsaga;

import java.util.*;

/**
 * An elevator with physics simulation, capacity, and button states.
 */
public class Elevator extends Movable {
    public final double ACCELERATION;
    public final double DECELERATION;
    public final double MAXSPEED;
    public final int floorCount;
    public final double floorHeight;
    public final int maxUsers;
    public double destinationY = 0.0;
    public double velocityY = 0.0;
    public boolean isMoving = false;
    public boolean goingDownIndicator = true;
    public boolean goingUpIndicator = true;
    public int currentFloor = 0;
    private int previousTruncFutureFloorIfStopped = 0;
    public boolean[] buttonStates;
    public int moveCount = 0;
    public final int width;

    public static class UserSlot {
        public final int[] pos;
        public User user = null;

        public UserSlot(int x, int y) {
            this.pos = new int[]{x, y};
        }
    }

    public final UserSlot[] userSlots;

    public Elevator(double speedFloorsPerSec, int floorCount, double floorHeight, int maxUsers) {
        this.ACCELERATION = floorHeight * 2.1;
        this.DECELERATION = floorHeight * 2.6;
        this.MAXSPEED = floorHeight * speedFloorsPerSec;
        this.floorCount = floorCount;
        this.floorHeight = floorHeight;
        this.maxUsers = maxUsers;
        this.buttonStates = new boolean[floorCount];
        this.userSlots = new UserSlot[maxUsers];
        for (int i = 0; i < maxUsers; i++) {
            userSlots[i] = new UserSlot(2 + i * 10, 30);
        }
        this.width = maxUsers * 10;
        this.destinationY = getYPosOfFloor(currentFloor);

        on("new_state", args -> handleNewState());
    }

    public void setFloorPosition(int floor) {
        double destination = getYPosOfFloor(floor);
        this.currentFloor = floor;
        this.previousTruncFutureFloorIfStopped = floor;
        moveTo(null, destination);
    }

    public int[] userEntering(User user) {
        Random rand = new Random();
        int offset = rand.nextInt(userSlots.length);
        for (int i = 0; i < userSlots.length; i++) {
            UserSlot slot = userSlots[(i + offset) % userSlots.length];
            if (slot.user == null) {
                slot.user = user;
                return slot.pos;
            }
        }
        return null;
    }

    public void pressFloorButton(int floorNumber) {
        floorNumber = Base.limitNumber(floorNumber, 0, floorCount - 1);
        boolean prev = buttonStates[floorNumber];
        buttonStates[floorNumber] = true;
        if (!prev) {
            trigger("floor_button_pressed", floorNumber);
            trigger("floor_buttons_changed", buttonStates, floorNumber);
        }
    }

    public void userExiting(User user) {
        for (UserSlot slot : userSlots) {
            if (slot.user == user) {
                slot.user = null;
            }
        }
    }

    public void updateElevatorMovement(double dt) {
        if (isBusy()) return;

        velocityY = Base.limitNumber(velocityY, -MAXSPEED, MAXSPEED);
        moveTo(null, y + velocityY * dt);

        double destinationDiff = destinationY - y;
        int directionSign = Double.compare(destinationDiff, 0.0);
        int velocitySign = Double.compare(velocityY, 0.0);

        if (destinationDiff != 0.0) {
            if (directionSign == velocitySign) {
                double distanceNeeded = Base.distanceNeededToAchieveSpeed(velocityY, 0.0, DECELERATION);
                if (distanceNeeded * 1.05 < -Math.abs(destinationDiff)) {
                    double requiredDecel = Base.accelerationNeededToAchieveChangeDistance(velocityY, 0.0, destinationDiff);
                    double deceleration = Math.min(DECELERATION * 1.1, Math.abs(requiredDecel));
                    velocityY -= directionSign * deceleration * dt;
                } else {
                    double acceleration = Math.min(Math.abs(destinationDiff * 5), ACCELERATION);
                    velocityY += directionSign * acceleration * dt;
                }
            } else if (velocitySign == 0) {
                double acceleration = Math.min(Math.abs(destinationDiff * 5), ACCELERATION);
                velocityY += directionSign * acceleration * dt;
            } else {
                velocityY -= velocitySign * DECELERATION * dt;
                if (Double.compare(velocityY, 0.0) != velocitySign && velocitySign != 0) {
                    velocityY = 0.0;
                }
            }
        }

        if (isMoving && Math.abs(destinationDiff) < 0.5 && Math.abs(velocityY) < 3) {
            moveTo(null, destinationY);
            velocityY = 0.0;
            isMoving = false;
            handleDestinationArrival();
        }
    }

    private void handleDestinationArrival() {
        trigger("stopped", getExactCurrentFloor());
        if (isOnAFloor()) {
            buttonStates[currentFloor] = false;
            trigger("floor_buttons_changed", buttonStates, currentFloor);
            trigger("stopped_at_floor", currentFloor);
            trigger("exit_available", currentFloor, this);
            trigger("entrance_available", this);
        }
    }

    public void goToFloor(int floor) {
        makeSureNotBusy();
        isMoving = true;
        destinationY = getYPosOfFloor(floor);
    }

    public List<Integer> getPressedFloors() {
        List<Integer> result = new ArrayList<>();
        for (int i = 0; i < buttonStates.length; i++) {
            if (buttonStates[i]) result.add(i);
        }
        return result;
    }

    public boolean isSuitableForTravelBetween(int fromFloor, int toFloor) {
        if (fromFloor > toFloor) return goingDownIndicator;
        if (fromFloor < toFloor) return goingUpIndicator;
        return true;
    }

    public double getYPosOfFloor(int floorNum) {
        return (floorCount - 1) * floorHeight - floorNum * floorHeight;
    }

    public double getExactFloorOfYPos(double y) {
        return ((floorCount - 1) * floorHeight - y) / floorHeight;
    }

    public double getExactCurrentFloor() {
        return getExactFloorOfYPos(y);
    }

    public double getDestinationFloor() {
        return getExactFloorOfYPos(destinationY);
    }

    public int getRoundedCurrentFloor() {
        return (int) Math.round(getExactCurrentFloor());
    }

    public double getExactFutureFloorIfStopped() {
        double distanceNeeded = Base.distanceNeededToAchieveSpeed(velocityY, 0.0, DECELERATION);
        int sign = Double.compare(velocityY, 0.0);
        return getExactFloorOfYPos(y - sign * distanceNeeded);
    }

    public boolean isApproachingFloor(int floorNum) {
        double floorYPos = getYPosOfFloor(floorNum);
        double elevToFloor = floorYPos - y;
        return velocityY != 0.0 && (Double.compare(velocityY, 0.0) == Double.compare(elevToFloor, 0.0));
    }

    public boolean isOnAFloor() {
        return Base.epsilonEquals(getExactCurrentFloor(), getRoundedCurrentFloor());
    }

    public double getLoadFactor() {
        double load = 0;
        for (UserSlot slot : userSlots) {
            if (slot.user != null) load += slot.user.weight;
        }
        return load / (maxUsers * 100.0);
    }

    public boolean isFull() {
        for (UserSlot slot : userSlots) {
            if (slot.user == null) return false;
        }
        return true;
    }

    public boolean isEmpty() {
        for (UserSlot slot : userSlots) {
            if (slot.user != null) return false;
        }
        return true;
    }

    private void handleNewState() {
        int floor = getRoundedCurrentFloor();
        if (floor != currentFloor) {
            moveCount++;
            currentFloor = floor;
            trigger("new_current_floor", currentFloor);
        }

        int futureTrunc = (int) getExactFutureFloorIfStopped();
        if (futureTrunc != previousTruncFutureFloorIfStopped) {
            int floorBeingPassed = (int) Math.round(getExactFutureFloorIfStopped());
            if (getDestinationFloor() != floorBeingPassed && isApproachingFloor(floorBeingPassed)) {
                String direction = velocityY > 0.0 ? "down" : "up";
                trigger("passing_floor", floorBeingPassed, direction);
            }
        }
        previousTruncFutureFloorIfStopped = futureTrunc;
    }
}
