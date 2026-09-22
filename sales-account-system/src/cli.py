from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from src.account_manager import (
    accounts_due_for_follow_up,
    add_account,
    list_accounts,
    print_account,
)
from src.activity_menu import show_activity_menu
from src.contact_manager import add_contact
from src.customer_alerts import (
    get_customer_alerts,
    print_alert,
)
from src.customer_summary_menu import (
    show_customer_summary_menu,
)
from src.database import create_tables
from src.order_menu import show_order_menu
from src.payment_manager import (
    list_orders,
    print_order_summary,
)
from src.product_menu import show_product_menu
from src.report_menu import show_report_menu


def read_integer(
    prompt: str,
    allow_empty: bool = False,
) -> Optional[int]:
    """Read an integer from the user."""

    while True:
        value = input(prompt).strip()

        if allow_empty and not value:
            return None

        try:
            return int(value)

        except ValueError:
            print("Please enter a valid whole number.")


def read_decimal(prompt: str) -> Decimal:
    """Read a non-negative decimal amount."""

    while True:
        value = input(prompt).strip()

        try:
            amount = Decimal(value)

            if amount < Decimal("0.00"):
                print("Amount cannot be negative.")
                continue

            return amount

        except Exception:
            print(
                "Please enter a valid amount, "
                "such as 25000.00."
            )


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
            print(
                "Please use the format YYYY-MM-DD."
            )


def show_accounts() -> None:
    """Display all accounts."""

    print("\nAccounts")
    print("--------")

    accounts = list_accounts()

    if not accounts:
        print("No accounts found.")
        return

    for account in accounts:
        print_account(account)


def add_account_from_menu() -> None:
    """Collect account information and save it."""

    print("\nAdd Account")
    print("-----------")

    company_name = input("Company name: ").strip()
    industry = input("Industry: ").strip() or None
    owner = input("Account owner: ").strip() or None

    potential_value = read_decimal(
        "Potential value: "
    )

    sales_stage = (
        input("Sales stage [prospect]: ").strip()
        or "prospect"
    )

    phone = input("Phone: ").strip() or None
    website = input("Website: ").strip() or None
    notes = input("Notes: ").strip() or None

    follow_up_date = read_date(
        "Next follow-up date "
        "[YYYY-MM-DD, optional]: "
    )

    account = add_account(
        company_name=company_name,
        industry=industry,
        account_owner=owner,
        potential_value=potential_value,
        sales_stage=sales_stage,
        phone=phone,
        website=website,
        notes=notes,
        next_follow_up_date=follow_up_date,
    )

    print(
        f"\nAccount created successfully: "
        f"[{account.id}] {account.company_name}"
    )


def add_contact_from_menu() -> None:
    """Collect contact information and save it."""

    print("\nAdd Contact")
    print("-----------")

    account_id = read_integer("Account ID: ")

    first_name = input("First name: ").strip()
    last_name = input("Last name: ").strip()
    job_title = input("Job title: ").strip() or None
    email = input("Email: ").strip() or None
    phone = input("Phone: ").strip() or None

    primary_answer = (
        input("Make primary contact? [y/N]: ")
        .strip()
        .lower()
    )

    is_primary = primary_answer in {"y", "yes"}

    notes = input("Notes: ").strip() or None

    contact = add_contact(
        account_id=account_id,
        first_name=first_name,
        last_name=last_name,
        job_title=job_title,
        email=email,
        phone=phone,
        is_primary=is_primary,
        notes=notes,
    )

    print(
        f"\nContact created successfully: "
        f"[{contact.id}] {contact.full_name}"
    )


def show_orders() -> None:
    """Display all orders and payment summaries."""

    print("\nOrders")
    print("------")

    orders = list_orders()

    if not orders:
        print("No orders found.")
        return

    for order in orders:
        print_order_summary(order)


def show_follow_ups() -> None:
    """Display accounts due for follow-up."""

    print("\nAccounts due for follow-up")
    print("--------------------------")

    accounts = accounts_due_for_follow_up()

    if not accounts:
        print("No accounts currently require follow-up.")
        return

    for account in accounts:
        print_account(account)


def show_alerts() -> None:
    """Display current customer alerts."""

    print("\nCustomer alerts")
    print("---------------")

    alerts = get_customer_alerts(days_ahead=7)

    if not alerts:
        print("No customer alerts.")
        return

    for alert in alerts:
        print_alert(alert)


def display_menu() -> None:
    """Display the main menu."""

    print("\n" + "=" * 60)
    print("SALES ACCOUNT DEVELOPMENT SYSTEM")
    print("=" * 60)
    print("1. View accounts")
    print("2. Add account")
    print("3. Add contact")
    print("4. Order and payment operations")
    print("5. Product and inventory operations")
    print("6. Sales activity operations")
    print("7. View accounts due for follow-up")
    print("8. View customer alerts")
    print("9. View customer summaries")
    print("10. Reporting and exports")
    print("0. Exit")
    print("=" * 60)


def run_cli() -> None:
    """Run the interactive command-line application."""

    create_tables()

    while True:
        display_menu()
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                show_accounts()

            elif choice == "2":
                add_account_from_menu()

            elif choice == "3":
                add_contact_from_menu()

            elif choice == "4":
                show_orders()
                show_order_menu()

            elif choice == "5":
                show_product_menu()

            elif choice == "6":
                show_activity_menu()

            elif choice == "7":
                show_follow_ups()

            elif choice == "8":
                show_alerts()

            elif choice == "9":
                show_customer_summary_menu()

            elif choice == "10":
                show_report_menu()

            elif choice == "0":
                print("Goodbye.")
                break

            else:
                print(
                    "Invalid option. "
                    "Please choose from the menu."
                )

        except ValueError as error:
            print(f"\nOperation failed: {error}")

        except Exception as error:
            print(
                "\nUnexpected error: "
                f"{type(error).__name__}: {error}"
            )


if __name__ == "__main__":
    run_cli()
