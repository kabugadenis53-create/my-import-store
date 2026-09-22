from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.account_manager import add_account
from src.database import create_tables, get_session
from src.models import Account, Order, Product
from src.payment_manager import (
    calculate_amount_paid,
    create_order,
    record_payment,
)
from src.product_manager import add_product


def unique_suffix() -> str:
    """Return a short unique value for repeatable test runs."""

    return uuid4().hex[:10].upper()


def setup_function() -> None:
    """Initialize the database before each test."""

    create_tables()


def test_database_can_load() -> None:
    """Verify that the database session can be opened."""

    session = get_session()

    try:
        assert session is not None

    finally:
        session.close()


def test_account_creation() -> None:
    """Verify that an account can be created."""

    suffix = unique_suffix()

    account = add_account(
        company_name=f"Test Company {suffix}",
        industry="Technology",
        account_owner="Test Owner",
        potential_value=Decimal("10000.00"),
        sales_stage="prospect",
    )

    assert account.id is not None
    assert account.company_name == (
        f"Test Company {suffix}"
    )


def test_product_creation() -> None:
    """Verify that a product can be created."""

    suffix = unique_suffix()
    sku = f"TEST-{suffix}"
    product_name = f"Test Product {suffix}"

    product = add_product(
        sku=sku,
        name=product_name,
        unit_price=Decimal("1500.00"),
        stock_quantity=10,
        reorder_level=2,
        category="Testing",
        description="Product used for automated tests.",
    )

    assert product.id is not None
    assert product.sku == sku
    assert product.name == product_name
    assert product.stock_quantity == 10


def test_order_and_payment_workflow() -> None:
    """Verify order creation and partial payment."""

    suffix = unique_suffix()

    account = add_account(
        company_name=f"Payment Test Company {suffix}",
        industry="Services",
        account_owner="Test Owner",
        potential_value=Decimal("25000.00"),
        sales_stage="qualified",
    )

    order = create_order(
        account_id=account.id,
        order_number=f"TEST-ORDER-{suffix}",
        product_description="Testing service",
        order_date=date.today(),
        due_date=date.today() + timedelta(days=14),
        total_amount=Decimal("25000.00"),
        grace_period_days=7,
    )

    payment = record_payment(
        order_id=order.id,
        payment_date=date.today(),
        amount=Decimal("10000.00"),
        payment_method="bank_transfer",
        reference=f"TEST-PAYMENT-{suffix}",
    )

    assert payment.id is not None

    session = get_session()

    try:
        refreshed_order = session.scalar(
            select(Order)
            .options(
                selectinload(Order.payments),
            )
            .where(Order.id == order.id)
        )

        assert refreshed_order is not None

        amount_paid = calculate_amount_paid(
            refreshed_order
        )

        assert amount_paid == Decimal("10000.00")

    finally:
        session.close()


def test_required_tables_exist() -> None:
    """Verify that important models are available."""

    session = get_session()

    try:
        account_count = session.query(Account).count()
        order_count = session.query(Order).count()
        product_count = session.query(Product).count()

        assert account_count >= 0
        assert order_count >= 0
        assert product_count >= 0

    finally:
        session.close()
