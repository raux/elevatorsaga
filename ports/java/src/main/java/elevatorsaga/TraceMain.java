package elevatorsaga;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;

/** Records simulation snapshots as JSON for the Python NiceGUI visualizer. */
public final class TraceMain {
    private static final double TIME_STEP = 0.025;
    private static final double MAX_TIME = 3600.0;
    private static final int MAX_FRAMES = 6000;

    private TraceMain() {}

    private static String jsonString(String value) {
        if (value == null) return "null";
        StringBuilder escaped = new StringBuilder("\"");
        for (int i = 0; i < value.length(); i++) {
            char ch = value.charAt(i);
            switch (ch) {
                case '\\': escaped.append("\\\\"); break;
                case '"': escaped.append("\\\""); break;
                case '\n': escaped.append("\\n"); break;
                case '\r': escaped.append("\\r"); break;
                case '\t': escaped.append("\\t"); break;
                default:
                    if (ch < 0x20) escaped.append(String.format("\\u%04x", (int) ch));
                    else escaped.append(ch);
            }
        }
        return escaped.append('"').toString();
    }

    private static String number(double value) {
        if (!Double.isFinite(value)) return "0";
        return String.format(java.util.Locale.ROOT, "%.4f", value);
    }

    private static String snapshot(World world, Map<User, Integer> userIds) {
        StringBuilder json = new StringBuilder();
        json.append("{\"time\":").append(number(world.elapsedTime));
        json.append(",\"elevators\":[");
        for (int i = 0; i < world.elevators.size(); i++) {
            if (i > 0) json.append(',');
            Elevator elevator = world.elevators.get(i);
            double[] position = elevator.getWorldPosition();
            json.append("{\"id\":").append(i)
                .append(",\"x\":").append(number(position[0]))
                .append(",\"y\":").append(number(position[1]))
                .append(",\"floor\":").append(elevator.currentFloor)
                .append(",\"load\":").append(number(elevator.getLoadFactor()))
                .append(",\"up\":").append(elevator.goingUpIndicator)
                .append(",\"down\":").append(elevator.goingDownIndicator)
                .append('}');
        }
        json.append("],\"users\":[");
        boolean first = true;
        for (User user : world.users) {
            if (!first) json.append(',');
            first = false;
            if (!userIds.containsKey(user)) userIds.put(user, userIds.size());
            double[] position = user.getWorldPosition();
            json.append("{\"id\":").append(userIds.get(user))
                .append(",\"x\":").append(number(position[0]))
                .append(",\"y\":").append(number(position[1]))
                .append(",\"from\":").append(user.currentFloor)
                .append(",\"to\":").append(user.destinationFloor)
                .append(",\"done\":").append(user.done)
                .append(",\"type\":").append(jsonString(user.displayType))
                .append('}');
        }
        json.append("],\"stats\":{")
            .append("\"transported\":").append(world.transportedCounter)
            .append(",\"moves\":").append(world.moveCount)
            .append(",\"maxWaitTime\":").append(number(world.maxWaitTime))
            .append(",\"avgWaitTime\":").append(number(world.avgWaitTime))
            .append("}}");
        return json.toString();
    }

