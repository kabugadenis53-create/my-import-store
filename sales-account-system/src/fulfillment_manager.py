from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import create_tables, get_session
from src.models import Fulfillment, Order
from src.payment_manager import calculate_amount_paid


VALID_FULFILLMENT_STATUSES = {
    "not_started",
    "processing",
    "ready",
    "shipped",
    "delivered",
    "cancelled",
}


def calculate_item_total(order: Order) -> Decimal:
    """Calculate the total value of all product items."""

    return sum(
        (
            item.line_total
            for item in order.items
        ),
        Decimal("0.00"),
    )


def get_fulfillment_status(
    order_id: int,
    require_full_payment: bool = False,
) -> dict:
    """Check whether an order is ready for fulfillment."""

    session = get_session()

    try:
        order = session.scalar(
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.payments),
                selectinload(Order.fulfillment),
            )
            .where(Order.id == order_id)
        )

        if order is None:
            raise ValueError(
                f"No order found with ID {order_id}."
            )

        item_total = calculate_item_total(order)
        amount_paid = calculate_amount_paid(order)
        balance_due = order.total_amount - amount_paid

        reasons = []
        ready = True

        if not order.items:
            ready = False
            reasons.append(
                "No product items have been added."
            )

        if item_total != order.total_amount:
            ready = False
            reasons.append(
                "Product-item total does not match "
                "the official order total."
            )

        if require_full_payment and balance_due > Decimal("0.00"):
            ready = False
            reasons.append(
                "Full payment has not been received."
            )

        if ready:
            readiness_status = "READY"
            reasons.append(
                "Order passed all fulfillment checks."
            )
        else:
            readiness_status = "NOT_READY"

        fulfillment_status = "not_started"

        if order.fulfillment is not None:
            fulfillment_status = (
                order.fulfillment.fulfillment_status
            )

        customer_accepted = False

        if order.fulfillment is not None:
            customer_accepted = (
                order.fulfillment.customer_accepted
            )

        return {
            "order_id": order.id,
            "order_number": order.order_number,
            "readiness_status": readiness_status,
            "ready": ready,
            "fulfillment_status": fulfillment_status,
            "customer_accepted": customer_accepted,
            "item_count": len(order.items),
            "order_total": order.total_amount,
            "item_total": item_total,
            "amount_paid": amount_paid,
            "balance_due": balance_due,
            "require_full_payment": require_full_payment,
            "reasons": reasons,
        }

    finally:
        session.close()


def create_fulfillment(
    order_id: int,
    delivery_address: Optional[str] = None,
    require_full_payment: bool = False,
) -> Fulfillment:
    """
    Create a fulfillment record after readiness checks pass.

    By default, a partial payment is allowed. Set
    require_full_payment=True if delivery must wait for
    full payment.
    """

    readiness = get_fulfillment_status(
        order_id=order_id,
        require_full_payment=require_full_payment,
    )

    if not readiness["ready"]:
        raise ValueError(
            "Order is not ready for fulfillment: "
            + "; ".join(readiness["reasons"])
        )

    session = get_session()

    try:
        order = session.scalar(
            select(Order)
            .options(selectinload(Order.fulfillment))
            .where(Order.id == order_id)
        )

        if order is None:
            raise ValueError(
                f"No order found with ID {order_id}."
            )

        if order.fulfillment is not None:
            raise ValueError(
                f"Fulfillment already exists for order "
                f"{order.order_number}."
            )

        fulfillment = Fulfillment(
            order_id=order_id,
            fulfillment_status="processing",
            delivery_address=(
                delivery_address.strip()
                if delivery_address
                else None
            ),
        )

        session.add(fulfillment)
        session.commit()
        session.refresh(fulfillment)

        return fulfillment

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def update_fulfillment_status(
    order_id: int,
    new_status: str,
    delivery_date: Optional[date] = None,
    tracking_number: Optional[str] = None,
    delivery_notes: Optional[str] = None,
) -> Fulfillment:
    """Update the delivery status of an order."""

    normalized_status = new_status.strip().lower()

    if normalized_status not in VALID_FULFILLMENT_STATUSES:
        valid_statuses = ", ".join(
            sorted(VALID_FULFILLMENT_STATUSES)
        )

        raise ValueError(
            "Invalid fulfillment status. Choose one of: "
            f"{valid_statuses}"
        )

    session = get_session()

    try:
        order = session.scalar(
            select(Order)
            .options(selectinload(Order.fulfillment))
            .where(Order.id == order_id)
        )

        if order is None:
            raise ValueError(
                f"No order found with ID {order_id}."
            )

        if order.fulfillment is None:
            raise ValueError(
                "No fulfillment record exists for this order. "
                "Create one first."
            )

        fulfillment = order.fulfillment
        fulfillment.fulfillment_status = normalized_status

        if delivery_date is not None:
            fulfillment.delivery_date = delivery_date

        if tracking_number is not None:
            fulfillment.tracking_number = (
                tracking_number.strip() or None
            )

        if delivery_notes is not None:
            fulfillment.delivery_notes = (
                delivery_notes.strip() or None
            )

        session.commit()
        session.refresh(fulfillment)

        return fulfillment

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def mark_customer_accepted(
    order_id: int,
) -> Fulfillment:
    """Mark delivery as accepted by the customer."""

    session = get_session()

    try:
        order = session.scalar(
            select(Order)
            .options(selectinload(Order.fulfillment))
            .where(Order.id == order_id)
        )

        if order is None:
            raise ValueError(
                f"No order found with ID {order_id}."
            )

        if order.fulfillment is None:
            raise ValueError(
                "No fulfillment record exists for this order."
            )

        if order.fulfillment.fulfillment_status != "delivered":
            raise ValueError(
                "Customer acceptance can only be recorded "
                "after the order is marked delivered."
            )

        order.fulfillment.customer_accepted = True

        session.commit()
        session.refresh(order.fulfillment)

        return order.fulfillment

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def list_fulfillment_statuses(
    require_full_payment: bool = False,
) -> list[dict]:
    """Return fulfillment status for every order."""

    session = get_session()

    try:
        orders = session.scalars(
            select(Order).order_by(Order.id)
        ).all()

        order_ids = [order.id for order in orders]

    finally:
        session.close()

    return [
        get_fulfillment_status(
            order_id=order_id,
            require_full_payment=require_full_payment,
        )
        for order_id in order_ids
    ]


def print_fulfillment_status(result: dict) -> None:
    """Print one fulfillment result."""

    print(
        f"[{result['order_id']}] "
        f"{result['order_number']} | "
        f"Readiness: "
        f"{result['readiness_status']} | "
        f"Fulfillment: "
        f"{result['fulfillment_status']} | "
        f"Accepted: "
        f"{'YES' if result['customer_accepted'] else 'NO'} | "
        f"Items: {result['item_count']} | "
        f"Order total: "
        f"${result['order_total']:,.2f} | "
        f"Item total: "
        f"${result['item_total']:,.2f} | "
        f"Paid: "
        f"${result['amount_paid']:,.2f} | "
        f"Balance: "
        f"${result['balance_due']:,.2f}"
    )

    for reason in result["reasons"]:
        print(f"  - {reason}")


if __name__ == "__main__":
    create_tables()

    print("\nFulfillment readiness")
    print("---------------------")

    results = list_fulfillment_statuses(
        require_full_payment=False,
    )

    if not results:
        print("No orders found.")
    else:
        for result in results:
            print_fulfillment_status(result)
