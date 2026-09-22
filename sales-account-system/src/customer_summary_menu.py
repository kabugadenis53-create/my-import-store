from src.customer_summary import (
    get_customer_summary,
    list_account_ids,
    print_customer_summary,
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


def show_all_customer_summaries() -> None:
    """Display summaries for every account."""

    account_ids = list_account_ids()

    if not account_ids:
        print("\nNo accounts found.")
        return

    for account_id in account_ids:
        summary = get_customer_summary(account_id)
        print_customer_summary(summary)


def show_one_customer_summary() -> None:
    """Display one account summary."""

    account_id = read_positive_integer(
        "Account ID: "
    )

    summary = get_customer_summary(account_id)
    print_customer_summary(summary)


def show_customer_summary_menu() -> None:
    """Display customer-summary options."""

    while True:
        print("\nCustomer Summary")
        print("----------------")
        print("1. View all customer summaries")
        print("2. View one customer summary")
        print("0. Return to main menu")

        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                show_all_customer_summaries()

            elif choice == "2":
                show_one_customer_summary()

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
