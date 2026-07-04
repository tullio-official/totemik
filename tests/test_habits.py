"""Unit tests for the Habit class."""

from datetime import datetime, timedelta

from totemik.habit import Habit


def test_daily_streak_today():
    """Daily habit completed today has a live streak."""
    habit = Habit(
        name="test",
        period="daily",
        category="Body",
        created_at=datetime.now(),
        completions=[datetime.now()],
    )
    streak = habit.get_streak()
    assert streak == 1


def test_daily_streak_yesterday():
    """Daily habit last completed yesterday is still live."""
    habit = Habit(
        name="test",
        period="daily",
        category="Body",
        created_at=datetime.now(),
        completions=[datetime.now() - timedelta(days=1)],
    )
    streak = habit.get_streak()
    assert streak == 1


def test_daily_streak_broken_two_days_ago():
    """Daily habit last completed two days ago has no streak."""
    habit = Habit(
        name="test",
        period="daily",
        category="Body",
        created_at=datetime.now(),
        completions=[datetime.now() - timedelta(days=2)],
    )
    streak = habit.get_streak()
    assert streak == 0


def test_weekly_streak_this_week():
    """Weekly habit completed this week has a live streak."""
    habit = Habit(
        name="test",
        period="weekly",
        category="Body",
        created_at=datetime.now(),
        completions=[datetime.now()],
    )
    streak = habit.get_streak()
    assert streak == 1


def test_weekly_streak_last_week():
    """Weekly habit completed last week is still live."""
    habit = Habit(
        name="test",
        period="weekly",
        category="Body",
        created_at=datetime.now(),
        completions=[datetime.now() - timedelta(weeks=1)],
    )
    streak = habit.get_streak()
    assert streak == 1


def test_weekly_streak_two_weeks_ago():
    """Weekly habit last completed two weeks ago has no streak."""
    habit = Habit(
        name="test",
        period="weekly",
        category="Body",
        created_at=datetime.now(),
        completions=[datetime.now() - timedelta(weeks=2)],
    )
    streak = habit.get_streak()
    assert streak == 0


def test_longest_streak_uses_history():
    """History returns the historical maximum, not the current run."""
    habit = Habit(
        name="test",
        period="daily",
        category="Body",
        created_at=datetime.now(),
        completions=[
            datetime.now() - timedelta(days=d) for d in [9, 8, 7, 6, 2, 1, 0]
        ],
    )
    assert habit.get_streak() == 3
    assert habit.get_longest_streak() == 4


def test_complete_appends_and_increases_streak():
    """complete() records a timestamp and lifts the streak."""
    habit = Habit(
        name="test",
        period="daily",
        category="Body",
        created_at=datetime.now(),
        completions=[],
    )
    habit.complete()
    assert len(habit.completions) == 1
    assert habit.get_streak() == 1
