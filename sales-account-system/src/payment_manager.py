from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import create_tables, get_session
from src.models import Account, Order, Payment


VALID_STATUSES = {
    "pending",
    "partial",
    "paid",
    "due",
    "overdue",
}


def calculate_order_status(
    total_amount: Decimal,
    amount_paid: Decimal,
    due_date: date,
    grace_period_end_date: date,
    as_of_date: Optional[date] = None,
) -> str:
    """
    Calculate the current payment status of an order.

    Status rules:

    - paid: the full amount has been received
    - overdue: the grace period has ended and a balance remains
    - due: the due date has arrived but the grace period has not ended
    - partial: some payment has been received before the due date
    - pending: no payment has been received before the due date
    """

    if as_of_date is None:
        as_of_date = date.today()

    if amount_paid >= total_amount:
        return "paid"

    if as_of_date > grace_period_end_date:
        return "overdue"

    if as_of_date >= due_date:
        return "due"

    if amount_paid > Decimal("0.00"):
        return "partial"

    return "pending"


def calculate_amount_paid(order: Order) -> Decimal:
    """Return the total amount paid against an order."""

    return sum(
        (
            payment.amount
            for payment in order.payments
        ),
        Decimal("0.00"),
    )


def create_order(
    account_id: int,
    order_number: str,
    product_description: str,
    order_date: date,
    due_date: date,
    total_amount: Decimal,
    grace_period_days: int = 0,
    notes: Optional[str] = None,
) -> Order:
    """Create an actual sale or invoice."""

    order_number = order_number.strip()
    product_description = product_description.strip()

    if not order_number:
        raise ValueError("order_number cannot be empty.")

    if not product_description:
        raise ValueError(
            "product_description cannot be empty."
        )

    if total_amount <= Decimal("0.00"):
        raise ValueError(
            "total_amount must be greater than zero."
        )

    if grace_period_days < 0:
        raise ValueError(
            "grace_period_days cannot be negative."
        )

    if due_date < order_date:
        raise ValueError(
            "due_date cannot be earlier than order_date."
        )

    session = get_session()

    try:
        account = session.get(Account, account_id)

        if account is None:
            raise ValueError(
                f"No account found with ID {account_id}."
            )

        existing_order = session.scalar(
            select(Order).where(
                Order.order_number == order_number
            )
        )

        if existing_order is not None:
            raise ValueError(
                f"Order already exists: {order_number}"
            )

        order = Order(
            account_id=account_id,
            order_number=order_number,
            product_description=product_description,
            order_date=order_date,
            due_date=due_date,
            total_amount=total_amount,
            grace_period_days=grace_period_days,
            notes=notes,
        )

        session.add(order)
        session.commit()
        session.refresh(order)

        return order

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def record_payment(
    order_id: int,
    payment_date: date,
    amount: Decimal,
    payment_method: Optional[str] = None,
    reference: Optional[str] = None,
    notes: Optional[str] = None,
) -> Payment:
    """Record a payment received against an order."""

    if amount <= Decimal("0.00"):
        raise ValueError(
            "Payment amount must be greater than zero."
        )

    session = get_session()

    try:
        order = session.scalar(
            select(Order)
            .options(selectinload(Order.payments))
            .where(Order.id == order_id)
        )

        if order is None:
            raise ValueError(
                f"No order found with ID {order_id}."
            )

        current_paid = calculate_amount_paid(order)
        remaining_balance = (
            order.total_amount - current_paid
        )

        if amount > remaining_balance:
            raise ValueError(
                "Payment would exceed the order total. "
                f"Balance remaining: "
                f"${remaining_balance:,.2f}"
            )

        payment = Payment(
            order_id=order_id,
            payment_date=payment_date,
            amount=amount,
            payment_method=payment_method,
            reference=reference,
            notes=notes,
        )

        session.add(payment)
        session.commit()
        session.refresh(payment)

        return payment

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def get_order_payment_summary(
    order_id: int,
    as_of_date: Optional[date] = None,
) -> dict:
    """Return payment totals and current payment status."""

    if as_of_date is None:
        as_of_date = date.today()

    session = get_session()

    try:
        order = session.scalar(
            select(Order)
            .options(selectinload(Order.payments))
            .where(Order.id == order_id)
        )

        if order is None:
            raise ValueError(
                f"No order found with ID {order_id}."
            )

        amount_paid = calculate_amount_paid(order)
        balance_due = order.total_amount - amount_paid

        status = calculate_order_status(
            total_amount=order.total_amount,
            amount_paid=amount_paid,
            due_date=order.due_date,
            grace_period_end_date=(
                order.grace_period_end_date
            ),
            as_of_date=as_of_date,
        )

        return {
            "order_id": order.id,
            "order_number": order.order_number,
            "account_id": order.account_id,
            "product_description": (
                order.product_description
            ),
            "order_date": order.order_date,
            "total_amount": order.total_amount,
            "amount_paid": amount_paid,
            "balance_due": balance_due,
            "due_date": order.due_date,
            "grace_period_days": order.grace_period_days,
            "grace_period_end_date": (
                order.grace_period_end_date
            ),
            "status": status,
        }

    finally:
        session.close()


def list_orders(
    as_of_date: Optional[date] = None,
) -> list[dict]:
    """Return all orders with their current payment summaries."""

    if as_of_date is None:
        as_of_date = date.today()

    session = get_session()

    try:
        orders = session.scalars(
            select(Order)
            .options(selectinload(Order.payments))
            .order_by(Order.due_date, Order.order_number)
        ).all()

        summaries = []

        for order in orders:
            amount_paid = calculate_amount_paid(order)
            balance_due = order.total_amount - amount_paid

            status = calculate_order_status(
                total_amount=order.total_amount,
                amount_paid=amount_paid,
                due_date=order.due_date,
                grace_period_end_date=(
                    order.grace_period_end_date
                ),
                as_of_date=as_of_date,
            )

            summaries.append(
                {
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "account_id": order.account_id,
                    "product_description": (
                        order.product_description
                    ),
                    "order_date": order.order_date,
                    "total_amount": order.total_amount,
                    "amount_paid": amount_paid,
                    "balance_due": balance_due,
                    "due_date": order.due_date,
                    "grace_period_days": (
                        order.grace_period_days
                    ),
                    "grace_period_end_date": (
                        order.grace_period_end_date
                    ),
                    "status": status,
                }
            )

        return summaries

    finally:
        session.close()


def print_order_summary(summary: dict) -> None:
    """Print one order-payment summary."""

    print(
        f"[{summary['order_id']}] "
        f"{summary['order_number']} | "
        f"Total: "
        f"${summary['total_amount']:,.2f} | "
        f"Paid: "
        f"${summary['amount_paid']:,.2f} | "
        f"Balance: "
        f"${summary['balance_due']:,.2f} | "
        f"Due: "
        f"{summary['due_date']} | "
        f"Grace ends: "
        f"{summary['grace_period_end_date']} | "
        f"Status: "
        f"{summary['status']}"
    )


def print_payment_summary(
    order_id: int,
) -> None:
    """Print one specific order's payment summary."""

    summary = get_order_payment_summary(order_id)
    print_order_summary(summary)


if __name__ == "__main__":
    create_tables()

    print("\nOrders and payment status")
    print("-------------------------")

    summaries = list_orders()

    if not summaries:
        print("No orders found.")
    else:
        for summary in summaries:
            print_order_summary(summary)
