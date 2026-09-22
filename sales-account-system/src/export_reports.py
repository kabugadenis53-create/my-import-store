import csv
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.account_scoring import score_all_accounts
from src.database import create_tables, get_session
from src.models import Account, Activity, Order
from src.payment_manager import calculate_amount_paid


REPORT_DIRECTORY = Path("data/reports")


def export_account_priorities() -> Path:
    """Export scored accounts to CSV."""

    REPORT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    scored_accounts = score_all_accounts()
    output_file = REPORT_DIRECTORY / "account_priorities.csv"

    fieldnames = [
        "account_id",
        "company_name",
        "industry",
        "sales_stage",
        "potential_value",
        "score",
        "priority",
        "activity_count",
        "latest_activity_date",
        "reasons",
    ]

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for account in scored_accounts:
            row = account.copy()
            row["potential_value"] = str(
                row["potential_value"]
            )
            row["reasons"] = "; ".join(row["reasons"])
            writer.writerow(row)

    return output_file


def export_payment_balances() -> Path:
    """Export order balances and payment statuses to CSV."""

    REPORT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    session = get_session()

    try:
        orders = session.scalars(
            select(Order)
            .options(selectinload(Order.payments))
            .order_by(Order.due_date)
        ).all()

        output_file = REPORT_DIRECTORY / "payment_balances.csv"

        fieldnames = [
            "order_id",
            "order_number",
            "account_id",
            "product_description",
            "order_date",
            "due_date",
            "grace_period_end_date",
            "total_amount",
            "amount_paid",
            "balance_due",
        ]

        with output_file.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
            )

            writer.writeheader()

            for order in orders:
                amount_paid = calculate_amount_paid(order)
                balance_due = (
                    order.total_amount - amount_paid
                )

                writer.writerow(
                    {
                        "order_id": order.id,
                        "order_number": order.order_number,
                        "account_id": order.account_id,
                        "product_description": (
                            order.product_description
                        ),
                        "order_date": order.order_date,
                        "due_date": order.due_date,
                        "grace_period_end_date": (
                            order.grace_period_end_date
                        ),
                        "total_amount": order.total_amount,
                        "amount_paid": amount_paid,
                        "balance_due": balance_due,
                    }
                )

        return output_file

    finally:
        session.close()


def export_activities() -> Path:
    """Export sales activities to CSV."""

    REPORT_DIRECTORY.mkdir(parents=True, exist_ok=True)

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
        ).all()

        output_file = REPORT_DIRECTORY / "sales_activities.csv"

        fieldnames = [
            "activity_id",
            "account_id",
            "company_name",
            "contact_id",
            "contact_name",
            "activity_type",
            "activity_date",
            "subject",
            "notes",
            "next_action",
            "next_action_date",
        ]

        with output_file.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
            )

            writer.writeheader()

            for activity in activities:
                writer.writerow(
                    {
                        "activity_id": activity.id,
                        "account_id": activity.account_id,
                        "company_name": (
                            activity.account.company_name
                            if activity.account
                            else ""
                        ),
                        "contact_id": activity.contact_id or "",
                        "contact_name": (
                            activity.contact.full_name
                            if activity.contact
                            else ""
                        ),
                        "activity_type": (
                            activity.activity_type
                        ),
                        "activity_date": (
                            activity.activity_date
                        ),
                        "subject": activity.subject,
                        "notes": activity.notes or "",
                        "next_action": (
                            activity.next_action or ""
                        ),
                        "next_action_date": (
                            activity.next_action_date or ""
                        ),
                    }
                )

        return output_file

    finally:
        session.close()


if __name__ == "__main__":
    create_tables()

    print("Exporting sales reports...\n")

    account_file = export_account_priorities()
    payment_file = export_payment_balances()
    activity_file = export_activities()

    print(f"Account priorities: {account_file}")
    print(f"Payment balances:   {payment_file}")
    print(f"Sales activities:   {activity_file}")
