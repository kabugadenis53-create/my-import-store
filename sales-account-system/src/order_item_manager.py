from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import create_tables, get_session
from src.models import Order, OrderItem, Product


def add_product_to_order(
    order_id: int,
    product_id: int,
    quantity: int,
) -> OrderItem:
    """
    Add a product to an order and reduce stock.

    The product's current unit price is copied into the order item.
    This preserves the historical sale price even if the catalog
    price changes later.
    """

    if quantity <= 0:
        raise ValueError(
            "quantity must be greater than zero."
        )

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

        product = session.get(Product, product_id)

        if product is None:
            raise ValueError(
                f"No product found with ID {product_id}."
            )

        if not product.is_active:
            raise ValueError(
                f"Product '{product.name}' is inactive."
            )

        if product.stock_quantity < quantity:
            raise ValueError(
                f"Insufficient stock for '{product.name}'. "
                f"Available: {product.stock_quantity}, "
                f"requested: {quantity}."
            )

        existing_item = session.scalar(
            select(OrderItem).where(
                OrderItem.order_id == order_id,
                OrderItem.product_id == product_id,
            )
        )

        if existing_item is not None:
            existing_item.quantity += quantity
            existing_item.line_total = (
                existing_item.quantity
                * existing_item.unit_price
            )

            product.stock_quantity -= quantity

            session.commit()
            session.refresh(existing_item)

            return existing_item

        unit_price = Decimal(str(product.unit_price))
        line_total = unit_price * quantity

        order_item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            line_total=line_total,
        )

        product.stock_quantity -= quantity

        session.add(order_item)
        session.commit()
        session.refresh(order_item)

        return order_item

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def list_order_items(
    order_id: int,
) -> list[OrderItem]:
    """Return all product items belonging to an order."""

    session = get_session()

    try:
        order = session.get(Order, order_id)

        if order is None:
            raise ValueError(
                f"No order found with ID {order_id}."
            )

        items = session.scalars(
            select(OrderItem)
            .options(selectinload(OrderItem.product))
            .where(OrderItem.order_id == order_id)
            .order_by(OrderItem.id)
        ).all()

        return list(items)

    finally:
        session.close()


def calculate_order_items_total(
    order_id: int,
) -> Decimal:
    """Calculate the total of all product lines on an order."""

    items = list_order_items(order_id)

    return sum(
        (
            item.line_total
            for item in items
        ),
        Decimal("0.00"),
    )


def print_order_items(
    order_id: int,
) -> None:
    """Print all product lines for an order."""

    items = list_order_items(order_id)

    if not items:
        print("No products have been added to this order.")
        return

    total = Decimal("0.00")

    for item in items:
        product_name = (
            item.product.name
            if item.product is not None
            else "Unknown product"
        )

        print(
            f"[{item.id}] "
            f"{product_name} | "
            f"Quantity: {item.quantity} | "
            f"Unit price: ${item.unit_price:,.2f} | "
            f"Line total: ${item.line_total:,.2f}"
        )

        total += item.line_total

    print("-" * 60)
    print(f"Product total: ${total:,.2f}")


if __name__ == "__main__":
    create_tables()

    print("\nOrders with product items")
    print("-------------------------")

    session = get_session()

    try:
        orders = session.scalars(
            select(Order).order_by(Order.id)
        ).all()
    finally:
        session.close()

    if not orders:
        print("No orders found.")
    else:
        for order in orders:
            print(
                f"\nOrder {order.id}: "
                f"{order.order_number}"
            )
            print_order_items(order.id)
