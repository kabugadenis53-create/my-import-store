from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.database import create_tables, get_session
from src.models import Account, Order
from src.payment_manager import (
    calculate_amount_paid,
    calculate_order_status,
)


def money(value: Decimal | None) -> str:
    """Format a decimal value as currency."""

    if value is None:
        value = Decimal("0.00")

    return f"${value:,.2f}"


def get_dashboard_data(
    days_ahead: int = 7,
    as_of_date: date | None = None,
) -> dict:
    """Collect sales, account, payment, and follow-up statistics."""

    if days_ahead < 0:
        raise ValueError(
            "days_ahead cannot be negative."
        )

    if as_of_date is None:
        as_of_date = date.today()

    session = get_session()

    try:
        accounts = session.scalars(
            select(Account)
            .options(selectinload(Account.contacts))
            .order_by(Account.company_name)
        ).all()

        orders = session.scalars(
            select(Order)
            .options(selectinload(Order.payments))
            .order_by(Order.due_date)
        ).all()

        total_pipeline_value = sum(
            (
                account.potential_value
                for account in accounts
                if account.potential_value is not None
            ),
            Decimal("0.00"),
        )

        total_sales_value = sum(
            (
                order.total_amount
                for order in orders
            ),
            Decimal("0.00"),
        )

        total_collected = Decimal("0.00")
        total_outstanding = Decimal("0.00")
        overdue_balance = Decimal("0.00")

        paid_orders = 0
        partial_orders = 0
        pending_orders = 0
        due_orders = 0
        overdue_orders = 0

        upcoming_payments = []
        overdue_payments = []

        payment_window_end = (
            as_of_date + timedelta(days=days_ahead)
        )

        for order in orders:
            amount_paid = calculate_amount_paid(order)
            balance_due = order.total_amount - amount_paid

            total_collected += amount_paid
            total_outstanding += balance_due

            status = calculate_order_status(
                total_amount=order.total_amount,
                amount_paid=amount_paid,
                due_date=order.due_date,
                grace_period_end_date=(
                    order.grace_period_end_date
                ),
                as_of_date=as_of_date,
            )

            if status == "paid":
                paid_orders += 1
            elif status == "partial":
                partial_orders += 1
            elif status == "pending":
                pending_orders += 1
            elif status == "due":
                due_orders += 1
            elif status == "overdue":
                overdue_orders += 1

            if balance_due > Decimal("0.00"):
                if status == "overdue":
                    overdue_balance += balance_due

                    overdue_payments.append(
                        {
                            "order_number": order.order_number,
                            "balance_due": balance_due,
                            "due_date": order.due_date,
                            "grace_period_end_date": (
                                order.grace_period_end_date
                            ),
                            "status": status,
                        }
                    )

                elif order.due_date <= payment_window_end:
                    upcoming_payments.append(
                        {
                            "order_number": order.order_number,
                            "balance_due": balance_due,
                            "due_date": order.due_date,
                            "grace_period_end_date": (
                                order.grace_period_end_date
                            ),
                            "status": status,
                        }
                    )

        accounts_due_for_follow_up = [
            account
            for account in accounts
            if (
                account.next_follow_up_date is not None
                and account.next_follow_up_date <= as_of_date
            )
        ]

        stage_counts = {}

        for account in accounts:
            stage = account.sales_stage or "unknown"
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

        return {
            "as_of_date": as_of_date,
            "total_accounts": len(accounts),
            "total_contacts": sum(
                len(account.contacts)
                for account in accounts
            ),
            "total_pipeline_value": total_pipeline_value,
            "total_orders": len(orders),
            "total_sales_value": total_sales_value,
            "total_collected": total_collected,
            "total_outstanding": total_outstanding,
            "overdue_balance": overdue_balance,
            "paid_orders": paid_orders,
            "partial_orders": partial_orders,
            "pending_orders": pending_orders,
            "due_orders": due_orders,
            "overdue_orders": overdue_orders,
            "upcoming_payments": upcoming_payments,
            "overdue_payments": overdue_payments,
            "accounts_due_for_follow_up": (
                accounts_due_for_follow_up
            ),
            "stage_counts": stage_counts,
        }

    finally:
        session.close()


def print_dashboard(data: dict) -> None:
    """Print the sales dashboard."""

    print("\n" + "=" * 70)
    print("SALES ACCOUNT DEVELOPMENT DASHBOARD")
    print("=" * 70)
    print(f"As of: {data['as_of_date']}")

    print("\nAccount Summary")
    print("-" * 70)
    print(f"Total accounts:          {data['total_accounts']}")
    print(f"Total contacts:          {data['total_contacts']}")
    print(
        "Estimated pipeline:      "
        f"{money(data['total_pipeline_value'])}"
    )

    print("\nSales Summary")
    print("-" * 70)
    print(f"Total orders:            {data['total_orders']}")
    print(
        "Total sales value:       "
        f"{money(data['total_sales_value'])}"
    )
    print(
        "Total collected:         "
        f"{money(data['total_collected'])}"
    )
    print(
        "Outstanding balance:     "
        f"{money(data['total_outstanding'])}"
    )
    print(
        "Overdue balance:         "
        f"{money(data['overdue_balance'])}"
    )

    print("\nOrder Status")
    print("-" * 70)
    print(f"Paid orders:             {data['paid_orders']}")
    print(f"Partial orders:          {data['partial_orders']}")
    print(f"Pending orders:          {data['pending_orders']}")
    print(f"Due orders:              {data['due_orders']}")
    print(f"Overdue orders:          {data['overdue_orders']}")

    print("\nAccounts by Sales Stage")
    print("-" * 70)

    if not data["stage_counts"]:
        print("No account stages found.")
    else:
        for stage, count in sorted(
            data["stage_counts"].items()
        ):
            print(f"{stage}: {count}")

    print("\nUpcoming Payments")
    print("-" * 70)

    if not data["upcoming_payments"]:
        print("No payments due within the configured window.")
    else:
        for payment in data["upcoming_payments"]:
            print(
                f"{payment['order_number']} | "
                f"Balance: {money(payment['balance_due'])} | "
                f"Due: {payment['due_date']} | "
                f"Status: {payment['status']}"
            )

    print("\nOverdue Payments")
    print("-" * 70)

    if not data["overdue_payments"]:
        print("No overdue payments.")
    else:
        for payment in data["overdue_payments"]:
            print(
                f"{payment['order_number']} | "
                f"Balance: {money(payment['balance_due'])} | "
                f"Due: {payment['due_date']} | "
                f"Grace ended: "
                f"{payment['grace_period_end_date']}"
            )

    print("\nAccounts Requiring Follow-up")
    print("-" * 70)

    if not data["accounts_due_for_follow_up"]:
        print("No accounts currently require follow-up.")
    else:
        for account in data["accounts_due_for_follow_up"]:
            print(
                f"[{account.id}] "
                f"{account.company_name} | "
                f"Stage: {account.sales_stage} | "
                f"Follow-up: "
                f"{account.next_follow_up_date}"
            )

    print("\n" + "=" * 70)


if __name__ == "__main__":
    create_tables()

    dashboard_data = get_dashboard_data(
        days_ahead=7
    )

    print_dashboard(dashboard_data)
