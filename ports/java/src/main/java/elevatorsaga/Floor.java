package elevatorsaga;

/**
 * A floor in the building with up/down call buttons.
 */
public class Floor extends Observable {
    public final int level;
    public final double yPosition;
    public String buttonUp = "";
    public String buttonDown = "";
    private final ErrorHandler errorHandler;

    @FunctionalInterface
    public interface ErrorHandler {
        void handle(Exception e);
    }

    public Floor(int level, double yPosition, ErrorHandler errorHandler) {
        this.level = level;
        this.yPosition = yPosition;
        this.errorHandler = errorHandler;
    }

    private void tryTrigger(String event, Object... args) {
        try {
            trigger(event, args);
        } catch (Exception e) {
            if (errorHandler != null) errorHandler.handle(e);
        }
    }

    public void pressUpButton() {
        String prev = buttonUp;
        buttonUp = "activated";
        if (!prev.equals(buttonUp)) {
            tryTrigger("buttonstate_change");
            tryTrigger("up_button_pressed", this);
        }
    }

    public void pressDownButton() {
        String prev = buttonDown;
        buttonDown = "activated";
        if (!prev.equals(buttonDown)) {
            tryTrigger("buttonstate_change");
            tryTrigger("down_button_pressed", this);
        }
    }

    public void elevatorAvailable(Elevator elevator) {
        if (elevator.goingUpIndicator && !buttonUp.isEmpty()) {
            buttonUp = "";
            tryTrigger("buttonstate_change");
        }
        if (elevator.goingDownIndicator && !buttonDown.isEmpty()) {
            buttonDown = "";
            tryTrigger("buttonstate_change");
        }
    }

    public double getSpawnPosY() {
        return yPosition + 30;
    }

    public int floorNum() {
        return level;
    }
}
