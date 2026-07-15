"""User (passenger) class."""

import random
from .movable import Movable
from .base import linear_interpolate


class User(Movable):
    """A passenger that travels between floors."""

    def __init__(self, weight):
        super().__init__()
        self.weight = weight
        self.current_floor = 0
        self.destination_floor = 0
        self.done = False
        self.remove_me = False
        self.display_type = "male"
        self.spawn_timestamp = 0.0
        self._exit_available_handler = None

    def appear_on_floor(self, floor, destination_floor_num):
        """Place user on a floor with a destination."""
        floor_pos_y = floor.get_spawn_pos_y()
        self.current_floor = floor.level
        self.destination_floor = destination_floor_num
        self.move_to(None, floor_pos_y)
        self._press_floor_button(floor)

    def _press_floor_button(self, floor):
        """Press the appropriate button on the floor."""
        if self.destination_floor < self.current_floor:
            floor.press_down_button()
        else:
            floor.press_up_button()

    def _handle_exit(self, floor_num, elevator):
        """Handle exiting an elevator."""
        if elevator.current_floor == self.destination_floor:
            elevator.user_exiting(self)
            self.current_floor = elevator.current_floor
            self.set_parent(None)
            destination = self.x + 100
            self.done = True
            self.trigger("exited_elevator", elevator)
            self.trigger("new_state")
            self.trigger("new_display_state")

            def last_move():
                self.remove_me = True
                self.trigger("removed")
                self.off("*")

            self.move_to_over_time(destination, None, 1 + random.random() * 0.5, linear_interpolate, last_move)
            elevator.off("exit_available", self._exit_available_handler)

    def elevator_available(self, elevator, floor):
        """Called when an elevator is available on the user's floor."""
        if self.done or self.parent is not None or self.is_busy():
            return

        if not elevator.is_suitable_for_travel_between(self.current_floor, self.destination_floor):
            return

        pos = elevator.user_entering(self)
        if pos:
            self.set_parent(elevator)
            self.trigger("entered_elevator", elevator)

            def on_entered():
                elevator.press_floor_button(self.destination_floor)

            self.move_to_over_time(pos[0], pos[1], 1, None, on_entered)

            def exit_handler(floor_num, elev):
                self._handle_exit(elev.current_floor, elev)

            self._exit_available_handler = exit_handler
            elevator.on("exit_available", self._exit_available_handler)
        else:
            self._press_floor_button(floor)
