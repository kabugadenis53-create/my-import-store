from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import create_tables, get_session
from src.models import Account, Order
from src.payment_manager import (
    calculate_amount_paid,
    calculate_order_status,
)


def get_customer_summary(account_id: int) -> dict:
    """Return a complete post-sale summary for one account."""

    session = get_session()

    try:
        account = session.scalar(
            select(Account)
            .options(
                selectinload(Account.contacts),
                selectinload(Account.orders).selectinload(
                    Order.payments
                ),
                selectinload(Account.orders).selectinload(
                    Order.fulfillment
                ),
                selectinload(Account.activities),
            )
            .where(Account.id == account_id)
        )

        if account is None:
            raise ValueError(
                f"No account found with ID {account_id}."
            )

        total_sales = Decimal("0.00")
        total_paid = Decimal("0.00")
        total_outstanding = Decimal("0.00")

        order_summaries = []

        for order in account.orders:
            amount_paid = calculate_amount_paid(order)
            balance_due = order.total_amount - amount_paid

            payment_status = calculate_order_status(
                total_amount=order.total_amount,
                amount_paid=amount_paid,
                due_date=order.due_date,
                grace_period_end_date=(
                    order.grace_period_end_date
                ),
            )

            fulfillment_status = "not_started"
            customer_accepted = False
            tracking_number = None
            delivery_date = None

            if order.fulfillment is not None:
                fulfillment_status = (
                    order.fulfillment.fulfillment_status
                )
                customer_accepted = (
                    order.fulfillment.customer_accepted
                )
                tracking_number = (
                    order.fulfillment.tracking_number
                )
                delivery_date = (
                    order.fulfillment.delivery_date
                )

            total_sales += order.total_amount
            total_paid += amount_paid
            total_outstanding += balance_due

            order_summaries.append(
                {
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "product_description": (
                        order.product_description
                    ),
                    "order_date": order.order_date,
                    "due_date": order.due_date,
                    "total_amount": order.total_amount,
                    "amount_paid": amount_paid,
                    "balance_due": balance_due,
                    "payment_status": payment_status,
                    "fulfillment_status": fulfillment_status,
                    "customer_accepted": customer_accepted,
                    "tracking_number": tracking_number,
                    "delivery_date": delivery_date,
                }
            )

        recent_activities = sorted(
            account.activities,
            key=lambda activity: (
                activity.activity_date,
                activity.id,
            ),
            reverse=True,
        )[:5]

        return {
            "account_id": account.id,
            "company_name": account.company_name,
            "industry": account.industry,
            "sales_stage": account.sales_stage,
            "account_owner": account.account_owner,
            "potential_value": (
                account.potential_value
                or Decimal("0.00")
            ),
            "next_follow_up_date": (
                account.next_follow_up_date
            ),
            "contacts": list(account.contacts),
            "orders": order_summaries,
            "total_sales": total_sales,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding,
            "recent_activities": recent_activities,
        }

    finally:
        session.close()


def print_customer_summary(summary: dict) -> None:
    """Print a complete account summary."""

    print("\n" + "=" * 70)
    print(
        f"CUSTOMER SUMMARY: "
        f"{summary['company_name']}"
    )
    print("=" * 70)

    print(f"Account ID:       {summary['account_id']}")
    print(
        f"Industry:         "
        f"{summary['industry'] or 'Not set'}"
    )
    print(f"Sales stage:      {summary['sales_stage']}")
    print(
        f"Account owner:    "
        f"{summary['account_owner'] or 'Not set'}"
    )
    print(
        f"Potential value:  "
        f"${summary['potential_value']:,.2f}"
    )
    print(
        f"Next follow-up:   "
        f"{summary['next_follow_up_date'] or 'Not set'}"
    )

    print("\nContacts")
    print("-" * 70)

    if not summary["contacts"]:
        print("No contacts found.")
    else:
        for contact in summary["contacts"]:
            label = (
                "PRIMARY"
                if contact.is_primary
                else "SECONDARY"
            )

            print(
                f"[{contact.id}] "
                f"{contact.full_name} | "
                f"{contact.job_title or 'No title'} | "
                f"{contact.email or 'No email'} | "
                f"{label}"
            )

    print("\nFinancial Summary")
    print("-" * 70)
    print(
        f"Total sales:      "
        f"${summary['total_sales']:,.2f}"
    )
    print(
        f"Total paid:       "
        f"${summary['total_paid']:,.2f}"
    )
    print(
        f"Outstanding:      "
        f"${summary['total_outstanding']:,.2f}"
    )

    print("\nOrders")
    print("-" * 70)

    if not summary["orders"]:
        print("No orders found.")
    else:
        for order in summary["orders"]:
            accepted = (
                "YES"
                if order["customer_accepted"]
                else "NO"
            )

            tracking = (
                order["tracking_number"]
                or "None"
            )

            delivery_date = (
                order["delivery_date"]
                or "Not delivered"
            )

            print(
                f"[{order['order_id']}] "
                f"{order['order_number']} | "
                f"Total: "
                f"${order['total_amount']:,.2f} | "
                f"Paid: "
                f"${order['amount_paid']:,.2f} | "
                f"Balance: "
                f"${order['balance_due']:,.2f}"
            )

            print(
                f"  Payment: "
                f"{order['payment_status']} | "
                f"Fulfillment: "
                f"{order['fulfillment_status']} | "
                f"Accepted: {accepted}"
            )

            print(
                f"  Due: {order['due_date']} | "
                f"Delivery: {delivery_date} | "
                f"Tracking: {tracking}"
            )

    print("\nRecent Activities")
    print("-" * 70)

    if not summary["recent_activities"]:
        print("No activities found.")
    else:
        for activity in summary["recent_activities"]:
            print(
                f"[{activity.id}] "
                f"{activity.activity_date} | "
                f"{activity.activity_type.upper()} | "
                f"{activity.subject}"
            )

            if activity.next_action:
                print(
                    f"  Next action: "
                    f"{activity.next_action} "
                    f"on {activity.next_action_date}"
                )

    print("\n" + "=" * 70)


def list_account_ids() -> list[int]:
    """Return all account IDs."""

    session = get_session()

    try:
        accounts = session.scalars(
            select(Account).order_by(Account.company_name)
        ).all()

        return [account.id for account in accounts]

    finally:
        session.close()


if __name__ == "__main__":
    create_tables()

    account_ids = list_account_ids()

    if not account_ids:
        print("No accounts found.")
    else:
        for account_id in account_ids:
            summary = get_customer_summary(account_id)
            print_customer_summary(summary)
