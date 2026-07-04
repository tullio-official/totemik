"""Integration tests for HabitTracker, the SQLite layer and the seed."""

from datetime import datetime, timedelta

import pytest

from totemik import seed
from totemik.tracker import HabitTracker


def find_category(tracker, name):
    """Return the in-memory category with this name."""
    return next(c for c in tracker.get_categories() if c.name == name)


def test_first_run_seeds_predefined_habits(tmp_path):
    """A fresh database is populated with the ten predefined habits."""
    tracker = HabitTracker(db_path=str(tmp_path / "fresh.db"))

    habits = tracker.get_habits()
    expected = sorted(name for name, _, _ in seed.PREDEFINED_HABITS)
    assert sorted(h.name for h in habits) == expected
    assert len(habits) == 10

    assert all(h.completions for h in habits)
    assert len(tracker.get_categories()) == 5

    tracker.close()


def test_seed_runs_once(tmp_path):
    """Reopening an existing database does not seed a second time."""
    db_path = str(tmp_path / "once.db")

    first = HabitTracker(db_path=db_path)
    first.close()

    second = HabitTracker(db_path=db_path)
    assert len(second.get_habits()) == 10
    second.close()

EXPECTED_LONGEST_STREAKS = {
    "30-minute workout": 28,     # 28 unbroken days
    "Read 20 pages": 14,         # a 14-day run, a gap, then 12 more days
    "Check in with someone": 7,  # the last seven days
    "Plan the day": 1,           # every other day
    "Journal entry": 7,          # seven early days, then three recent ones
    "Meal prep": 4,              # four unbroken weeks
    "Study something new": 2,    # a missed week
    "Meet up with a friend": 2,  # the last two weeks
    "Weekly review": 3,          # the last three weeks
    "Creative practice": 1,      # one recent week and one older week
}


def test_seed_data_longest_streaks(tmp_path):
    """Each predefined habit reports the longest streak it implies."""
    tracker = HabitTracker(db_path=str(tmp_path / "longest.db"))
    by_name = {h.name: h for h in tracker.get_habits()}

    for name, expected in EXPECTED_LONGEST_STREAKS.items():
        assert by_name[name].get_longest_streak() == expected, name

    tracker.close()


def test_seed_data_current_streaks(tmp_path):
    """Daily habits whose runs end yesterday report a current streak."""
    tracker = HabitTracker(db_path=str(tmp_path / "current.db"))
    by_name = {h.name: h for h in tracker.get_habits()}

    assert by_name["30-minute workout"].get_streak() == 28
    assert by_name["Read 20 pages"].get_streak() == 12
    assert by_name["Check in with someone"].get_streak() == 7
    assert by_name["Plan the day"].get_streak() == 1

    tracker.close()


def test_persistence_round_trip(tmp_path):
    """Habits, completions and totem state can survive a reopen."""
    db_path = str(tmp_path / "round.db")

    first = HabitTracker(db_path=db_path)
    first.add_habit("Drink water", "daily", "Body")
    first.complete_habit("Drink water")

    before_habits = {
        h.name: (h.period, h.category, len(h.completions))
        for h in first.get_habits()
    }
    before_categories = {
        c.name: (c.level, c.points) for c in first.get_categories()
    }
    first.close()

    second = HabitTracker(db_path=db_path)
    after_habits = {
        h.name: (h.period, h.category, len(h.completions))
        for h in second.get_habits()
    }
    after_categories = {
        c.name: (c.level, c.points) for c in second.get_categories()
    }

    assert "Drink water" in after_habits
    assert after_habits["Drink water"] == ("daily", "Body", 1)
    assert after_habits == before_habits
    assert after_categories == before_categories

    second.close()


def test_edit_habit_persists_and_keeps_history(tmp_path):
    """Editing name and category updates the habit & keeps its completions."""
    db_path = str(tmp_path / "edit.db")

    first = HabitTracker(db_path=db_path)
    target = "30-minute workout"
    before = next(h for h in first.get_habits() if h.name == target)
    completions_before = len(before.completions)

    first.edit_habit(target, new_name="Morning workout", new_category="Mind")
    edited = next(h for h in first.get_habits() if h.name == "Morning workout")
    assert edited.category == "Mind"
    assert edited.period == "daily"
    assert len(edited.completions) == completions_before
    assert all(h.name != target for h in first.get_habits())
    first.close()

    second = HabitTracker(db_path=db_path)
    names = [h.name for h in second.get_habits()]
    assert "Morning workout" in names
    assert target not in names

    reopened = next(h for h in second.get_habits() if h.name == "Morning workout")
    assert reopened.category == "Mind"
    assert len(reopened.completions) == completions_before
    second.close()


def test_edit_habit_changes_period(tmp_path):
    """Editing the period is stored and survives a reopen."""
    db_path = str(tmp_path / "editperiod.db")

    first = HabitTracker(db_path=db_path)
    first.edit_habit("Meal prep", new_period="daily")
    assert next(
        h for h in first.get_habits() if h.name == "Meal prep"
    ).period == "daily"
    first.close()

    second = HabitTracker(db_path=db_path)
    assert next(
        h for h in second.get_habits() if h.name == "Meal prep"
    ).period == "daily"
    second.close()


def test_edit_unknown_habit_returns_none(tmp_path):
    """Editing a habit that does not exist changes nothing and returns None."""
    tracker = HabitTracker(db_path=str(tmp_path / "noedit.db"))
    before = [h.name for h in tracker.get_habits()]

    assert tracker.edit_habit("Nonexistent", new_name="Whatever") is None
    assert [h.name for h in tracker.get_habits()] == before
    tracker.close()


def test_delete_habit_persists_and_cascades(tmp_path):
    """Deleting a habit removes it and its completions permanently."""
    db_path = str(tmp_path / "delete.db")

    first = HabitTracker(db_path=db_path)
    target = "30-minute workout"
    removed = next(h for h in first.get_habits() if h.name == target)
    removed_completions = len(removed.completions)
    total_before = sum(len(h.completions) for h in first.get_habits())

    first.delete_habit(target)
    assert all(h.name != target for h in first.get_habits())
    first.close()

    second = HabitTracker(db_path=db_path)
    assert len(second.get_habits()) == 9
    assert all(h.name != target for h in second.get_habits())

    total_after = sum(len(h.completions) for h in second.get_habits())
    assert total_after == total_before - removed_completions
    second.close()


def test_apply_decay_decays_stale_category(tmp_path):
    """A category left idle past the grace window loses points."""
    db_path = str(tmp_path / "decay.db")

    tracker = HabitTracker(db_path=db_path)
    body = find_category(tracker, "Body")
    body.level = 3
    body.points = 15.0

    stale = datetime.now() - timedelta(days=10)
    for habit in tracker.get_habits():
        if habit.category == "Body":
            habit.completions = [stale]

    tracker.apply_decay()
    assert body.level == 3
    assert body.points == pytest.approx(9.0)
    tracker.close()

    reopened = HabitTracker(db_path=db_path)
    body_again = find_category(reopened, "Body")
    assert body_again.level == 3
    assert body_again.points == pytest.approx(9.0)
    reopened.close()


def test_apply_decay_skips_recent_category(tmp_path):
    """Fresh seed data is in the grace window, so startup is unaffected."""
    tracker = HabitTracker(db_path=str(tmp_path / "recent.db"))

    before = {c.name: (c.level, c.points) for c in tracker.get_categories()}
    tracker.apply_decay()
    after = {c.name: (c.level, c.points) for c in tracker.get_categories()}

    assert after == before
    tracker.close()
