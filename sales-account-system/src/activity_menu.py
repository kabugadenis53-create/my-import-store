from datetime import date, datetime
from typing import Optional

from src.activity_manager import (
    add_activity,
    list_account_activities,
    list_pending_actions,
    print_activity,
)


def read_positive_integer(prompt: str) -> int:
    """Read a positive integer."""

    while True:
        value = input(prompt).strip()

        try:
            number = int(value)

            if number <= 0:
                print("Value must be greater than zero.")
                continue

            return number

        except ValueError:
            print("Please enter a valid whole number.")


def read_date(prompt: str) -> date:
    """Read a required date in YYYY-MM-DD format."""

    while True:
        value = input(prompt).strip()

        try:
            return datetime.strptime(
                value,
                "%Y-%m-%d",
            ).date()

        except ValueError:
            print("Please use the format YYYY-MM-DD.")


def read_optional_date(
    prompt: str,
) -> Optional[date]:
    """Read an optional date in YYYY-MM-DD format."""

    while True:
        value = input(prompt).strip()

        if not value:
            return None

        try:
            return datetime.strptime(
                value,
                "%Y-%m-%d",
            ).date()

        except ValueError:
            print("Please use the format YYYY-MM-DD.")


def read_optional_text(
    prompt: str,
) -> Optional[str]:
    """Read optional text."""

    value = input(prompt).strip()
    return value or None


def add_activity_from_menu() -> None:
    """Create a sales activity through the menu."""

    print("\nAdd Sales Activity")
    print("------------------")

    account_id = read_positive_integer(
        "Account ID: "
    )

    contact_value = input(
        "Contact ID [optional]: "
    ).strip()

    contact_id = (
        int(contact_value)
        if contact_value
        else None
    )

    print("\nActivity types:")
    print("call")
    print("email")
    print("meeting")
    print("demo")
    print("proposal")
    print("follow_up")
    print("note")

    activity_type = input(
        "Activity type: "
    ).strip()

    activity_date = read_date(
        "Activity date [YYYY-MM-DD]: "
    )

    subject = input("Subject: ").strip()
    notes = read_optional_text("Notes: ")
    next_action = read_optional_text(
        "Next action [optional]: "
    )

    next_action_date = read_optional_date(
        "Next action date "
        "[YYYY-MM-DD, optional]: "
    )

    activity = add_activity(
        account_id=account_id,
        contact_id=contact_id,
        activity_type=activity_type,
        activity_date=activity_date,
        subject=subject,
        notes=notes,
        next_action=next_action,
        next_action_date=next_action_date,
    )

    print(
        f"\nActivity created successfully: "
        f"[{activity.id}] {activity.subject}"
    )


def view_account_activities_from_menu() -> None:
    """Display activities for one account."""

    print("\nAccount Activity History")
    print("-----------------------")

    account_id = read_positive_integer(
        "Account ID: "
    )

    activities = list_account_activities(account_id)

    if not activities:
        print("No activities found.")
        return

    for activity in activities:
        print_activity(activity)


def view_pending_actions_from_menu() -> None:
    """Display overdue and due activity actions."""

    print("\nPending Sales Actions")
    print("---------------------")

    actions = list_pending_actions()

    if not actions:
        print("No pending actions.")
        return

    for activity in actions:
        print_activity(activity)


def show_activity_menu() -> None:
    """Display activity-management operations."""

    while True:
        print("\nSales Activity Operations")
        print("------------------------")
        print("1. Add sales activity")
        print("2. View account activity history")
        print("3. View pending actions")
        print("0. Return to main menu")

        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                add_activity_from_menu()

            elif choice == "2":
                view_account_activities_from_menu()

            elif choice == "3":
                view_pending_actions_from_menu()

            elif choice == "0":
                break

            else:
                print("Invalid option.")

        except ValueError as error:
            print(f"\nOperation failed: {error}")

        except Exception as error:
            print(
                "\nUnexpected error: "
                f"{type(error).__name__}: {error}"
            )
