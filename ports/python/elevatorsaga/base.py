"""Base utilities: math helpers, interpolation, and physics calculations."""

import math

EPSILON = 0.00001


def limit_number(num, min_val, max_val):
    """Clamp a number between min and max."""
    return min(max_val, max(min_val, num))


def epsilon_equals(a, b):
    """Check if two numbers are approximately equal."""
    return abs(a - b) < 0.00000001


def linear_interpolate(value0, value1, x):
    """Linear interpolation between two values."""
    return value0 + (value1 - value0) * x


def pow_interpolate(value0, value1, x, a):
    """Power-based interpolation between two values."""
    return value0 + (value1 - value0) * math.pow(x, a) / (math.pow(x, a) + math.pow(1 - x, a))


def cool_interpolate(value0, value1, x):
    """Default smooth interpolation."""
    return pow_interpolate(value0, value1, x, 1.3)


DEFAULT_INTERPOLATOR = cool_interpolate


def distance_needed_to_achieve_speed(current_speed, target_speed, acceleration):
    """Calculate distance needed to change from current to target speed.
    
    Uses v² = u² + 2a * d
    """
    return (target_speed ** 2 - current_speed ** 2) / (2 * acceleration)


def acceleration_needed_to_achieve_change_distance(current_speed, target_speed, distance):
    """Calculate acceleration needed to achieve speed change over distance.
    
    Uses v² = u² + 2a * d
    """
    return 0.5 * ((target_speed ** 2 - current_speed ** 2) / distance)
