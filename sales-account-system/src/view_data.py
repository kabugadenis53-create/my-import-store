from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.database import get_session
from src.models import Account


def display_accounts() -> None:
    """Display all accounts and their contacts."""

    session = get_session()

    try:
        accounts = session.scalars(
            select(Account)
            .options(joinedload(Account.contacts))
            .order_by(Account.company_name)
        ).unique().all()

        if not accounts:
            print("No accounts found.")
            return

        for account in accounts:
            print("\n" + "=" * 60)
            print(f"Company: {account.company_name}")
            print(f"Industry: {account.industry}")
            print(f"Owner: {account.account_owner}")
            print(f"Potential value: ${account.potential_value:,.2f}")
            print(f"Sales stage: {account.sales_stage}")
            print(f"Next follow-up: {account.next_follow_up_date}")

            print("\nContacts:")

            for contact in account.contacts:
                primary_label = "Primary" if contact.is_primary else "Secondary"

                print(
                    f"  - {contact.full_name} "
                    f"({contact.job_title or 'No title'})"
                )
                print(f"    Email: {contact.email or 'Not provided'}")
                print(f"    Phone: {contact.phone or 'Not provided'}")
                print(f"    Type: {primary_label}")

    finally:
        session.close()


if __name__ == "__main__":
    display_accounts()
