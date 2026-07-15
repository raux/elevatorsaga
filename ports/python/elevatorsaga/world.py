"""World creation and simulation logic."""

import random
from .observable import Observable
from .floor import Floor
from .elevator import Elevator
from .user import User
from .interfaces import ElevatorInterface


class World(Observable):
    """The game world containing elevators, floors, and users."""

    def __init__(self, options=None):
        super().__init__()
        defaults = {
            "floor_height": 50,
            "floor_count": 4,
            "elevator_count": 2,
            "spawn_rate": 0.5,
            "elevator_capacities": [4],
        }
        if options:
            defaults.update(options)
        options = defaults

        self.floor_height = options["floor_height"]
        self.transported_counter = 0
        self.transported_per_sec = 0.0
        self.move_count = 0
        self.elapsed_time = 0.0
        self.max_wait_time = 0.0
        self.avg_wait_time = 0.0
        self.challenge_ended = False
        self.users = []
        self._spawn_rate = options["spawn_rate"]
        self._elapsed_since_spawn = 1.001 / self._spawn_rate

        def error_handler(e):
            self.trigger("usercode_error", e)

        # Create floors
        floor_count = options["floor_count"]
        self.floors = []
        for i in range(floor_count):
            y_pos = (floor_count - 1 - i) * self.floor_height
            self.floors.append(Floor(i, y_pos, error_handler))

        # Create elevators
        elevator_capacities = options["elevator_capacities"]
        current_x = 200.0
        self.elevators = []
        for i in range(options["elevator_count"]):
            cap = elevator_capacities[i % len(elevator_capacities)]
            elevator = Elevator(2.6, floor_count, self.floor_height, cap)
            elevator.move_to(current_x, None)
            elevator.set_floor_position(0)
            elevator.update_display_position()
            current_x += 20 + elevator.width
            self.elevators.append(elevator)

        # Create interfaces
        self.elevator_interfaces = [
            ElevatorInterface(e, floor_count, error_handler) for e in self.elevators
        ]

        # Bind elevator entrance events
        for elevator in self.elevators:
            elevator.on("entrance_available", self._handle_elev_availability)

        # Bind floor button repressing
        for floor in self.floors:
            floor.on("up_button_pressed", lambda f, ev="up_button_pressed": self._handle_button_repressing(ev, f))
            floor.on("down_button_pressed", lambda f, ev="down_button_pressed": self._handle_button_repressing(ev, f))

    def _handle_elev_availability(self, elevator):
        """Notify floors and users when elevator is available."""
        for i, floor in enumerate(self.floors):
            if elevator.current_floor == i:
                floor.elevator_available(elevator)
        for user in list(self.users):
            if user.current_floor == elevator.current_floor:
                user.elevator_available(elevator, self.floors[elevator.current_floor])

    def _handle_button_repressing(self, event_name, floor):
        """Handle button re-pressing to make elevators re-arrive."""
        offset = random.randint(0, len(self.elevators) - 1)
        for i in range(len(self.elevators)):
            elev_index = (i + offset) % len(self.elevators)
            elevator = self.elevators[elev_index]
            if (event_name == "up_button_pressed" and elevator.going_up_indicator) or \
               (event_name == "down_button_pressed" and elevator.going_down_indicator):
                if (elevator.current_floor == floor.level and
                        elevator.is_on_a_floor() and
                        not elevator.is_moving and
                        not elevator.is_full()):
                    self.elevator_interfaces[elev_index].go_to_floor(floor.level, True)
                    return

    def _recalculate_stats(self):
        """Recalculate world statistics."""
        if self.elapsed_time > 0:
            self.transported_per_sec = self.transported_counter / self.elapsed_time
        self.move_count = sum(e.move_count for e in self.elevators)
        self.trigger("stats_changed")

    def _register_user(self, user):
        """Register a new user in the world."""
        self.users.append(user)
        user.update_display_position(True)
        user.spawn_timestamp = self.elapsed_time
        self.trigger("new_user", user)

        def on_exited(elevator):
            self.transported_counter += 1
            self.max_wait_time = max(self.max_wait_time, self.elapsed_time - user.spawn_timestamp)
            self.avg_wait_time = (
                self.avg_wait_time * (self.transported_counter - 1) +
                (self.elapsed_time - user.spawn_timestamp)
            ) / self.transported_counter
            self._recalculate_stats()

        user.on("exited_elevator", on_exited)
        user.update_display_position(True)

    def _spawn_user_randomly(self):
        """Create and spawn a random user."""
        weight = random.randint(55, 100)
        user = User(weight)
        r = random.randint(0, 40)
        if r == 0:
            user.display_type = "child"
        elif random.randint(0, 1) == 0:
            user.display_type = "female"
        else:
            user.display_type = "male"

        user.move_to(105 + random.randint(0, 40), 0)
        floor_count = len(self.floors)
        current_floor = 0 if random.randint(0, 1) == 0 else random.randint(0, floor_count - 1)

        if current_floor == 0:
            destination_floor = random.randint(1, floor_count - 1)
        else:
            if random.randint(0, 10) == 0:
                destination_floor = (current_floor + random.randint(1, floor_count - 1)) % floor_count
            else:
                destination_floor = 0

        user.appear_on_floor(self.floors[current_floor], destination_floor)
        return user

    def update(self, dt):
        """Main world update for one time step."""
        self.elapsed_time += dt
        self._elapsed_since_spawn += dt

        while self._elapsed_since_spawn > 1.0 / self._spawn_rate:
            self._elapsed_since_spawn -= 1.0 / self._spawn_rate
            self._register_user(self._spawn_user_randomly())

        for elevator in self.elevators:
            elevator.update(dt)
            elevator.update_elevator_movement(dt)

        for user in self.users:
            user.update(dt)
            self.max_wait_time = max(self.max_wait_time, self.elapsed_time - user.spawn_timestamp)

        self.users = [u for u in self.users if not u.remove_me]
        self._recalculate_stats()

    def init(self):
        """Initialize the world - triggers idle events."""
        for interface in self.elevator_interfaces:
            interface.check_destination_queue()

    def unwind(self):
        """Clean up world resources."""
        for obj in self.elevators + self.elevator_interfaces + self.users + self.floors + [self]:
            obj.off("*")
        self.challenge_ended = True
        self.elevators = []
        self.elevator_interfaces = []
        self.users = []
        self.floors = []
