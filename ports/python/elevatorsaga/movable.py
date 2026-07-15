"""Movable base class for objects with position and movement."""

from .observable import Observable
from .base import DEFAULT_INTERPOLATOR


class Movable(Observable):
    """Base class for anything that can move in the world."""

    def __init__(self):
        super().__init__()
        self.x = 0.0
        self.y = 0.0
        self.parent = None
        self.world_x = 0.0
        self.world_y = 0.0
        self.current_task = None
        self.trigger("new_state", self)

    def update_display_position(self, force_trigger=False):
        """Update world position and trigger display event if changed."""
        pos = self.get_world_position()
        old_x, old_y = self.world_x, self.world_y
        self.world_x, self.world_y = pos
        if old_x != self.world_x or old_y != self.world_y or force_trigger:
            self.trigger("new_display_state", self)

    def move_to(self, new_x, new_y):
        """Move to a new position immediately."""
        if new_x is not None:
            self.x = new_x
        if new_y is not None:
            self.y = new_y
        self.trigger("new_state", self)

    def move_to_fast(self, new_x, new_y):
        """Move to position without null checks."""
        self.x = new_x
        self.y = new_y
        self.trigger("new_state", self)

    def is_busy(self):
        """Check if currently performing a task."""
        return self.current_task is not None

    def make_sure_not_busy(self):
        """Raise error if busy."""
        if self.is_busy():
            raise RuntimeError("Object is busy - you should use callback")

    def wait(self, millis, cb=None):
        """Wait for a duration then call callback."""
        self.make_sure_not_busy()
        time_spent = [0.0]

        def wait_task(dt):
            time_spent[0] += dt
            if time_spent[0] > millis:
                self.current_task = None
                if cb:
                    cb()

        self.current_task = wait_task

    def move_to_over_time(self, new_x, new_y, time_to_spend, interpolator=None, cb=None):
        """Move to position over time using interpolation."""
        self.make_sure_not_busy()
        if new_x is None:
            new_x = self.x
        if new_y is None:
            new_y = self.y
        if interpolator is None:
            interpolator = DEFAULT_INTERPOLATOR
        orig_x = self.x
        orig_y = self.y
        time_spent = [0.0]

        def move_task(dt):
            time_spent[0] = min(time_to_spend, time_spent[0] + dt)
            if time_spent[0] == time_to_spend:
                self.move_to_fast(new_x, new_y)
                self.current_task = None
                if cb:
                    cb()
            else:
                factor = time_spent[0] / time_to_spend
                self.move_to_fast(
                    interpolator(orig_x, new_x, factor),
                    interpolator(orig_y, new_y, factor),
                )

        self.current_task = move_task

    def update(self, dt):
        """Update the current task."""
        if self.current_task is not None:
            self.current_task(dt)

    def get_world_position(self):
        """Get absolute world position traversing parent chain."""
        result_x = self.x
        result_y = self.y
        current_parent = self.parent
        while current_parent is not None:
            result_x += current_parent.x
            result_y += current_parent.y
            current_parent = current_parent.parent
        return (result_x, result_y)

    def set_parent(self, movable_parent):
        """Set or clear the parent movable."""
        if movable_parent is None:
            if self.parent is not None:
                obj_world = self.get_world_position()
                self.parent = None
                self.move_to_fast(obj_world[0], obj_world[1])
        else:
            obj_world = self.get_world_position()
            parent_world = movable_parent.get_world_position()
            self.parent = movable_parent
            self.move_to_fast(obj_world[0] - parent_world[0], obj_world[1] - parent_world[1])
