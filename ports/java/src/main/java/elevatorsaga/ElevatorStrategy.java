package elevatorsaga;

import java.util.List;

/**
 * Interface for player-defined elevator strategies.
 * Implement this interface to create your elevator control logic.
 */
public interface ElevatorStrategy {
    /**
     * Called once at the start of the simulation.
     * Set up event handlers on elevators and floors here.
     */
    void init(List<ElevatorInterface> elevators, List<Floor> floors);

    /**
     * Called each simulation tick.
     * Use for polling-based logic (optional - can be empty for event-driven strategies).
     */
    void update(double dt, List<ElevatorInterface> elevators, List<Floor> floors);
}
