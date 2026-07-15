package elevatorsaga;

import java.util.*;
import java.util.function.Function;

/**
 * Challenge definitions for Elevator Saga.
 */
public class Challenge {
    public final Map<String, Object> options;
    public final String description;
    public final Function<World, Boolean> evaluate;

    public Challenge(Map<String, Object> options, String description, Function<World, Boolean> evaluate) {
        this.options = options;
        this.description = description;
        this.evaluate = evaluate;
    }

    private static Map<String, Object> opts(Object... pairs) {
        Map<String, Object> map = new HashMap<>();
        for (int i = 0; i < pairs.length; i += 2) {
            map.put((String) pairs[i], pairs[i + 1]);
        }
        return map;
    }

    public static List<Challenge> getAllChallenges() {
        List<Challenge> challenges = new ArrayList<>();

        challenges.add(new Challenge(
            opts("floor_count", 3, "elevator_count", 1, "spawn_rate", 0.3, "elevator_capacities", new int[]{4}),
            "Transport 15 people in 60 seconds or less",
            w -> (w.elapsedTime >= 60 || w.transportedCounter >= 15)
                ? (w.elapsedTime <= 60 && w.transportedCounter >= 15) : null));

        challenges.add(new Challenge(
            opts("floor_count", 5, "elevator_count", 1, "spawn_rate", 0.4, "elevator_capacities", new int[]{4}),
            "Transport 20 people in 60 seconds or less",
            w -> (w.elapsedTime >= 60 || w.transportedCounter >= 20)
                ? (w.elapsedTime <= 60 && w.transportedCounter >= 20) : null));

        challenges.add(new Challenge(
            opts("floor_count", 5, "elevator_count", 1, "spawn_rate", 0.5, "elevator_capacities", new int[]{6}),
            "Transport 23 people in 60 seconds or less",
            w -> (w.elapsedTime >= 60 || w.transportedCounter >= 23)
                ? (w.elapsedTime <= 60 && w.transportedCounter >= 23) : null));

        challenges.add(new Challenge(
            opts("floor_count", 8, "elevator_count", 2, "spawn_rate", 0.6, "elevator_capacities", new int[]{4}),
            "Transport 28 people in 60 seconds or less",
            w -> (w.elapsedTime >= 60 || w.transportedCounter >= 28)
                ? (w.elapsedTime <= 60 && w.transportedCounter >= 28) : null));

        challenges.add(new Challenge(
            opts("floor_count", 6, "elevator_count", 4, "spawn_rate", 1.7, "elevator_capacities", new int[]{4}),
            "Transport 100 people in 68 seconds or less",
            w -> (w.elapsedTime >= 68 || w.transportedCounter >= 100)
                ? (w.elapsedTime <= 68 && w.transportedCounter >= 100) : null));

        challenges.add(new Challenge(
            opts("floor_count", 4, "elevator_count", 2, "spawn_rate", 0.8, "elevator_capacities", new int[]{4}),
            "Transport 40 people using 60 elevator moves or less",
            w -> (w.moveCount >= 60 || w.transportedCounter >= 40)
                ? (w.moveCount <= 60 && w.transportedCounter >= 40) : null));

        challenges.add(new Challenge(
            opts("floor_count", 3, "elevator_count", 3, "spawn_rate", 3.0, "elevator_capacities", new int[]{4}),
            "Transport 100 people using 63 elevator moves or less",
            w -> (w.moveCount >= 63 || w.transportedCounter >= 100)
                ? (w.moveCount <= 63 && w.transportedCounter >= 100) : null));

        challenges.add(new Challenge(
            opts("floor_count", 6, "elevator_count", 2, "spawn_rate", 0.4, "elevator_capacities", new int[]{5}),
            "Transport 50 people and let no one wait more than 21.0 seconds",
            w -> (w.maxWaitTime >= 21 || w.transportedCounter >= 50)
                ? (w.maxWaitTime <= 21 && w.transportedCounter >= 50) : null));

        challenges.add(new Challenge(
            opts("floor_count", 7, "elevator_count", 3, "spawn_rate", 0.6, "elevator_capacities", new int[]{4}),
            "Transport 50 people and let no one wait more than 20.0 seconds",
            w -> (w.maxWaitTime >= 20 || w.transportedCounter >= 50)
                ? (w.maxWaitTime <= 20 && w.transportedCounter >= 50) : null));

        challenges.add(new Challenge(
            opts("floor_count", 13, "elevator_count", 2, "spawn_rate", 1.1, "elevator_capacities", new int[]{4, 10}),
            "Transport 50 people in 70 seconds or less",
            w -> (w.elapsedTime >= 70 || w.transportedCounter >= 50)
                ? (w.elapsedTime <= 70 && w.transportedCounter >= 50) : null));

        challenges.add(new Challenge(
            opts("floor_count", 9, "elevator_count", 5, "spawn_rate", 1.1, "elevator_capacities", new int[]{4}),
            "Transport 60 people and let no one wait more than 19.0 seconds",
            w -> (w.maxWaitTime >= 19 || w.transportedCounter >= 60)
                ? (w.maxWaitTime <= 19 && w.transportedCounter >= 60) : null));

        challenges.add(new Challenge(
            opts("floor_count", 9, "elevator_count", 5, "spawn_rate", 1.1, "elevator_capacities", new int[]{4}),
            "Transport 80 people and let no one wait more than 17.0 seconds",
            w -> (w.maxWaitTime >= 17 || w.transportedCounter >= 80)
                ? (w.maxWaitTime <= 17 && w.transportedCounter >= 80) : null));

        challenges.add(new Challenge(
            opts("floor_count", 9, "elevator_count", 5, "spawn_rate", 1.1, "elevator_capacities", new int[]{5}),
            "Transport 100 people and let no one wait more than 15.0 seconds",
            w -> (w.maxWaitTime >= 15 || w.transportedCounter >= 100)
                ? (w.maxWaitTime <= 15 && w.transportedCounter >= 100) : null));

        challenges.add(new Challenge(
            opts("floor_count", 9, "elevator_count", 5, "spawn_rate", 1.0, "elevator_capacities", new int[]{6}),
            "Transport 110 people and let no one wait more than 15.0 seconds",
            w -> (w.maxWaitTime >= 15 || w.transportedCounter >= 110)
                ? (w.maxWaitTime <= 15 && w.transportedCounter >= 110) : null));

        challenges.add(new Challenge(
            opts("floor_count", 8, "elevator_count", 6, "spawn_rate", 0.9, "elevator_capacities", new int[]{4}),
            "Transport 120 people and let no one wait more than 14.0 seconds",
            w -> (w.maxWaitTime >= 14 || w.transportedCounter >= 120)
                ? (w.maxWaitTime <= 14 && w.transportedCounter >= 120) : null));

        challenges.add(new Challenge(
            opts("floor_count", 12, "elevator_count", 4, "spawn_rate", 1.4, "elevator_capacities", new int[]{5, 10}),
            "Transport 70 people in 80 seconds or less",
            w -> (w.elapsedTime >= 80 || w.transportedCounter >= 70)
                ? (w.elapsedTime <= 80 && w.transportedCounter >= 70) : null));

        challenges.add(new Challenge(
            opts("floor_count", 21, "elevator_count", 5, "spawn_rate", 1.9, "elevator_capacities", new int[]{10}),
            "Transport 110 people in 80 seconds or less",
            w -> (w.elapsedTime >= 80 || w.transportedCounter >= 110)
                ? (w.elapsedTime <= 80 && w.transportedCounter >= 110) : null));

        challenges.add(new Challenge(
            opts("floor_count", 21, "elevator_count", 8, "spawn_rate", 1.5, "elevator_capacities", new int[]{6, 8}),
            "Transport 2675 people in 1800 seconds or less and let no one wait more than 45.0 seconds",
            w -> (w.elapsedTime >= 1800 || w.maxWaitTime >= 45 || w.transportedCounter >= 2675)
                ? (w.elapsedTime <= 1800 && w.maxWaitTime <= 45 && w.transportedCounter >= 2675) : null));

        return challenges;
    }
}
