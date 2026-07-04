"""Predefined habits and four weeks of example data."""

from datetime import date, datetime, time, timedelta


PREDEFINED_HABITS = [
    ("30-minute workout", "daily", "Body"),
    ("Meal prep", "weekly", "Body"),
    ("Read 20 pages", "daily", "Mind"),
    ("Study something new", "weekly", "Mind"),
    ("Check in with someone", "daily", "Kin"),
    ("Meet up with a friend", "weekly", "Kin"),
    ("Plan the day", "daily", "Craft"),
    ("Weekly review", "weekly", "Craft"),
    ("Journal entry", "daily", "Self"),
    ("Creative practice", "weekly", "Self"),
]

# Day offsets to complete for each daily habit (1 means yesterday).
DAILY_PATTERNS = {
    "30-minute workout": list(range(1, 29)),
    "Read 20 pages": list(range(15, 29)) + list(range(1, 13)),
    "Check in with someone": list(range(1, 8)),
    "Plan the day": list(range(1, 29, 2)),
    "Journal entry": list(range(22, 29)) + list(range(1, 4)),
}

# Week offsets to complete for each weekly habit (1 means last week).
WEEKLY_PATTERNS = {
    "Meal prep": [1, 2, 3, 4],
    "Study something new": [1, 3, 4],
    "Meet up with a friend": [1, 2],
    "Weekly review": [1, 2, 3],
    "Creative practice": [1, 4],
}


def load(tracker):
    """Populate the database once."""
    today = date.today()
    noon = time(12, 0)

    # Weekly completions sit on Mondays. Anchor to the Monday of the week that
    # holds yesterday, so every marker falls inside the 28 days behind today.
    yesterday = today - timedelta(days=1)
    last_monday = yesterday - timedelta(days=yesterday.weekday())

    for name, period, category in PREDEFINED_HABITS:
        tracker.add_habit(name, period, category)
        habit_id = tracker.conn.execute(
            "SELECT id FROM habits WHERE name = ?", (name,)
        ).fetchone()["id"]

        if period == "daily":
            stamps = [
                datetime.combine(today - timedelta(days=d), noon)
                for d in DAILY_PATTERNS[name]
            ]
        else:
            stamps = [
                datetime.combine(last_monday - timedelta(weeks=w - 1), noon)
                for w in WEEKLY_PATTERNS[name]
            ]

        # Write the rows straight to the database. HabitTracker reloads the
        # habits afterwards, so the objects in memory pick up the completions.
        tracker.conn.executemany(
            "INSERT INTO completions (habit_id, completed_at) VALUES (?, ?)",
            [(habit_id, s.isoformat()) for s in stamps],
        )

    tracker.conn.commit()
