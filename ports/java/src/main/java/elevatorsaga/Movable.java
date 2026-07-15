package elevatorsaga;

/**
 * Base class for objects that can move in the world.
 */
public class Movable extends Observable {
    public double x = 0.0;
    public double y = 0.0;
    public Movable parent = null;
    public double worldX = 0.0;
    public double worldY = 0.0;
    protected Runnable currentTaskRunner = null;

    @FunctionalInterface
    public interface TaskUpdater {
        void update(double dt);
    }

    private TaskUpdater currentTask = null;

    public Movable() {
        trigger("new_state", this);
    }

    public void updateDisplayPosition(boolean forceTrigger) {
        double[] pos = getWorldPosition();
        double oldX = worldX, oldY = worldY;
        worldX = pos[0];
        worldY = pos[1];
        if (oldX != worldX || oldY != worldY || forceTrigger) {
            trigger("new_display_state", this);
        }
    }

    public void updateDisplayPosition() {
        updateDisplayPosition(false);
    }

    public void moveTo(Double newX, Double newY) {
        if (newX != null) this.x = newX;
        if (newY != null) this.y = newY;
        trigger("new_state", this);
    }

    public void moveToFast(double newX, double newY) {
        this.x = newX;
        this.y = newY;
        trigger("new_state", this);
    }

    public boolean isBusy() {
        return currentTask != null;
    }

    public void makeSureNotBusy() {
        if (isBusy()) {
            throw new RuntimeException("Object is busy - you should use callback");
        }
    }

    public void wait(double millis, Runnable cb) {
        makeSureNotBusy();
        final double[] timeSpent = {0.0};
        currentTask = (dt) -> {
            timeSpent[0] += dt;
            if (timeSpent[0] > millis) {
                currentTask = null;
                if (cb != null) cb.run();
            }
        };
    }

    public void moveToOverTime(Double newX, Double newY, double timeToSpend, Base.Interpolator interpolator, Runnable cb) {
        makeSureNotBusy();
        double targetX = (newX != null) ? newX : this.x;
        double targetY = (newY != null) ? newY : this.y;
        if (interpolator == null) interpolator = Base.DEFAULT_INTERPOLATOR;
        double origX = this.x;
        double origY = this.y;
        final double[] timeSpent = {0.0};
        final Base.Interpolator interp = interpolator;
        currentTask = (dt) -> {
            timeSpent[0] = Math.min(timeToSpend, timeSpent[0] + dt);
            if (timeSpent[0] == timeToSpend) {
                moveToFast(targetX, targetY);
                currentTask = null;
                if (cb != null) cb.run();
            } else {
                double factor = timeSpent[0] / timeToSpend;
                moveToFast(interp.interpolate(origX, targetX, factor), interp.interpolate(origY, targetY, factor));
            }
        };
    }

    public void update(double dt) {
        if (currentTask != null) {
            currentTask.update(dt);
        }
    }

    public double[] getWorldPosition() {
        double resultX = this.x;
        double resultY = this.y;
        Movable current = this.parent;
        while (current != null) {
            resultX += current.x;
            resultY += current.y;
            current = current.parent;
        }
        return new double[]{resultX, resultY};
    }

    public void setParent(Movable movableParent) {
        if (movableParent == null) {
            if (this.parent != null) {
                double[] objWorld = getWorldPosition();
                this.parent = null;
                moveToFast(objWorld[0], objWorld[1]);
            }
        } else {
            double[] objWorld = getWorldPosition();
            double[] parentWorld = movableParent.getWorldPosition();
            this.parent = movableParent;
            moveToFast(objWorld[0] - parentWorld[0], objWorld[1] - parentWorld[1]);
        }
    }
}
