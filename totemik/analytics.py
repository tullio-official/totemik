"""Functional analytics over Habit and Category objects.

These functions use map, filter, and reduce explicitly.
"""

from datetime import datetime, timedelta
from functools import reduce

from totemik.category import TOTEMS


def list_all_habits(habits):
    """Return a list of all habits."""
    return list(map(lambda h: h, habits))


def list_habits_by_period(habits, period):
    """Return a list of all habits that match a certain period."""
    return list(filter(lambda h: h.period == period, habits))


def longest_streak_all(habits):
    """Return the habit with the highest longest streak, or None.

    In case of a tie, return the first habit.
    """
    if not habits:
        return None

    return reduce(
        lambda a, b: a
        if a.get_longest_streak() >= b.get_longest_streak()
        else b,
        habits,
    )


def longest_streak_one(habit):
    """Return the longest streak of one habit."""
    return habit.get_longest_streak()


def totem_summary(categories):
    """Return one summary dict per category totem."""
    return [
        {
            "name": c.name,
            "totem": TOTEMS[c.name],
            "level": c.level,
            "points": c.points,
            "progress": c.progress_to_next(),
        }
        for c in categories
    ]


def completion_rate(habit, days=30):
    """Return the completion percentage over the last n days."""
    # Expected completions in the window: one per day, or one per week.
    expected = days if habit.period == "daily" else days // 7
    if expected == 0:
        return 0.0

    # Count the completions that fall inside the window.
    cutoff = datetime.now() - timedelta(days=days)
    actual = len(list(filter(lambda c: c >= cutoff, habit.completions)))

    return actual / expected * 100
