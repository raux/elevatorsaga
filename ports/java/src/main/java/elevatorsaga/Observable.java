package elevatorsaga;

import java.util.*;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * Observable class providing event-based communication.
 */
public class Observable {
    private final Map<String, List<EventListener>> listeners = new HashMap<>();

    @FunctionalInterface
    public interface EventListener {
        void handle(Object... args);
    }

    public void on(String events, EventListener callback) {
        for (String event : events.split("\\s+")) {
            listeners.computeIfAbsent(event, k -> new CopyOnWriteArrayList<>()).add(callback);
        }
    }

    public void off(String events, EventListener callback) {
        if ("*".equals(events)) {
            listeners.clear();
            return;
        }
        for (String event : events.split("\\s+")) {
            if (callback == null) {
                listeners.remove(event);
            } else {
                List<EventListener> list = listeners.get(event);
                if (list != null) {
                    list.remove(callback);
                }
            }
        }
    }

    public void off(String events) {
        off(events, null);
    }

    public void trigger(String event, Object... args) {
        List<EventListener> list = listeners.get(event);
        if (list != null) {
            for (EventListener listener : list) {
                listener.handle(args);
            }
        }
    }
}
