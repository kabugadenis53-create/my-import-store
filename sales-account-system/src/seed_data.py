from datetime import date
from decimal import Decimal

from sqlalchemy import select

from src.database import create_tables, get_session
from src.models import Account, Contact


def seed_sample_data() -> None:
    """Insert sample accounts and contacts if they do not already exist."""

    create_tables()

    session = get_session()

    try:
        sample_accounts = [
            {
                "company_name": "Acme Manufacturing",
                "industry": "Manufacturing",
                "account_owner": "Administrator",
                "potential_value": Decimal("75000.00"),
                "sales_stage": "prospect",
                "phone": "+1-555-0100",
                "website": "https://example.com/acme",
                "address": "100 Industrial Avenue",
                "notes": "Growing manufacturer evaluating workflow automation.",
                "next_follow_up_date": date(2026, 9, 15 ),
                "contacts": [
                    {
                        "first_name": "Sarah",
                        "last_name": "Johnson",
                        "job_title": "Operations Director",
                        "email": "sarah.johnson@example.com",
                        "phone": "+1-555-0101",
                        "is_primary": True,
                        "notes": "Interested in reducing manual reporting.",
                    },
                    {
                        "first_name": "Michael",
                        "last_name": "Brown",
                        "job_title": "Finance Manager",
                        "email": "michael.brown@example.com",
                        "phone": "+1-555-0102",
                        "is_primary": False,
                        "notes": "May participate in commercial evaluation.",
                    },
                ],
            },
            {
                "company_name": "Northstar Health",
                "industry": "Healthcare",
                "account_owner": "Administrator",
                "potential_value": Decimal("120000.00"),
                "sales_stage": "qualified",
                "phone": "+1-555-0200",
                "website": "https://example.com/northstar",
                "address": "200 Market Street",
                "notes": "Qualified opportunity with several departments involved.",
                "next_follow_up_date": date(2026, 9, 18 ),
                "contacts": [
                    {
                        "first_name": "David",
                        "last_name": "Williams",
                        "job_title": "Chief Operating Officer",
                        "email": "david.williams@example.com",
                        "phone": "+1-555-0201",
                        "is_primary": True,
                        "notes": "Executive sponsor for the evaluation.",
                    },
                ],
            },
            {
                "company_name": "BrightPath Logistics",
                "industry": "Logistics",
                "account_owner": "Administrator",
                "potential_value": Decimal("45000.00"),
                "sales_stage": "lead",
                "phone": "+1-555-0300",
                "website": "https://example.com/brightpath",
                "address": "300 Distribution Road",
                "notes": "Early-stage lead from an industry referral.",
                "next_follow_up_date": date(2026, 9, 22 ),
                "contacts": [
                    {
                        "first_name": "Emily",
                        "last_name": "Davis",
                        "job_title": "Business Development Manager",
                        "email": "emily.davis@example.com",
                        "phone": "+1-555-0301",
                        "is_primary": True,
                        "notes": "Requested an introductory product discussion.",
                    },
                ],
            },
        ]

        accounts_created = 0
        contacts_created = 0

        for account_data in sample_accounts:
            contacts_data = account_data.pop("contacts")

            existing_account = session.scalar(
                select(Account).where(
                    Account.company_name
                    == account_data["company_name"]
                )
            )

            if existing_account is not None:
                print(
                    f"Skipped existing account: "
                    f"{existing_account.company_name}"
                )
                continue

            account = Account(**account_data)

            for contact_data in contacts_data:
                account.contacts.append(Contact(**contact_data))
                contacts_created += 1

            session.add(account)
            accounts_created += 1

        session.commit()

        print(f"\nAccounts created: {accounts_created}")
        print(f"Contacts created: {contacts_created}")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    seed_sample_data()
