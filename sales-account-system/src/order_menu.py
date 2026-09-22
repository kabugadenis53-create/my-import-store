from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from src.order_item_menu import show_order_item_menu
from src.payment_manager import (
    create_order,
    record_payment,
)


def read_integer(prompt: str) -> int:
    """Read an integer from the user."""

    while True:
        value = input(prompt).strip()

        try:
            return int(value)

        except ValueError:
            print("Please enter a valid whole number.")


def read_positive_decimal(prompt: str) -> Decimal:
    """Read a positive decimal amount."""

    while True:
        value = input(prompt).strip()

        try:
            amount = Decimal(value)

            if amount <= Decimal("0.00"):
                print("Amount must be greater than zero.")
                continue

            return amount

        except Exception:
            print(
                "Please enter a valid amount, "
                "such as 25000.00."
            )


def read_non_negative_integer(prompt: str) -> int:
    """Read a non-negative integer."""

    while True:
        value = input(prompt).strip()

        try:
            number = int(value)

            if number < 0:
                print("Value cannot be negative.")
                continue

            return number

        except ValueError:
            print("Please enter a valid whole number.")


def read_required_date(prompt: str) -> date:
    """Read a required date in YYYY-MM-DD format."""

    while True:
        value = input(prompt).strip()

        try:
            return datetime.strptime(
                value,
                "%Y-%m-%d",
            ).date()

        except ValueError:
            print(
                "Please use the format YYYY-MM-DD."
            )


def read_optional_text(prompt: str) -> Optional[str]:
    """Read optional text."""

    value = input(prompt).strip()
    return value or None


def create_order_from_menu() -> None:
    """Collect order information and create an invoice."""

    print("\nCreate Order / Invoice")
    print("---------------------")

    account_id = read_integer("Account ID: ")

    order_number = input(
        "Order or invoice number: "
    ).strip()

    product_description = input(
        "Product or service description: "
    ).strip()

    order_date = read_required_date(
        "Order date [YYYY-MM-DD]: "
    )

    due_date = read_required_date(
        "Due date [YYYY-MM-DD]: "
    )

    total_amount = read_positive_decimal(
        "Total invoice amount: "
    )

    grace_period_days = read_non_negative_integer(
        "Grace-period days [0]: "
    )

    notes = read_optional_text("Notes: ")

    order = create_order(
        account_id=account_id,
        order_number=order_number,
        product_description=product_description,
        order_date=order_date,
        due_date=due_date,
        total_amount=total_amount,
        grace_period_days=grace_period_days,
        notes=notes,
    )

    print(
        f"\nOrder created successfully: "
        f"[{order.id}] {order.order_number}"
    )


def record_payment_from_menu() -> None:
    """Collect payment information and save a payment."""

    print("\nRecord Payment")
    print("--------------")

    order_id = read_integer("Order ID: ")

    payment_date = read_required_date(
        "Payment date [YYYY-MM-DD]: "
    )

    amount = read_positive_decimal(
        "Payment amount: "
    )

    payment_method = read_optional_text(
        "Payment method: "
    )

    reference = read_optional_text(
        "Payment reference: "
    )

    notes = read_optional_text("Notes: ")

    payment = record_payment(
        order_id=order_id,
        payment_date=payment_date,
        amount=amount,
        payment_method=payment_method,
        reference=reference,
        notes=notes,
    )

    print(
        f"\nPayment recorded successfully: "
        f"[{payment.id}] "
        f"${payment.amount:,.2f}"
    )


def show_order_menu() -> None:
    """Display order, payment, and product operations."""

    while True:
        print("\nOrder Operations")
        print("----------------")
        print("1. Create order / invoice")
        print("2. Record payment")
        print("3. Add or view products on an order")
        print("0. Return to main menu")

        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                create_order_from_menu()

            elif choice == "2":
                record_payment_from_menu()

            elif choice == "3":
                show_order_item_menu()

            elif choice == "0":
                break

            else:
                print("Invalid option.")

        except ValueError as error:
            print(f"\nOperation failed: {error}")

        except Exception as error:
            print(
                "\nUnexpected error: "
                f"{type(error).__name__}: {error}"
            )
