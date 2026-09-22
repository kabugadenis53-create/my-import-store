from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import create_tables, get_session
from src.models import Order, OrderItem


def calculate_order_items_total(
    order_id: int,
) -> Decimal:
    """Return the total value of all items on an order."""

    session = get_session()

    try:
        order = session.scalar(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )

        if order is None:
            raise ValueError(
                f"No order found with ID {order_id}."
            )

        return sum(
            (
                item.line_total
                for item in order.items
            ),
            Decimal("0.00"),
        )

    finally:
        session.close()


def validate_order_total(
    order_id: int,
) -> dict:
    """
    Compare the official order total with its product-item total.
    """

    session = get_session()

    try:
        order = session.scalar(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )

        if order is None:
            raise ValueError(
                f"No order found with ID {order_id}."
            )

        item_total = sum(
            (
                item.line_total
                for item in order.items
            ),
            Decimal("0.00"),
        )

        difference = order.total_amount - item_total
        is_valid = difference == Decimal("0.00")

        return {
            "order_id": order.id,
            "order_number": order.order_number,
            "order_total": order.total_amount,
            "item_total": item_total,
            "difference": difference,
            "item_count": len(order.items),
            "is_valid": is_valid,
        }

    finally:
        session.close()


def validate_all_orders() -> list[dict]:
    """Validate every order in the database."""

    session = get_session()

    try:
        orders = session.scalars(
            select(Order).order_by(Order.id)
        ).all()

        validations = []

        for order in orders:
            item_total = sum(
                (
                    item.line_total
                    for item in order.items
                ),
                Decimal("0.00"),
            )

            difference = order.total_amount - item_total

            validations.append(
                {
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "order_total": order.total_amount,
                    "item_total": item_total,
                    "difference": difference,
                    "item_count": len(order.items),
                    "is_valid": (
                        difference == Decimal("0.00")
                    ),
                }
            )

        return validations

    finally:
        session.close()


def print_validation(result: dict) -> None:
    """Print one order validation result."""

    status = "VALID" if result["is_valid"] else "MISMATCH"

    print(
        f"[{result['order_id']}] "
        f"{result['order_number']} | "
        f"Status: {status} | "
        f"Items: {result['item_count']} | "
        f"Order total: "
        f"${result['order_total']:,.2f} | "
        f"Item total: "
        f"${result['item_total']:,.2f} | "
        f"Difference: "
        f"${result['difference']:,.2f}"
    )


if __name__ == "__main__":
    create_tables()

    print("\nOrder total validation")
    print("----------------------")

    results = validate_all_orders()

    if not results:
        print("No orders found.")
    else:
        for result in results:
            print_validation(result)
