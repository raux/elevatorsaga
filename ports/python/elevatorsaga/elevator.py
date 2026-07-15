"""Elevator class with physics-based movement."""

import math
from .movable import Movable
from .base import limit_number, epsilon_equals, distance_needed_to_achieve_speed, acceleration_needed_to_achieve_change_distance


class Elevator(Movable):
    """An elevator with physics simulation, capacity, and button states."""

    def __init__(self, speed_floors_per_sec, floor_count, floor_height, max_users=4):
        super().__init__()
        self.ACCELERATION = floor_height * 2.1
        self.DECELERATION = floor_height * 2.6
        self.MAXSPEED = floor_height * speed_floors_per_sec
        self.floor_count = floor_count
        self.floor_height = floor_height
        self.max_users = max_users
        self.destination_y = 0.0
        self.velocity_y = 0.0
        self.is_moving = False

        self.going_down_indicator = True
        self.going_up_indicator = True

        self.current_floor = 0
        self.previous_trunc_future_floor_if_stopped = 0
        self.button_states = [False] * floor_count
        self.move_count = 0
        self.removed = False
        self.user_slots = [{"pos": [2 + (i * 10), 30], "user": None} for i in range(max_users)]
        self.width = max_users * 10
        self.destination_y = self.get_y_pos_of_floor(self.current_floor)

        self.on("new_state", self._handle_new_state)

    def set_floor_position(self, floor):
        """Set elevator to exact floor position."""
        destination = self.get_y_pos_of_floor(floor)
        self.current_floor = floor
        self.previous_trunc_future_floor_if_stopped = floor
        self.move_to(None, destination)

    def user_entering(self, user):
        """Try to add a user to the elevator. Returns slot position or False."""
        import random
        offset = random.randint(0, len(self.user_slots) - 1)
        for i in range(len(self.user_slots)):
            slot = self.user_slots[(i + offset) % len(self.user_slots)]
            if slot["user"] is None:
                slot["user"] = user
                return slot["pos"]
        return False

    def press_floor_button(self, floor_number):
        """Press a floor button inside the elevator."""
        floor_number = limit_number(floor_number, 0, self.floor_count - 1)
        prev = self.button_states[floor_number]
        self.button_states[floor_number] = True
        if not prev:
            self.trigger("floor_button_pressed", floor_number)
            self.trigger("floor_buttons_changed", self.button_states, floor_number)

    def user_exiting(self, user):
        """Remove a user from the elevator."""
        for slot in self.user_slots:
            if slot["user"] is user:
                slot["user"] = None

    def update_elevator_movement(self, dt):
        """Update elevator physics for one time step."""
        if self.is_busy():
            return

        # Clamp velocity
        self.velocity_y = limit_number(self.velocity_y, -self.MAXSPEED, self.MAXSPEED)

        # Move elevator
        self.move_to(None, self.y + self.velocity_y * dt)

        destination_diff = self.destination_y - self.y
        direction_sign = (1 if destination_diff > 0 else -1 if destination_diff < 0 else 0)
        velocity_sign = (1 if self.velocity_y > 0 else -1 if self.velocity_y < 0 else 0)

        if destination_diff != 0.0:
            if direction_sign == velocity_sign:
                # Moving in correct direction
                distance_needed = distance_needed_to_achieve_speed(self.velocity_y, 0.0, self.DECELERATION)
                if distance_needed * 1.05 < -abs(destination_diff):
                    # Slow down
                    required_decel = acceleration_needed_to_achieve_change_distance(
                        self.velocity_y, 0.0, destination_diff
                    )
                    deceleration = min(self.DECELERATION * 1.1, abs(required_decel))
                    self.velocity_y -= direction_sign * deceleration * dt
                else:
                    # Speed up
                    acceleration = min(abs(destination_diff * 5), self.ACCELERATION)
                    self.velocity_y += direction_sign * acceleration * dt
            elif velocity_sign == 0:
                # Standing still - accelerate
                acceleration = min(abs(destination_diff * 5), self.ACCELERATION)
                self.velocity_y += direction_sign * acceleration * dt
            else:
                # Moving wrong direction - decelerate
                self.velocity_y -= velocity_sign * self.DECELERATION * dt
                if (1 if self.velocity_y > 0 else -1 if self.velocity_y < 0 else 0) != velocity_sign:
                    self.velocity_y = 0.0

        if self.is_moving and abs(destination_diff) < 0.5 and abs(self.velocity_y) < 3:
            # Snap to destination
            self.move_to(None, self.destination_y)
            self.velocity_y = 0.0
            self.is_moving = False
            self._handle_destination_arrival()

    def _handle_destination_arrival(self):
        """Handle elevator arriving at destination."""
        self.trigger("stopped", self.get_exact_current_floor())
        if self.is_on_a_floor():
            self.button_states[self.current_floor] = False
            self.trigger("floor_buttons_changed", self.button_states, self.current_floor)
            self.trigger("stopped_at_floor", self.current_floor)
            self.trigger("exit_available", self.current_floor, self)
            self.trigger("entrance_available", self)

    def go_to_floor(self, floor):
        """Start moving to a floor."""
        self.make_sure_not_busy()
        self.is_moving = True
        self.destination_y = self.get_y_pos_of_floor(floor)

    def get_pressed_floors(self):
        """Get list of floors with pressed buttons."""
        return [i for i, pressed in enumerate(self.button_states) if pressed]

    def is_suitable_for_travel_between(self, from_floor, to_floor):
        """Check if elevator indicators match travel direction."""
        if from_floor > to_floor:
            return self.going_down_indicator
        if from_floor < to_floor:
            return self.going_up_indicator
        return True

    def get_y_pos_of_floor(self, floor_num):
        """Get Y position of a floor."""
        return (self.floor_count - 1) * self.floor_height - floor_num * self.floor_height

    def get_exact_floor_of_y_pos(self, y):
        """Get exact floor number for a Y position."""
        return ((self.floor_count - 1) * self.floor_height - y) / self.floor_height

    def get_exact_current_floor(self):
        """Get exact current floor (may be between floors)."""
        return self.get_exact_floor_of_y_pos(self.y)

    def get_destination_floor(self):
        """Get the destination floor."""
        return self.get_exact_floor_of_y_pos(self.destination_y)

    def get_rounded_current_floor(self):
        """Get nearest floor number."""
        return round(self.get_exact_current_floor())

    def get_exact_future_floor_if_stopped(self):
        """Get floor where elevator would end up if it started stopping now."""
        distance_needed = distance_needed_to_achieve_speed(self.velocity_y, 0.0, self.DECELERATION)
        sign = 1 if self.velocity_y > 0 else -1 if self.velocity_y < 0 else 0
        return self.get_exact_floor_of_y_pos(self.y - sign * distance_needed)

    def is_approaching_floor(self, floor_num):
        """Check if elevator is approaching a specific floor."""
        floor_y_pos = self.get_y_pos_of_floor(floor_num)
        elev_to_floor = floor_y_pos - self.y
        sign_elev = 1 if elev_to_floor > 0 else -1 if elev_to_floor < 0 else 0
        sign_vel = 1 if self.velocity_y > 0 else -1 if self.velocity_y < 0 else 0
        return self.velocity_y != 0.0 and sign_vel == sign_elev

    def is_on_a_floor(self):
        """Check if elevator is exactly at a floor."""
        return epsilon_equals(self.get_exact_current_floor(), self.get_rounded_current_floor())

    def get_load_factor(self):
        """Get load factor (0.0 to 1.0+)."""
        load = sum(slot["user"].weight for slot in self.user_slots if slot["user"] is not None)
        return load / (self.max_users * 100)

    def is_full(self):
        """Check if all slots are occupied."""
        return all(slot["user"] is not None for slot in self.user_slots)

    def is_empty(self):
        """Check if no slots are occupied."""
        return all(slot["user"] is None for slot in self.user_slots)

    def _handle_new_state(self, *args):
        """Handle state changes - recalculate floor and detect passing."""
        current_floor = self.get_rounded_current_floor()
        if current_floor != self.current_floor:
            self.move_count += 1
            self.current_floor = current_floor
            self.trigger("new_current_floor", self.current_floor)

        future_trunc = math.trunc(self.get_exact_future_floor_if_stopped())
        if future_trunc != self.previous_trunc_future_floor_if_stopped:
            floor_being_passed = round(self.get_exact_future_floor_if_stopped())
            if self.get_destination_floor() != floor_being_passed and self.is_approaching_floor(floor_being_passed):
                direction = "down" if self.velocity_y > 0.0 else "up"
                self.trigger("passing_floor", floor_being_passed, direction)
        self.previous_trunc_future_floor_if_stopped = future_trunc
