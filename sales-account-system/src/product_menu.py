from decimal import Decimal
from typing import Optional

from src.product_manager import (
    add_product,
    adjust_stock,
    list_low_stock_products,
    list_products,
    print_product,
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


def read_decimal(prompt: str) -> Decimal:
    """Read a non-negative decimal value."""

    while True:
        value = input(prompt).strip()

        try:
            amount = Decimal(value)

            if amount < Decimal("0.00"):
                print("Value cannot be negative.")
                continue

            return amount

        except Exception:
            print(
                "Please enter a valid amount, "
                "such as 75000.00."
            )


def read_optional_text(prompt: str) -> Optional[str]:
    """Read optional text."""

    value = input(prompt).strip()
    return value or None


def create_product_from_menu() -> None:
    """Create a product through the menu."""

    print("\nCreate Product")
    print("--------------")

    sku = input("SKU: ").strip()
    name = input("Product name: ").strip()
    category = read_optional_text("Category: ")
    description = read_optional_text("Description: ")

    unit_price = read_decimal("Unit price: ")

    stock_quantity = read_non_negative_integer(
        "Initial stock quantity: "
    )

    reorder_level = read_non_negative_integer(
        "Reorder level: "
    )

    product = add_product(
        sku=sku,
        name=name,
        unit_price=unit_price,
        stock_quantity=stock_quantity,
        reorder_level=reorder_level,
        category=category,
        description=description,
    )

    print(
        f"\nProduct created successfully: "
        f"[{product.id}] {product.name}"
    )


def adjust_stock_from_menu() -> None:
    """Increase or decrease product stock."""

    print("\nAdjust Stock")
    print("------------")

    product_id = read_positive_integer("Product ID: ")

    print("Use a positive quantity to add stock.")
    print("Use a negative quantity to remove stock.")

    quantity_change = int(
        input("Quantity change: ").strip()
    )

    if quantity_change == 0:
        raise ValueError(
            "Quantity change cannot be zero."
        )

    product = adjust_stock(
        product_id=product_id,
        quantity_change=quantity_change,
    )

    print(
        f"\nStock updated successfully: "
        f"{product.name} | "
        f"Current stock: {product.stock_quantity}"
    )


def show_all_products_from_menu() -> None:
    """Display all products."""

    print("\nProducts")
    print("--------")

    products = list_products(active_only=False)

    if not products:
        print("No products found.")
        return

    for product in products:
        print_product(product)


def show_low_stock_from_menu() -> None:
    """Display products at or below reorder level."""

    print("\nLow-stock Products")
    print("------------------")

    products = list_low_stock_products()

    if not products:
        print("No low-stock products.")
        return

    for product in products:
        print_product(product)


def show_product_menu() -> None:
    """Display product and inventory operations."""

    while True:
        print("\nProduct and Inventory Operations")
        print("--------------------------------")
        print("1. Create product")
        print("2. Adjust stock")
        print("3. View all products")
        print("4. View low-stock products")
        print("0. Return to main menu")

        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                create_product_from_menu()

            elif choice == "2":
                adjust_stock_from_menu()

            elif choice == "3":
                show_all_products_from_menu()

            elif choice == "4":
                show_low_stock_from_menu()

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
