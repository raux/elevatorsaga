package elevatorsaga;

import java.util.*;

/**
 * Main entry point for running Elevator Saga simulations.
 */
public class Main {
    private static final double TIME_STEP = 0.025;
    private static final double MAX_TIME = 3600;

    public static boolean runChallenge(int challengeIndex, ElevatorStrategy strategy, boolean verbose) {
        List<Challenge> challenges = Challenge.getAllChallenges();
        if (challengeIndex < 0 || challengeIndex >= challenges.size()) {
            System.out.println("Error: Challenge " + (challengeIndex + 1) + " does not exist. Available: 1-" + challenges.size());
            return false;
        }

        Challenge challenge = challenges.get(challengeIndex);

        if (verbose) {
            System.out.println("\n" + "=".repeat(60));
            System.out.println("  Challenge #" + (challengeIndex + 1));
            System.out.println("  " + challenge.description);
            System.out.println("=".repeat(60));
        }

        World world = new World(challenge.options);

        try {
            strategy.init(world.elevatorInterfaces, world.floors);
            world.init();
        } catch (Exception e) {
            System.out.println("Error in strategy init: " + e.getMessage());
            return false;
        }

        Boolean result = null;
        double lastReportTime = 0.0;

        while (result == null && world.elapsedTime < MAX_TIME) {
            try {
                strategy.update(TIME_STEP, world.elevatorInterfaces, world.floors);
            } catch (Exception e) {
                System.out.println("Error in strategy update: " + e.getMessage());
                return false;
            }

            world.update(TIME_STEP);
            result = challenge.evaluate.apply(world);

            if (verbose && world.elapsedTime - lastReportTime >= 5.0) {
                lastReportTime = world.elapsedTime;
                System.out.printf("  [%6.1fs] Transported: %4d | Moves: %4d | Max wait: %.1fs | Waiting: %3d%n",
                    world.elapsedTime, world.transportedCounter, world.moveCount,
                    world.maxWaitTime, world.users.size());
            }
        }

        if (verbose) {
            System.out.printf("%n  Final: %.1fs elapsed, %d transported, %d moves, max wait %.1fs%n",
                world.elapsedTime, world.transportedCounter, world.moveCount, world.maxWaitTime);
        }

        if (Boolean.TRUE.equals(result)) {
            if (verbose) System.out.println("  ✓ CHALLENGE PASSED!");
            return true;
        } else {
            if (verbose) System.out.println("  ✗ CHALLENGE FAILED");
            return false;
        }
    }

    public static void main(String[] args) {
        int challengeNum = 1;
        String strategyClass = null;
        boolean quiet = false;
        boolean runAll = false;

        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--challenge": case "-c":
                    challengeNum = Integer.parseInt(args[++i]);
                    break;
                case "--strategy": case "-s":
                    strategyClass = args[++i];
                    break;
                case "--quiet": case "-q":
                    quiet = true;
                    break;
                case "--all": case "-a":
                    runAll = true;
                    break;
                case "--help": case "-h":
                    System.out.println("Elevator Saga - Java Edition");
                    System.out.println("Usage: java elevatorsaga.Main [options]");
                    System.out.println("  --challenge, -c <num>   Challenge number (1-indexed, default: 1)");
                    System.out.println("  --strategy, -s <class>  Fully qualified strategy class name");
                    System.out.println("  --quiet, -q             Minimal output");
                    System.out.println("  --all, -a               Run all challenges");
                    return;
            }
        }

        if (strategyClass == null) {
            System.out.println("Error: --strategy is required. Provide a fully qualified class name.");
            System.out.println("Example: java elevatorsaga.Main --strategy examples.SimpleStrategy --challenge 1");
            System.exit(1);
        }

        ElevatorStrategy strategy;
        try {
            Class<?> clazz = Class.forName(strategyClass);
            strategy = (ElevatorStrategy) clazz.getDeclaredConstructor().newInstance();
        } catch (Exception e) {
            System.out.println("Error loading strategy: " + e.getMessage());
            System.exit(1);
            return;
        }

        if (runAll) {
            List<Challenge> challenges = Challenge.getAllChallenges();
            int passed = 0;
            for (int i = 0; i < challenges.size(); i++) {
                if (runChallenge(i, strategy, !quiet)) passed++;
            }
            System.out.printf("%nResults: %d/%d challenges passed%n", passed, challenges.size());
            System.exit(passed == challenges.size() ? 0 : 1);
        } else {
            boolean success = runChallenge(challengeNum - 1, strategy, !quiet);
            System.exit(success ? 0 : 1);
        }
    }
}
