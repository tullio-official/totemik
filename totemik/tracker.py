"""HabitTracker: coordinates the database and the in-memory objects."""

from datetime import date, datetime, timedelta

from totemik import db, seed
from totemik.habit import Habit, VALID_PERIODS
from totemik.category import Category, CATEGORY_NAMES


class HabitTracker:
    """Loads, stores and updates the habits and their totems."""

    def __init__(self, db_path="habits.db"):
        """Open the database and load all state into memory."""
        self.conn = db.get_connection(db_path)
        db.init_db(self.conn)
        self.habits = self._load_habits()
        self.categories = self._load_categories()

        # Seed a fresh database and reload.
        if not self.habits:
            seed.load(self)
            self.habits = self._load_habits()
            self._seed_totem_points()

        self.apply_decay()

    def add_habit(self, name, period, category):
        """Create a habit, store it, and keep it in memory."""
        habit = Habit(name, period, category, datetime.now())
        self.conn.execute(
            "INSERT INTO habits (name, period, category, created_at) "
            "VALUES (?, ?, ?, ?)",
            (habit.name, habit.period, habit.category,
             habit.created_at.isoformat()),
        )
        self.conn.commit()
        self.habits.append(habit)
        return habit

    def edit_habit(self, name, new_name=None, new_period=None,
                   new_category=None):
        """Change a habit's name, period or category, keeping its history."""
        habit = self._find_habit(name)
        if habit is None:
            return None

        # Anything left unspecified keeps its current value.
        new_name = new_name if new_name else habit.name
        new_period = new_period if new_period else habit.period
        new_category = new_category if new_category else habit.category

        if new_period not in VALID_PERIODS:
            raise ValueError("Habit period must be 'daily' or 'weekly'.")

        self.conn.execute(
            "UPDATE habits SET name = ?, period = ?, category = ? "
            "WHERE name = ?",
            (new_name, new_period, new_category, name),
        )
        self.conn.commit()

        habit.name = new_name
        habit.period = new_period
        habit.category = new_category
        return habit

    def delete_habit(self, name):
        """Remove a habit by name from memory and the database."""
        self.conn.execute("DELETE FROM habits WHERE name = ?", (name,))
        self.conn.commit()
        self.habits = [h for h in self.habits if h.name != name]

    def complete_habit(self, name):
        """Mark a habit done and update its totem."""
        habit = self._find_habit(name)
        if habit is None:
            return

        habit.complete()
        self.conn.execute(
            "INSERT INTO completions (habit_id, completed_at) VALUES (?, ?)",
            (self._habit_id(name), habit.completions[-1].isoformat()),
        )

        # Award totem points for this completion, then save the new state.
        category = self._find_category(habit.category)
        if category is not None:
            category.add_points(habit.get_streak(), habit.period)
            self._save_category(category)

        self.conn.commit()

    def apply_decay(self):
        """Apply inactivity decay to every category, then save the changes."""
        now = datetime.now()
        for category in self.categories:
            habits = [h for h in self.habits if h.category == category.name]
            completions = [c for h in habits for c in h.completions]
            if not completions:
                continue

            # Convert days past the grace window into missed periods.
            gap_days = (now - max(completions)).days
            weekly_only = all(h.period == "weekly" for h in habits)
            grace = 14 if weekly_only else 7
            step = 7 if weekly_only else 1

            past_grace = (gap_days - grace) // step
            if past_grace <= 0:
                continue

            category.subtract_points(past_grace)
            self._save_category(category)

        self.conn.commit()

    def _seed_totem_points(self):
        """Award totem points for the seeded history, in date order."""
        for habit in self.habits:
            category = self._find_category(habit.category)
            if category is None:
                continue

            # Collapse completions to period markers, oldest first.
            if habit.period == "weekly":
                markers = sorted(set(
                    date.fromisocalendar(
                        c.isocalendar()[0], c.isocalendar()[1], 1
                    )
                    for c in habit.completions
                ))
                step = timedelta(weeks=1)
            else:
                markers = sorted(set(c.date() for c in habit.completions))
                step = timedelta(days=1)

            streak = 0
            for i, marker in enumerate(markers):
                if i > 0 and marker == markers[i - 1] + step:
                    streak += 1
                else:
                    streak = 1
                category.add_points(streak, habit.period)

            self._save_category(category)
        self.conn.commit()

    def get_habits(self):
        """Return the in-memory habits."""
        return self.habits

    def get_categories(self):
        """Return the in-memory categories."""
        return self.categories

    def close(self):
        """Close the database connection."""
        self.conn.close()

    def _load_habits(self):
        """Read every habit and its completions from the database."""
        habits = []
        rows = self.conn.execute(
            "SELECT id, name, period, category, created_at FROM habits"
        ).fetchall()
        for row in rows:
            stamps = self.conn.execute(
                "SELECT completed_at FROM completions WHERE habit_id = ? "
                "ORDER BY completed_at",
                (row["id"],),
            ).fetchall()
            completions = [datetime.fromisoformat(s["completed_at"])
                           for s in stamps]
            habits.append(Habit(
                row["name"],
                row["period"],
                row["category"],
                datetime.fromisoformat(row["created_at"]),
                completions,
            ))
        return habits

    def _load_categories(self):
        """Read the five categories, creating them on a fresh database."""
        rows = self.conn.execute(
            "SELECT name, level, points FROM categories"
        ).fetchall()
        if not rows:
            self.conn.executemany(
                "INSERT INTO categories (name) VALUES (?)",
                [(name,) for name in CATEGORY_NAMES],
            )
            self.conn.commit()
            rows = self.conn.execute(
                "SELECT name, level, points FROM categories"
            ).fetchall()
        return [Category(r["name"], r["level"], r["points"]) for r in rows]

    def _save_category(self, category):
        """Write a category's level and points back to the database."""
        self.conn.execute(
            "UPDATE categories SET level = ?, points = ? WHERE name = ?",
            (category.level, category.points, category.name),
        )

    def _find_habit(self, name):
        """Return the in-memory habit with this name, or None."""
        for habit in self.habits:
            if habit.name == name:
                return habit
        return None

    def _find_category(self, name):
        """Return the category with this name, or None."""
        for category in self.categories:
            if category.name == name:
                return category
        return None

    def _habit_id(self, name):
        """Return the database id for a habit name, or None."""
        row = self.conn.execute(
            "SELECT id FROM habits WHERE name = ?", (name,)
        ).fetchone()
        return row["id"] if row else None
