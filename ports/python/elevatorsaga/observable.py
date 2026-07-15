"""Observable mixin providing event emit/subscribe functionality."""


class Observable:
    """Mixin class that provides event-based communication."""

    def __init__(self):
        self._listeners = {}

    def on(self, events, callback):
        """Register a callback for one or more space-separated events."""
        for event in events.split():
            if event not in self._listeners:
                self._listeners[event] = []
            self._listeners[event].append(callback)

    def off(self, events, callback=None):
        """Remove listener(s). If events is '*', remove all."""
        if events == "*":
            self._listeners = {}
            return
        for event in events.split():
            if callback is None:
                self._listeners.pop(event, None)
            elif event in self._listeners:
                self._listeners[event] = [
                    cb for cb in self._listeners[event] if cb != callback
                ]

    def trigger(self, event, *args):
        """Trigger an event, calling all registered listeners."""
        if event in self._listeners:
            for callback in list(self._listeners[event]):
                callback(*args)
