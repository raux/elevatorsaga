package elevatorsaga;

/**
 * Base utility functions for math, interpolation, and physics.
 */
public final class Base {
    public static final double EPSILON = 0.00001;

    private Base() {}

    public static double limitNumber(double num, double min, double max) {
        return Math.min(max, Math.max(min, num));
    }

    public static int limitNumber(int num, int min, int max) {
        return Math.min(max, Math.max(min, num));
    }

    public static boolean epsilonEquals(double a, double b) {
        return Math.abs(a - b) < 0.00000001;
    }

    public static double linearInterpolate(double value0, double value1, double x) {
        return value0 + (value1 - value0) * x;
    }

    public static double powInterpolate(double value0, double value1, double x, double a) {
        return value0 + (value1 - value0) * Math.pow(x, a) / (Math.pow(x, a) + Math.pow(1 - x, a));
    }

    public static double coolInterpolate(double value0, double value1, double x) {
        return powInterpolate(value0, value1, x, 1.3);
    }

    public static double distanceNeededToAchieveSpeed(double currentSpeed, double targetSpeed, double acceleration) {
        return (Math.pow(targetSpeed, 2) - Math.pow(currentSpeed, 2)) / (2 * acceleration);
    }

    public static double accelerationNeededToAchieveChangeDistance(double currentSpeed, double targetSpeed, double distance) {
        return 0.5 * ((Math.pow(targetSpeed, 2) - Math.pow(currentSpeed, 2)) / distance);
    }

    @FunctionalInterface
    public interface Interpolator {
        double interpolate(double value0, double value1, double x);
    }

    public static final Interpolator DEFAULT_INTERPOLATOR = Base::coolInterpolate;
}
