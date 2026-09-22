from decimal import Decimal
from typing import Optional

from sqlalchemy import or_, select

from src.database import create_tables, get_session
from src.models import Product


def add_product(
    sku: str,
    name: str,
    unit_price: Decimal,
    stock_quantity: int = 0,
    reorder_level: int = 0,
    category: Optional[str] = None,
    description: Optional[str] = None,
) -> Product:
    """Create and save a product."""

    sku = sku.strip()
    name = name.strip()

    if not sku:
        raise ValueError("sku cannot be empty.")

    if not name:
        raise ValueError("name cannot be empty.")

    if unit_price < Decimal("0.00"):
        raise ValueError("unit_price cannot be negative.")

    if stock_quantity < 0:
        raise ValueError(
            "stock_quantity cannot be negative."
        )

    if reorder_level < 0:
        raise ValueError(
            "reorder_level cannot be negative."
        )

    session = get_session()

    try:
        existing_product = session.scalar(
            select(Product).where(Product.sku == sku)
        )

        if existing_product is not None:
            raise ValueError(
                f"A product with SKU '{sku}' already exists."
            )

        product = Product(
            sku=sku,
            name=name,
            unit_price=unit_price,
            stock_quantity=stock_quantity,
            reorder_level=reorder_level,
            category=category,
            description=description,
        )

        session.add(product)
        session.commit()
        session.refresh(product)

        return product

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def list_products(
    active_only: bool = True,
) -> list[Product]:
    """Return products ordered by name."""

    session = get_session()

    try:
        statement = select(Product)

        if active_only:
            statement = statement.where(
                Product.is_active.is_(True)
            )

        statement = statement.order_by(Product.name)

        return list(session.scalars(statement).all())

    finally:
        session.close()


def search_products(
    search_term: str,
) -> list[Product]:
    """Search products by SKU, name, or category."""

    search_term = search_term.strip()

    if not search_term:
        raise ValueError(
            "search_term cannot be empty."
        )

    pattern = f"%{search_term}%"

    session = get_session()

    try:
        statement = select(Product).where(
            Product.is_active.is_(True),
            or_(
                Product.sku.ilike(pattern),
                Product.name.ilike(pattern),
                Product.category.ilike(pattern),
            ),
        ).order_by(Product.name)

        return list(session.scalars(statement).all())

    finally:
        session.close()


def adjust_stock(
    product_id: int,
    quantity_change: int,
) -> Product:
    """
    Increase or decrease stock.

    Positive quantity_change adds stock.
    Negative quantity_change removes stock.
    """

    if quantity_change == 0:
        raise ValueError(
            "quantity_change cannot be zero."
        )

    session = get_session()

    try:
        product = session.get(Product, product_id)

        if product is None:
            raise ValueError(
                f"No product found with ID {product_id}."
            )

        new_quantity = (
            product.stock_quantity + quantity_change
        )

        if new_quantity < 0:
            raise ValueError(
                "Stock cannot become negative. "
                f"Current stock: {product.stock_quantity}"
            )

        product.stock_quantity = new_quantity

        session.commit()
        session.refresh(product)

        return product

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def set_product_active(
    product_id: int,
    is_active: bool,
) -> Product:
    """Activate or deactivate a product."""

    session = get_session()

    try:
        product = session.get(Product, product_id)

        if product is None:
            raise ValueError(
                f"No product found with ID {product_id}."
            )

        product.is_active = is_active

        session.commit()
        session.refresh(product)

        return product

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def list_low_stock_products() -> list[Product]:
    """Return active products at or below their reorder level."""

    session = get_session()

    try:
        products = session.scalars(
            select(Product)
            .where(
                Product.is_active.is_(True),
                Product.stock_quantity
                <= Product.reorder_level,
            )
            .order_by(Product.stock_quantity, Product.name)
        ).all()

        return list(products)

    finally:
        session.close()


def print_product(product: Product) -> None:
    """Print one product."""

    status = "LOW STOCK" if product.is_low_stock else "OK"
    active_status = "ACTIVE" if product.is_active else "INACTIVE"

    print(
        f"[{product.id}] "
        f"{product.sku} | "
        f"{product.name} | "
        f"Price: ${product.unit_price:,.2f} | "
        f"Stock: {product.stock_quantity} | "
        f"Reorder level: {product.reorder_level} | "
        f"{status} | "
        f"{active_status}"
    )


if __name__ == "__main__":
    create_tables()

    print("\nProducts")
    print("--------")

    products = list_products(active_only=False)

    if not products:
        print("No products found.")
    else:
        for product in products:
            print_product(product)

    print("\nLow-stock products")
    print("------------------")

    low_stock_products = list_low_stock_products()

    if not low_stock_products:
        print("No low-stock products.")
    else:
        for product in low_stock_products:
            print_product(product)
