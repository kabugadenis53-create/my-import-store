from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import create_tables, get_session
from src.models import Account, Activity, Contact


VALID_ACTIVITY_TYPES = {
    "call",
    "email",
    "meeting",
    "demo",
    "proposal",
    "follow_up",
    "note",
}


def add_activity(
    account_id: int,
    activity_type: str,
    activity_date: date,
    subject: str,
    contact_id: Optional[int] = None,
    notes: Optional[str] = None,
    next_action: Optional[str] = None,
    next_action_date: Optional[date] = None,
) -> Activity:
    """Add a sales activity to an account."""

    normalized_type = activity_type.strip().lower()
    subject = subject.strip()

    if normalized_type not in VALID_ACTIVITY_TYPES:
        valid_types = ", ".join(sorted(VALID_ACTIVITY_TYPES))
        raise ValueError(
            f"Invalid activity_type. Choose one of: {valid_types}"
        )

    if not subject:
        raise ValueError("subject cannot be empty.")

    if next_action_date is not None and not next_action:
        raise ValueError(
            "next_action is required when next_action_date is provided."
        )

    session = get_session()

    try:
        account = session.get(Account, account_id)

        if account is None:
            raise ValueError(
                f"No account found with ID {account_id}."
            )

        if contact_id is not None:
            contact = session.get(Contact, contact_id)

            if contact is None:
                raise ValueError(
                    f"No contact found with ID {contact_id}."
                )

            if contact.account_id != account_id:
                raise ValueError(
                    "The selected contact does not belong "
                    "to the selected account."
                )

        activity = Activity(
            account_id=account_id,
            contact_id=contact_id,
            activity_type=normalized_type,
            activity_date=activity_date,
            subject=subject,
            notes=notes,
            next_action=next_action,
            next_action_date=next_action_date,
        )

        session.add(activity)
        session.commit()
        session.refresh(activity)

        return activity

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def list_account_activities(
    account_id: int,
) -> list[Activity]:
    """Return all activities for one account."""

    session = get_session()

    try:
        account = session.get(Account, account_id)

        if account is None:
            raise ValueError(
                f"No account found with ID {account_id}."
            )

        activities = session.scalars(
            select(Activity)
            .options(selectinload(Activity.contact))
            .where(Activity.account_id == account_id)
            .order_by(
                Activity.activity_date.desc(),
                Activity.id.desc(),
            )
        ).all()

        return list(activities)

    finally:
        session.close()


def list_pending_actions(
    as_of_date: Optional[date] = None,
) -> list[Activity]:
    """Return activities with actions due by the selected date."""

    if as_of_date is None:
        as_of_date = date.today()

    session = get_session()

    try:
        activities = session.scalars(
            select(Activity)
            .options(
                selectinload(Activity.account),
                selectinload(Activity.contact),
            )
            .where(
                Activity.next_action_date.is_not(None),
                Activity.next_action_date <= as_of_date,
            )
            .order_by(Activity.next_action_date)
        ).all()

        return list(activities)

    finally:
        session.close()


def list_recent_activities(
    limit: int = 20,
) -> list[Activity]:
    """Return the most recent sales activities."""

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    session = get_session()

    try:
        activities = session.scalars(
            select(Activity)
            .options(
                selectinload(Activity.account),
                selectinload(Activity.contact),
            )
            .order_by(
                Activity.activity_date.desc(),
                Activity.id.desc(),
            )
            .limit(limit)
        ).all()

        return list(activities)

    finally:
        session.close()


def print_activity(activity: Activity) -> None:
    """Print one activity in a readable format."""

    contact_name = "No contact"

    if activity.contact is not None:
        contact_name = activity.contact.full_name

    account_name = "No account"

    if activity.account is not None:
        account_name = activity.account.company_name

    print(
        f"[{activity.id}] "
        f"{account_name} | "
        f"{activity.activity_date} | "
        f"{activity.activity_type.upper()} | "
        f"{activity.subject} | "
        f"Contact: {contact_name}"
    )

    if activity.notes:
        print(f"  Notes: {activity.notes}")

    if activity.next_action:
        print(
            f"  Next action: {activity.next_action} "
            f"on {activity.next_action_date}"
        )


if __name__ == "__main__":
    create_tables()

    print("\nPending sales actions")
    print("---------------------")

    pending_actions = list_pending_actions()

    if not pending_actions:
        print("No pending actions.")
    else:
        for activity in pending_actions:
            print_activity(activity)

    print("\nRecent account activities")
    print("-------------------------")

    recent_activities = list_recent_activities()

    if not recent_activities:
        print("No activities found.")
    else:
        for activity in recent_activities:
            print_activity(activity)
