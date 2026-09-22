from src.dashboard import (
    get_dashboard_data,
    print_dashboard,
)
from src.export_reports import (
    export_account_priorities,
    export_activities,
    export_payment_balances,
)


def show_dashboard_from_menu() -> None:
    """Display the sales dashboard."""

    dashboard_data = get_dashboard_data(
        days_ahead=7,
    )

    print_dashboard(dashboard_data)


def export_reports_from_menu() -> None:
    """Export all available CSV reports."""

    print("\nExporting reports...")
    print("--------------------")

    account_file = export_account_priorities()
    payment_file = export_payment_balances()
    activity_file = export_activities()

    print(f"Account priorities: {account_file}")
    print(f"Payment balances:   {payment_file}")
    print(f"Sales activities:   {activity_file}")


def show_report_menu() -> None:
    """Display reporting operations."""

    while True:
        print("\nReporting Operations")
        print("--------------------")
        print("1. View sales dashboard")
        print("2. Export reports to CSV")
        print("0. Return to main menu")

        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                show_dashboard_from_menu()

            elif choice == "2":
                export_reports_from_menu()

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
