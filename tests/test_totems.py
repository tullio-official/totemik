"""Unit tests for the Category class."""

import pytest

from totemik.category import Category


def test_points_needed_grows_with_level():
    """_points_needed() follows round(10 * 1.4 ** (level - 1))."""
    assert Category("Body", level=1)._points_needed() == 10
    assert Category("Body", level=2)._points_needed() == 14
    assert Category("Body", level=3)._points_needed() == 20
    assert Category("Body", level=4)._points_needed() == 27


def test_points_accrue_by_multiplier_bracket():
    """Points accrue at streak 1, 4 and 8 with the x1, x2, x4 multipliers."""
    low = Category("Body")
    low.add_points(streak=1, period="daily")
    assert low.points == 1  # base 1 x1

    mid = Category("Body")
    mid.add_points(streak=4, period="daily")
    assert mid.points == 2  # base 1 x2

    high = Category("Body")
    high.add_points(streak=8, period="daily")
    assert high.points == 4  # base 1 x4


def test_level_up_carries_surplus():
    """Clearing the threshold raises the level and carries the surplus."""
    category = Category("Body", level=1, points=9.0)
    # +5 clears the level-1 threshold of 10
    category.add_points(streak=1, period="weekly")
    assert category.level == 2
    assert category.points == 4


def test_subtract_points_reduces_points():
    """One period past grace removes 0.10 of the current threshold."""
    category = Category("Body", level=3, points=15.0)
    category.subtract_points(1)  # 0.10 * 20 = 2.0
    assert category.level == 3
    assert category.points == pytest.approx(13.0)


def test_subtract_points_drops_level_with_carry():
    """A deduction below zero drops a level and carries the remainder down."""
    category = Category("Body", level=2, points=1.0)
    category.subtract_points(1)  # 0.10 * 14 = 1.4, points fall below zero
    assert category.level == 1
    assert category.points == pytest.approx(9.6)  # carried down, not negative


def test_subtract_points_clamps_at_level_one():
    """At level 1 the points floor at zero and the level holds."""
    category = Category("Body", level=1, points=2.0)
    category.subtract_points(50)
    assert category.level == 1
    assert category.points == 0.0


def test_progress_to_next_is_fraction():
    """progress_to_next() returns points over the threshold, within [0, 1)."""
    category = Category("Body", level=1, points=5.0)
    result = category.progress_to_next()
    assert result == 0.5
    assert 0.0 <= result < 1.0
