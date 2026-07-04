"""Habit definition and streak calculation."""

from datetime import date, datetime, timedelta


VALID_PERIODS = ("daily", "weekly")


class Habit:
    """A habit with a period, a category and its completions."""

    def __init__(self, name, period, category, created_at, completions=None):
        if period not in VALID_PERIODS:
            raise ValueError("Habit period must be 'daily' or 'weekly'.")
        self.name = name
        self.period = period
        self.category = category
        self.created_at = created_at
        self.completions = completions if completions is not None else []

    def complete(self):
        """Record a completion at the current time."""
        self.completions.append(datetime.now())

    def get_streak(self):
        """Return the current live streak."""
        if not self.completions:
            return 0

        if self.period == "daily":
            # Each completion collapses to its date, so several on the
            # same day count once. Most recent first.
            markers = sorted(
                set(map(lambda c: c.date(), self.completions)),
                reverse=True,
            )

            # A live streak needs a completion today or yesterday.
            today = datetime.now().date()
            if markers[0] not in (today, today - timedelta(days=1)):
                return 0

            step = timedelta(days=1)

        elif self.period == "weekly":
            # Each completion collapses to the Monday of its ISO week, so
            # several in one week count once. Most recent first.
            markers = sorted(
                set(map(
                    lambda c: date.fromisocalendar(
                        c.isocalendar()[0], c.isocalendar()[1], 1
                    ),
                    self.completions,
                )),
                reverse=True,
            )

            # A live streak needs a completion this week or last week.
            now = datetime.now()
            this_week = date.fromisocalendar(
                now.isocalendar()[0], now.isocalendar()[1], 1
            )
            if markers[0] not in (this_week, this_week - timedelta(weeks=1)):
                return 0

            step = timedelta(weeks=1)

        else:
            raise ValueError("Habit period must be 'daily' or 'weekly'.")

        # Count back while markers stay one step apart.
        streak = 1
        for i in range(1, len(markers)):
            if markers[i] == markers[0] - step * i:
                streak += 1
            else:
                break
        return streak

    def get_longest_streak(self):
        """Return the longest streak ever recorded."""
        if not self.completions:
            return 0

        if self.period == "daily":
            # Each completion collapses to its date.
            # Oldest first.
            markers = sorted(set(map(lambda c: c.date(), self.completions)))
            step = timedelta(days=1)

        elif self.period == "weekly":
            # Each completion collapses to the Monday of its ISO week.
            # Oldest first.
            markers = sorted(
                set(map(
                    lambda c: date.fromisocalendar(
                        c.isocalendar()[0], c.isocalendar()[1], 1
                    ),
                    self.completions,
                ))
            )
            step = timedelta(weeks=1)

        else:
            raise ValueError("Habit period must be 'daily' or 'weekly'.")

        # Track the best run of consecutive markers.
        longest = 1
        current = 1
        for i in range(1, len(markers)):
            if markers[i] == markers[i - 1] + step:
                current += 1
            else:
                current = 1
            if current > longest:
                longest = current
        return longest
