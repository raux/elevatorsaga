"""Simple elevator solution example.

This implements a basic strategy: send idle elevators to floors
where buttons are pressed, and go to pressed floors inside the elevator.
"""


def init(elevators, floors):
    """Initialize elevator event handlers."""
    for elevator in elevators:
        def make_handlers(elev):
            def on_idle():
                # Go to any floor with a pressed button
                pressed = elev.get_pressed_floors()
                if pressed:
                    elev.go_to_floor(pressed[0])
                else:
                    elev.go_to_floor(0)

            def on_floor_button_pressed(floor_num):
                elev.go_to_floor(floor_num)

            def on_stopped_at_floor(floor_num):
                # Check if there are more pressed floors
                pass

            elev.on("idle", on_idle)
            elev.on("floor_button_pressed", on_floor_button_pressed)
            elev.on("stopped_at_floor", on_stopped_at_floor)

        make_handlers(elevator)


def update(dt, elevators, floors):
    """Called each simulation tick (no-op for event-driven strategy)."""
    pass
