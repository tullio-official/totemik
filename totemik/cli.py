"""Terminal menu loop for totemik."""

from totemik import tracker
from totemik.tracker import HabitTracker
from totemik import analytics
from totemik.category import TOTEMS, CATEGORY_NAMES
from totemik.habit import VALID_PERIODS


MENU = """
=== totemik ===
1. View all habits
2. Add a habit
3. Edit a habit
4. Delete a habit
5. Complete a habit
6. Analytics
7. View totems
8. Exit
"""

ANALYTICS_MENU = """
--- Analytics ---
1. Longest streak (all habits)
2. Longest streak (one habit)
3. Habits by period
4. Completion rate (one habit)
5. Back
"""


def run():
    """Run the main menu loop."""
    tracker = HabitTracker()
    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()

        if choice == "1":
            view_all_habits(tracker)
        elif choice == "2":
            add_habit(tracker)
        elif choice == "3":
            edit_habit(tracker)
        elif choice == "4":
            delete_habit(tracker)
        elif choice == "5":
            complete_habit(tracker)
        elif choice == "6":
            analytics_menu(tracker)
        elif choice == "7":
            view_totems(tracker)
        elif choice == "8":
            break
        else:
            print("Please choose a number from 1 to 8.")

        input("\nPress Enter to continue...")

    print("Saving and closing...")
    tracker.close()
    print("Goodbye!")


def view_all_habits(tracker):
    """Print every habit with both streak values."""
    habits = tracker.get_habits()
    if not habits:
        print("No habits yet.")
        return

    for habit in habits:
        print(
            f"- {habit.name} [{habit.period.capitalize()} | {habit.category.title()}]\n"
            f"  Current streak: {habit.get_streak()} (Longest: {habit.get_longest_streak()})"
        )


def add_habit(tracker):
    """Prompt for a new habit and create it."""
    name = input("Name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return
    if any(h.name == name for h in tracker.get_habits()):
        print("A habit with that name already exists.")
        return

    period = input("Period (daily/weekly): ").strip().lower()
    if period not in VALID_PERIODS:
        print("Period must be daily or weekly.")
        return

    prompt = f"Category ({', '.join(CATEGORY_NAMES)}): "
    category = input(prompt).strip().title()
    if category not in CATEGORY_NAMES:
        print("Category must be one of: " + ", ".join(CATEGORY_NAMES) + ".")
        return

    tracker.add_habit(name, period, category)
    print(f"Added {name}.")


def edit_habit(tracker):
    """Prompt for a habit and change its name, period or category."""
    name = input("Name to edit: ").strip()
    habit = next((h for h in tracker.get_habits() if h.name == name), None)
    if habit is None:
        print("No habit by that name.")
        return

    print("Leave a field blank to keep it unchanged.")

    new_name = input(f"New name [{habit.name}]: ").strip()
    if new_name and any(h.name == new_name for h in tracker.get_habits()):
        print("A habit with that name already exists.")
        return

    new_period = input(
        f"New period (daily/weekly) [{habit.period}]: "
    ).strip().lower()
    if new_period and new_period not in VALID_PERIODS:
        print("Period must be daily or weekly.")
        return

    prompt = f"New category ({', '.join(CATEGORY_NAMES)}) [{habit.category}]: "
    new_category = input(prompt).strip().title()
    if new_category and new_category not in CATEGORY_NAMES:
        print("Category must be one of: " + ", ".join(CATEGORY_NAMES) + ".")
        return

    tracker.edit_habit(
        name,
        new_name=new_name or None,
        new_period=new_period or None,
        new_category=new_category or None,
    )
    print(f"Updated {name}.")


def delete_habit(tracker):
    """Prompt for a name and delete it."""
    name = input("Name to delete: ").strip()
    if not any(h.name == name for h in tracker.get_habits()):
        print("No habit by that name.")
        return

    if input(f"Delete '{name}'? (y/n): ").strip().lower() != "y":
        print("Cancelled.")
        return

    tracker.delete_habit(name)
    print(f"Deleted {name}.")


def complete_habit(tracker):
    """Prompt for a name and mark it done."""
    name = input("Name to complete: ").strip()
    if not any(h.name == name for h in tracker.get_habits()):
        print("No habit by that name.")
        return

    tracker.complete_habit(name)
    print(f"Marked {name} as done.")


def analytics_menu(tracker):
    """Run the analytics submenu."""
    while True:
        print(ANALYTICS_MENU)
        choice = input("Choose an option: ").strip()

        if choice == "1":
            habit = analytics.longest_streak_all(tracker.get_habits())
            if habit is None:
                print("No habits yet.")
            else:
                print(
                    f"{habit.name} has the longest streak: "
                    f"{habit.get_longest_streak()}."
                )

        elif choice == "2":
            habit = _ask_for_habit(tracker)
            if habit is not None:
                print(
                    f"{habit.name} longest streak: "
                    f"{analytics.longest_streak_one(habit)}."
                )

        elif choice == "3":
            period = input("Period (daily/weekly): ").strip().lower()
            if period not in VALID_PERIODS:
                print("Period must be daily or weekly.")
                continue
            matches = analytics.list_habits_by_period(
                tracker.get_habits(), period
            )
            if not matches:
                print(f"No {period} habits.")
            else:
                for habit in matches:
                    print(f"{habit.name} ({habit.category.title()})")

        elif choice == "4":
            habit = _ask_for_habit(tracker)
            if habit is not None:
                rate = analytics.completion_rate(habit)
                print(f"{habit.name} completion rate (30 days): {rate:.1f}%.")

        elif choice == "5":
            break

        else:
            print("Please choose a number from 1 to 5.")


def view_totems(tracker):
    """Print each category as a totem with a progress bar."""
    width = 20
    for category in tracker.get_categories():
        needed = category._points_needed()
        filled = int(category.progress_to_next() * width)
        bar = "=" * filled + " " * (width - filled)
        print(
            f"{category.name} - {TOTEMS[category.name]}  "
            f"Lv.{category.level}  [{bar}]  "
            f"{int(category.points)}/{needed} pts"
        )


def _ask_for_habit(tracker):
    """Prompt for a habit name and return the object, or None if missing."""
    name = input("Habit name: ").strip()
    for habit in tracker.get_habits():
        if habit.name == name:
            return habit
    print("No habit by that name.")
    return None
