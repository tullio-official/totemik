"""Unit tests for the analytics functions."""

from datetime import datetime, timedelta

from totemik.habit import Habit
from totemik import analytics


def test_list_all_habits():
    """Every habit passed in is returned."""
    habits = [
        Habit(name="a", period="daily", category="Body",
              created_at=datetime.now()),
        Habit(name="b", period="weekly", category="Mind",
              created_at=datetime.now()),
        Habit(name="c", period="daily", category="Self",
              created_at=datetime.now()),
    ]
    result = analytics.list_all_habits(habits)
    assert result == habits
    assert len(result) == 3


def test_list_habits_by_period_daily():
    """Only the daily habits are returned."""
    habits = [
        Habit(name="a", period="daily", category="Body",
              created_at=datetime.now()),
        Habit(name="b", period="weekly", category="Mind",
              created_at=datetime.now()),
        Habit(name="c", period="daily", category="Self",
              created_at=datetime.now()),
    ]
    result = analytics.list_habits_by_period(habits, "daily")
    assert len(result) == 2
    assert all(h.period == "daily" for h in result)


def test_list_habits_by_period_weekly():
    """Only the weekly habits are returned."""
    habits = [
        Habit(name="a", period="daily", category="Body",
              created_at=datetime.now()),
        Habit(name="b", period="weekly", category="Mind",
              created_at=datetime.now()),
        Habit(name="c", period="daily", category="Self",
              created_at=datetime.now()),
    ]
    result = analytics.list_habits_by_period(habits, "weekly")
    assert len(result) == 1
    assert all(h.period == "weekly" for h in result)


def test_longest_streak_all_returns_top_habit():
    """The habit with the highest longest streak wins."""
    short = Habit(
        name="short",
        period="daily",
        category="Body",
        created_at=datetime.now(),
        completions=[
            datetime.now() - timedelta(days=d) for d in [0, 1]
        ],
    )
    long = Habit(
        name="long",
        period="daily",
        category="Mind",
        created_at=datetime.now(),
        completions=[
            datetime.now() - timedelta(days=d) for d in [0, 1, 2, 3, 4]
        ],
    )
    medium = Habit(
        name="medium",
        period="daily",
        category="Self",
        created_at=datetime.now(),
        completions=[
            datetime.now() - timedelta(days=d) for d in [0, 1, 2]
        ],
    )
    top = analytics.longest_streak_all([short, long, medium])
    assert top is long
    assert top.get_longest_streak() == 5


def test_longest_streak_all_empty_returns_none():
    """An empty list returns None instead of raising."""
    assert analytics.longest_streak_all([]) is None


def test_longest_streak_one():
    """A single habit reports its own longest streak."""
    habit = Habit(
        name="solo",
        period="daily",
        category="Body",
        created_at=datetime.now(),
        completions=[
            datetime.now() - timedelta(days=d) for d in [0, 1, 2, 3]
        ],
    )
    assert analytics.longest_streak_one(habit) == habit.get_longest_streak()
    assert analytics.longest_streak_one(habit) == 4


def test_completion_rate_full_and_partial():
    """A full history scores high, a half-filled one scores lower."""
    full = Habit(
        name="full",
        period="daily",
        category="Body",
        created_at=datetime.now(),
        completions=[
            datetime.now() - timedelta(days=d) for d in range(30)
        ],
    )
    partial = Habit(
        name="partial",
        period="daily",
        category="Mind",
        created_at=datetime.now(),
        completions=[
            datetime.now() - timedelta(days=d) for d in range(0, 30, 2)
        ],
    )
    full_rate = analytics.completion_rate(full, days=30)
    partial_rate = analytics.completion_rate(partial, days=30)
    assert full_rate == 100.0
    assert partial_rate == 50.0
    assert full_rate > partial_rate
