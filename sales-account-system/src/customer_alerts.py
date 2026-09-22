from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import create_tables, get_session
from src.models import Account, Activity, Order
from src.payment_manager import (
    calculate_amount_paid,
    calculate_order_status,
)


def get_customer_alerts(
    days_ahead: int = 7,
    as_of_date: date | None = None,
) -> list[dict]:
    """Return account, activity, payment, and delivery alerts."""

    if days_ahead < 0:
        raise ValueError(
            "days_ahead cannot be negative."
        )

    if as_of_date is None:
        as_of_date = date.today()

    alert_window_end = (
        as_of_date + timedelta(days=days_ahead)
    )

    session = get_session()
    alerts = []

    try:
        accounts = session.scalars(
            select(Account)
            .options(
                selectinload(Account.activities),
                selectinload(Account.orders).selectinload(
                    Order.payments
                ),
                selectinload(Account.orders).selectinload(
                    Order.fulfillment
                ),
            )
            .order_by(Account.company_name)
        ).all()

        for account in accounts:
            if account.next_follow_up_date is not None:
                if account.next_follow_up_date < as_of_date:
                    alerts.append(
                        {
                            "category": "ACCOUNT_FOLLOW_UP",
                            "priority": "HIGH",
                            "account_id": account.id,
                            "company_name": account.company_name,
                            "message": (
                                "Account follow-up is overdue."
                            ),
                            "date": account.next_follow_up_date,
                        }
                    )

                elif account.next_follow_up_date <= alert_window_end:
                    alerts.append(
                        {
                            "category": "ACCOUNT_FOLLOW_UP",
                            "priority": "MEDIUM",
                            "account_id": account.id,
                            "company_name": account.company_name,
                            "message": (
                                "Account follow-up is due soon."
                            ),
                            "date": account.next_follow_up_date,
                        }
                    )

            for activity in account.activities:
                if activity.next_action_date is None:
                    continue

                if activity.next_action_date > alert_window_end:
                    continue

                if activity.next_action_date < as_of_date:
                    priority = "HIGH"
                    message = (
                        f"Activity action overdue: "
                        f"{activity.next_action or activity.subject}"
                    )
                else:
                    priority = "MEDIUM"
                    message = (
                        f"Activity action due: "
                        f"{activity.next_action or activity.subject}"
                    )

                alerts.append(
                    {
                        "category": "ACTIVITY_ACTION",
                        "priority": priority,
                        "account_id": account.id,
                        "company_name": account.company_name,
                        "message": message,
                        "date": activity.next_action_date,
                    }
                )

            for order in account.orders:
                amount_paid = calculate_amount_paid(order)
                balance_due = order.total_amount - amount_paid

                if balance_due <= Decimal("0.00"):
                    continue

                payment_status = calculate_order_status(
                    total_amount=order.total_amount,
                    amount_paid=amount_paid,
                    due_date=order.due_date,
                    grace_period_end_date=(
                        order.grace_period_end_date
                    ),
                    as_of_date=as_of_date,
                )

                if payment_status == "overdue":
                    alerts.append(
                        {
                            "category": "PAYMENT",
                            "priority": "HIGH",
                            "account_id": account.id,
                            "company_name": account.company_name,
                            "message": (
                                f"Order {order.order_number} is "
                                f"overdue. Balance: "
                                f"${balance_due:,.2f}"
                            ),
                            "date": order.due_date,
                        }
                    )

                elif order.due_date <= alert_window_end:
                    alerts.append(
                        {
                            "category": "PAYMENT",
                            "priority": "HIGH",
                            "account_id": account.id,
                            "company_name": account.company_name,
                            "message": (
                                f"Order {order.order_number} payment "
                                f"is due. Balance: "
                                f"${balance_due:,.2f}"
                            ),
                            "date": order.due_date,
                        }
                    )

            for order in account.orders:
                if order.fulfillment is None:
                    continue

                fulfillment_status = (
                    order.fulfillment.fulfillment_status
                )

                if fulfillment_status in {
                    "delivered",
                    "cancelled",
                }:
                    continue

                alerts.append(
                    {
                        "category": "FULFILLMENT",
                        "priority": "MEDIUM",
                        "account_id": account.id,
                        "company_name": account.company_name,
                        "message": (
                            f"Order {order.order_number} fulfillment "
                            f"status: {fulfillment_status}"
                        ),
                        "date": order.order_date,
                    }
                )

        priority_order = {
            "HIGH": 0,
            "MEDIUM": 1,
            "LOW": 2,
        }

        return sorted(
            alerts,
            key=lambda alert: (
                priority_order.get(
                    alert["priority"],
                    9,
                ),
                alert["date"],
                alert["company_name"],
            ),
        )

    finally:
        session.close()


def print_alert(alert: dict) -> None:
    """Print one customer alert."""

    print(
        f"[{alert['priority']}] "
        f"{alert['category']} | "
        f"{alert['company_name']} | "
        f"{alert['date']}"
    )
    print(f"  {alert['message']}")


if __name__ == "__main__":
    create_tables()

    print("\nCustomer alerts")
    print("---------------")

    alerts = get_customer_alerts(days_ahead=7)

    if not alerts:
        print("No customer alerts.")
    else:
        for alert in alerts:
            print_alert(alert)

        print(f"\nTotal alerts: {len(alerts)}")
