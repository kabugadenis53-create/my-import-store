from datetime import date, datetime
from typing import Optional

from src.fulfillment_manager import (
    create_fulfillment,
    get_fulfillment_status,
    mark_customer_accepted,
    update_fulfillment_status,
)


def read_positive_integer(prompt: str) -> int:
    """Read a positive integer."""

    while True:
        value = input(prompt).strip()

        try:
            number = int(value)

            if number <= 0:
                print("Value must be greater than zero.")
                continue

            return number

        except ValueError:
            print("Please enter a valid whole number.")


def read_date(
    prompt: str,
    allow_empty: bool = True,
) -> Optional[date]:
    """Read a date in YYYY-MM-DD format."""

    while True:
        value = input(prompt).strip()

        if allow_empty and not value:
            return None

        try:
            return datetime.strptime(
                value,
                "%Y-%m-%d",
            ).date()

        except ValueError:
            print("Please use the format YYYY-MM-DD.")


def read_optional_text(prompt: str) -> Optional[str]:
    """Read optional text."""

    value = input(prompt).strip()
    return value or None


def show_fulfillment_status_from_menu() -> None:
    """Display fulfillment readiness for an order."""

    print("\nFulfillment Status")
    print("------------------")

    order_id = read_positive_integer("Order ID: ")

    result = get_fulfillment_status(
        order_id=order_id,
        require_full_payment=False,
    )

    print(
        f"\nOrder: {result['order_number']}"
    )
    print(
        f"Readiness: "
        f"{result['readiness_status']}"
    )
    print(
        f"Fulfillment status: "
        f"{result['fulfillment_status']}"
    )
    print(
        f"Customer accepted: "
        f"{'YES' if result['customer_accepted'] else 'NO'}"
    )
    print(
        f"Order total: "
        f"${result['order_total']:,.2f}"
    )
    print(
        f"Product-item total: "
        f"${result['item_total']:,.2f}"
    )
    print(
        f"Paid: "
        f"${result['amount_paid']:,.2f}"
    )
    print(
        f"Balance: "
        f"${result['balance_due']:,.2f}"
    )

    print("\nDetails:")

    for reason in result["reasons"]:
        print(f"- {reason}")


def create_fulfillment_from_menu() -> None:
    """Create a fulfillment record for a ready order."""

    print("\nCreate Fulfillment")
    print("------------------")

    order_id = read_positive_integer("Order ID: ")
    delivery_address = read_optional_text(
        "Delivery address: "
    )

    fulfillment = create_fulfillment(
        order_id=order_id,
        delivery_address=delivery_address,
    )

    print(
        f"\nFulfillment created successfully: "
        f"[{fulfillment.id}] "
        f"Order ID: {fulfillment.order_id} | "
        f"Status: {fulfillment.fulfillment_status}"
    )


def update_status_from_menu() -> None:
    """Update fulfillment delivery status."""

    print("\nUpdate Fulfillment Status")
    print("-------------------------")

    order_id = read_positive_integer("Order ID: ")

    print("\nAvailable statuses:")
    print("not_started")
    print("processing")
    print("ready")
    print("shipped")
    print("delivered")
    print("cancelled")

    new_status = input(
        "New status: "
    ).strip()

    delivery_date = None

    if new_status.lower() == "delivered":
        delivery_date = read_date(
            "Delivery date [YYYY-MM-DD, optional]: "
        )

    tracking_number = read_optional_text(
        "Tracking number [optional]: "
    )

    delivery_notes = read_optional_text(
        "Delivery notes [optional]: "
    )

    fulfillment = update_fulfillment_status(
        order_id=order_id,
        new_status=new_status,
        delivery_date=delivery_date,
        tracking_number=tracking_number,
        delivery_notes=delivery_notes,
    )

    print(
        f"\nFulfillment updated successfully: "
        f"Order ID {fulfillment.order_id} | "
        f"Status: {fulfillment.fulfillment_status}"
    )


def accept_delivery_from_menu() -> None:
    """Record customer acceptance of a delivered order."""

    print("\nRecord Customer Acceptance")
    print("--------------------------")

    order_id = read_positive_integer("Order ID: ")

    fulfillment = mark_customer_accepted(
        order_id=order_id,
    )

    print(
        f"\nCustomer acceptance recorded: "
        f"Order ID {fulfillment.order_id}"
    )


def show_fulfillment_menu() -> None:
    """Display fulfillment operations."""

    while True:
        print("\nFulfillment Operations")
        print("----------------------")
        print("1. Check fulfillment status")
        print("2. Create fulfillment record")
        print("3. Update fulfillment status")
        print("4. Record customer acceptance")
        print("0. Return to order menu")

        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                show_fulfillment_status_from_menu()

            elif choice == "2":
                create_fulfillment_from_menu()

            elif choice == "3":
                update_status_from_menu()

            elif choice == "4":
                accept_delivery_from_menu()

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
