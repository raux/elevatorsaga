package examples;

import elevatorsaga.*;
import java.util.List;

/**
 * Simple elevator strategy example.
 * Sends idle elevators to floors where buttons are pressed.
 */
public class SimpleStrategy implements ElevatorStrategy {
    @Override
    public void init(List<ElevatorInterface> elevators, List<Floor> floors) {
        for (ElevatorInterface elevator : elevators) {
            final ElevatorInterface elev = elevator;

            elev.on("idle", args -> {
                List<Integer> pressed = elev.getPressedFloors();
                if (!pressed.isEmpty()) {
                    elev.goToFloor(pressed.get(0));
                } else {
                    elev.goToFloor(0);
                }
            });

            elev.on("floor_button_pressed", args -> {
                int floorNum = (Integer) args[0];
                elev.goToFloor(floorNum);
            });

            elev.on("stopped_at_floor", args -> {
                // Can add logic here if needed
            });
        }
    }

    @Override
    public void update(double dt, List<ElevatorInterface> elevators, List<Floor> floors) {
        // Event-driven strategy - no polling needed
    }
}
