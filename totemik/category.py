"""Category and totem progression (points, levels, decay)."""


TOTEMS = {
    "Body": "Bear",
    "Mind": "Owl",
    "Kin": "Wolf",
    "Craft": "Beaver",
    "Self": "Fox",
}

CATEGORY_NAMES = list(TOTEMS.keys())


class Category:
    """A totem that levels up on points and decays when idle."""

    def __init__(self, name, level=1, points=0.0):
        self.name = name
        self.level = level
        self.points = points

    def _points_needed(self):
        """Return the points needed to complete the current level."""
        return round(10 * 1.4 ** (self.level - 1))

    def add_points(self, streak, period):
        """Award points for one completion and level up if earned."""
        base = 5 if period == "weekly" else 1

        # Longer streaks multiply the points.
        if streak >= 8:
            multiplier = 4
        elif streak >= 4:
            multiplier = 2
        else:
            multiplier = 1
        self.points += base * multiplier

        # Spend the threshold for each level gained, keeping the surplus.
        while self.points >= self._points_needed():
            self.points -= self._points_needed()
            self.level += 1

    def subtract_points(self, periods_inactive):
        """Subtract points for inactivity beyond the grace window."""
        for _ in range(int(periods_inactive)):
            self.points -= 0.10 * self._points_needed()

            # Drop a level when points go negative, or floor at level 1.
            if self.points < 0:
                if self.level > 1:
                    self.level -= 1
                    self.points += self._points_needed()
                else:
                    self.points = 0.0
                    break

    def progress_to_next(self):
        """Return the fraction of progress toward the next level."""
        return self.points / self._points_needed()
