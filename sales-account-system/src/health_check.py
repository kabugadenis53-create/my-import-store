from importlib import import_module

from src.database import create_tables


REQUIRED_MODULES = [
    "src.models",
    "src.database",
    "src.account_manager",
    "src.contact_manager",
    "src.activity_manager",
    "src.payment_manager",
    "src.product_manager",
    "src.order_item_manager",
    "src.fulfillment_manager",
    "src.customer_summary",
    "src.customer_alerts",
    "src.activity_menu",
    "src.order_item_menu",
    "src.fulfillment_menu",
    "src.order_menu",
    "src.product_menu",
    "src.customer_summary_menu",
    "src.report_menu",
    "src.cli",
]


def check_database() -> bool:
    """Verify that database tables can initialize."""

    try:
        create_tables()
        print("[PASS] Database initialized successfully.")
        return True

    except Exception as error:
        print(
            "[FAIL] Database initialization failed: "
            f"{type(error).__name__}: {error}"
        )
        return False


def check_modules() -> bool:
    """Verify that all required modules can be imported."""

    all_loaded = True

    for module_name in REQUIRED_MODULES:
        try:
            import_module(module_name)
            print(f"[PASS] Module loaded: {module_name}")

        except Exception as error:
            all_loaded = False
            print(
                f"[FAIL] Module failed: {module_name} | "
                f"{type(error).__name__}: {error}"
            )

    return all_loaded


def run_health_check() -> None:
    """Run all system checks."""

    print("\nSales Account System Health Check")
    print("---------------------------------")

    database_ok = check_database()

    print("\nModule checks")
    print("-------------")

    modules_ok = check_modules()

    print("\nHealth-check result")
    print("-------------------")

    if database_ok and modules_ok:
        print("SYSTEM STATUS: HEALTHY")
    else:
        print("SYSTEM STATUS: ERRORS FOUND")


if __name__ == "__main__":
    run_health_check()
