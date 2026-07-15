"""Elevator interface - facade exposed to player code with destination queue."""

from .observable import Observable
from .base import limit_number, epsilon_equals


class ElevatorInterface(Observable):
    """Player-facing elevator interface with destination queue management."""

    def __init__(self, elevator, floor_count, error_handler=None):
        super().__init__()
        self._elevator = elevator
        self._floor_count = floor_count
        self._error_handler = error_handler
        self.destination_queue = []

        # Set up event forwarding
        elevator.on("stopped", self._on_stopped)
        elevator.on("passing_floor", self._on_passing_floor)
        elevator.on("stopped_at_floor", self._on_stopped_at_floor)
        elevator.on("floor_button_pressed", self._on_floor_button_pressed)

    def _try_trigger(self, event, *args):
        """Trigger with error handling."""
        try:
            self.trigger(event, *args)
        except Exception as e:
            if self._error_handler:
                self._error_handler(e)

    def _on_stopped(self, position):
        if self.destination_queue and epsilon_equals(self.destination_queue[0], position):
            self.destination_queue = self.destination_queue[1:]
            if self._elevator.is_on_a_floor():
                self._elevator.wait(1, self.check_destination_queue)
            else:
                self.check_destination_queue()

    def _on_passing_floor(self, floor_num, direction):
        self._try_trigger("passing_floor", floor_num, direction)

    def _on_stopped_at_floor(self, floor_num):
        self._try_trigger("stopped_at_floor", floor_num)

    def _on_floor_button_pressed(self, floor_num):
        self._try_trigger("floor_button_pressed", floor_num)

    def check_destination_queue(self):
        """Process the next destination in queue or trigger idle."""
        if not self._elevator.is_busy():
            if self.destination_queue:
                self._elevator.go_to_floor(self.destination_queue[0])
            else:
                self._try_trigger("idle")

    def go_to_floor(self, floor_num, force_now=False):
        """Add a floor to the destination queue."""
        floor_num = limit_number(int(floor_num), 0, self._floor_count - 1)
        # Prevent duplicate adjacent destinations
        if self.destination_queue:
            adjacent = self.destination_queue[0] if force_now else self.destination_queue[-1]
            if epsilon_equals(floor_num, adjacent):
                return
        if force_now:
            self.destination_queue.insert(0, floor_num)
        else:
            self.destination_queue.append(floor_num)
        self.check_destination_queue()

    def stop(self):
        """Clear destination queue and stop."""
        self.destination_queue = []
        if not self._elevator.is_busy():
            self._elevator.go_to_floor(self._elevator.get_exact_future_floor_if_stopped())

    def get_pressed_floors(self):
        """Get list of pressed floor buttons."""
        return self._elevator.get_pressed_floors()

    def current_floor(self):
        """Get current floor number."""
        return self._elevator.current_floor

    def max_passenger_count(self):
        """Get maximum passenger capacity."""
        return self._elevator.max_users

    def load_factor(self):
        """Get current load factor."""
        return self._elevator.get_load_factor()

    def destination_direction(self):
        """Get current direction: 'up', 'down', or 'stopped'."""
        if self._elevator.destination_y == self._elevator.y:
            return "stopped"
        return "down" if self._elevator.destination_y > self._elevator.y else "up"

    def going_up_indicator(self, value=None):
        """Get or set the going-up indicator."""
        if value is not None:
            self._elevator.going_up_indicator = bool(value)
            self._elevator.trigger("change:goingUpIndicator", self._elevator.going_up_indicator)
            return self
        return self._elevator.going_up_indicator

    def going_down_indicator(self, value=None):
        """Get or set the going-down indicator."""
        if value is not None:
            self._elevator.going_down_indicator = bool(value)
            self._elevator.trigger("change:goingDownIndicator", self._elevator.going_down_indicator)
            return self
        return self._elevator.going_down_indicator
