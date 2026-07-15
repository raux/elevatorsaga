"""Floor class representing a building floor."""

from .observable import Observable


class Floor(Observable):
    """A floor in the building with up/down call buttons."""

    def __init__(self, level, y_position, error_handler=None):
        super().__init__()
        self.level = level
        self.y_position = y_position
        self.button_states = {"up": "", "down": ""}
        self._error_handler = error_handler

    def _try_trigger(self, event, *args):
        """Trigger event with error handling."""
        try:
            self.trigger(event, *args)
        except Exception as e:
            if self._error_handler:
                self._error_handler(e)

    def press_up_button(self):
        """Press the up button on this floor."""
        prev = self.button_states["up"]
        self.button_states["up"] = "activated"
        if prev != self.button_states["up"]:
            self._try_trigger("buttonstate_change", self.button_states)
            self._try_trigger("up_button_pressed", self)

    def press_down_button(self):
        """Press the down button on this floor."""
        prev = self.button_states["down"]
        self.button_states["down"] = "activated"
        if prev != self.button_states["down"]:
            self._try_trigger("buttonstate_change", self.button_states)
            self._try_trigger("down_button_pressed", self)

    def elevator_available(self, elevator):
        """Called when an elevator arrives at this floor."""
        if elevator.going_up_indicator and self.button_states["up"]:
            self.button_states["up"] = ""
            self._try_trigger("buttonstate_change", self.button_states)
        if elevator.going_down_indicator and self.button_states["down"]:
            self.button_states["down"] = ""
            self._try_trigger("buttonstate_change", self.button_states)

    def get_spawn_pos_y(self):
        """Get Y position where users spawn on this floor."""
        return self.y_position + 30

    def floor_num(self):
        """Get floor number."""
        return self.level
