from src.order_item_manager import (
    add_product_to_order,
    print_order_items,
)


def read_integer(prompt: str) -> int:
    """Read a whole number from the user."""

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


def add_product_to_order_from_menu() -> None:
    """Add an inventory product to an existing order."""

    print("\nAdd Product to Order")
    print("--------------------")

    order_id = read_integer("Order ID: ")
    product_id = read_integer("Product ID: ")
    quantity = read_integer("Quantity: ")

    order_item = add_product_to_order(
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
    )

    print(
        "\nProduct added successfully."
    )
    print(
        f"Order item ID: {order_item.id}"
    )
    print(
        f"Quantity: {order_item.quantity}"
    )
    print(
        f"Line total: "
        f"${order_item.line_total:,.2f}"
    )


def view_order_items_from_menu() -> None:
    """Display products assigned to an order."""

    print("\nView Order Products")
    print("-------------------")

    order_id = read_integer("Order ID: ")
    print_order_items(order_id)


def show_order_item_menu() -> None:
    """Display product-order operations."""

    while True:
        print("\nProduct Order Operations")
        print("------------------------")
        print("1. Add product to order")
        print("2. View products on order")
        print("0. Return to order menu")

        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                add_product_to_order_from_menu()

            elif choice == "2":
                view_order_items_from_menu()

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