    private static void writeTrace(
        Path output,
        int challengeNumber,
        ElevatorStrategy strategy,
        double sampleEvery
    ) throws IOException {
        List<Challenge> challenges = Challenge.getAllChallenges();
        if (challengeNumber < 1 || challengeNumber > challenges.size()) {
            throw new IllegalArgumentException("Challenge must be between 1 and " + challenges.size());
        }
        Challenge challenge = challenges.get(challengeNumber - 1);
        World world = new World(challenge.options);
        Map<User, Integer> userIds = new IdentityHashMap<>();
        final String[] callbackError = {null};
        world.on("usercode_error", args -> {
            if (callbackError[0] == null && args.length > 0) callbackError[0] = String.valueOf(args[0]);
        });

        String error = null;
        Boolean result = null;
        try {
            strategy.init(world.elevatorInterfaces, world.floors);
            world.init();
            if (callbackError[0] != null) throw new RuntimeException(callbackError[0]);
        } catch (Exception exception) {
            error = "Error in strategy init: " + exception;
        }

        try (BufferedWriter writer = Files.newBufferedWriter(output, StandardCharsets.UTF_8)) {
            writer.write("{\"language\":\"java\",\"challenge\":");
            writer.write(Integer.toString(challengeNumber));
            writer.write(",\"description\":");
            writer.write(jsonString(challenge.description));
            writer.write(",\"scene\":{\"floorCount\":");
            writer.write(Integer.toString(world.floors.size()));
            writer.write(",\"floorHeight\":");
            writer.write(number(world.floorHeight));
            writer.write(",\"elevatorCapacities\":[");
            for (int i = 0; i < world.elevators.size(); i++) {
                if (i > 0) writer.write(',');
                writer.write(Integer.toString(world.elevators.get(i).maxUsers));
            }
            writer.write("],\"sampleEvery\":");
            writer.write(number(sampleEvery));
            writer.write("},\"frames\":[");

            int frameCount = 0;
            double nextSample = 0.0;
            double lastRecordedTime = world.elapsedTime;
            writer.write(snapshot(world, userIds));
            frameCount++;
            nextSample += sampleEvery;

            while (error == null && result == null && world.elapsedTime < MAX_TIME) {
                try {
                    strategy.update(TIME_STEP, world.elevatorInterfaces, world.floors);
                    if (callbackError[0] != null) throw new RuntimeException(callbackError[0]);
                    world.update(TIME_STEP);
                    if (callbackError[0] != null) throw new RuntimeException(callbackError[0]);
                } catch (Exception exception) {
                    error = "Error in strategy callback/update: " + exception;
                    break;
                }
                result = challenge.evaluate.apply(world);
                if (world.elapsedTime + 1e-9 >= nextSample && frameCount < MAX_FRAMES) {
                    writer.write(',');
                    writer.write(snapshot(world, userIds));
                    frameCount++;
                    lastRecordedTime = world.elapsedTime;
                    nextSample += sampleEvery;
                }
            }
            if (frameCount < MAX_FRAMES && Math.abs(lastRecordedTime - world.elapsedTime) > 1e-9) {
                writer.write(',');
                writer.write(snapshot(world, userIds));
            }

            boolean passed = Boolean.TRUE.equals(result) && error == null;
            writer.write("],\"result\":{\"passed\":");
            writer.write(Boolean.toString(passed));
            writer.write(",\"error\":");
            writer.write(jsonString(error));
            writer.write(",\"elapsedTime\":");
            writer.write(number(world.elapsedTime));
            writer.write(",\"transported\":");
            writer.write(Integer.toString(world.transportedCounter));
            writer.write(",\"moves\":");
            writer.write(Integer.toString(world.moveCount));
            writer.write(",\"maxWaitTime\":");
            writer.write(number(world.maxWaitTime));
            writer.write("}}");
        }
    }

    public static void main(String[] args) {
        int challenge = 1;
        String strategyClass = null;
        String output = null;
        double sampleEvery = 0.1;
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--challenge": challenge = Integer.parseInt(args[++i]); break;
                case "--strategy": strategyClass = args[++i]; break;
                case "--output": output = args[++i]; break;
                case "--sample-every": sampleEvery = Double.parseDouble(args[++i]); break;
                default: throw new IllegalArgumentException("Unknown argument: " + args[i]);
            }
        }
        if (strategyClass == null || output == null) {
            throw new IllegalArgumentException("--strategy and --output are required");
        }
        try {
            Class<?> clazz = Class.forName(strategyClass);
            ElevatorStrategy strategy = (ElevatorStrategy) clazz.getDeclaredConstructor().newInstance();
            writeTrace(Path.of(output), challenge, strategy, sampleEvery);
        } catch (Exception exception) {
            System.err.println("Unable to record Java trace: " + exception);
            System.exit(1);
        }
    }
}
