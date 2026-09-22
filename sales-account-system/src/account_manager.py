from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import or_, select

from src.database import create_tables, get_session
from src.models import Account


def add_account(
    company_name: str,
    industry: Optional[str] = None,
    account_owner: Optional[str] = None,
    potential_value: Optional[Decimal] = None,
    sales_stage: str = "prospect",
    phone: Optional[str] = None,
    website: Optional[str] = None,
    address: Optional[str] = None,
    notes: Optional[str] = None,
    next_follow_up_date: Optional[date] = None,
) -> Account:
    """Create and save a new sales account."""

    if not company_name.strip():
        raise ValueError("company_name cannot be empty.")

    if potential_value is not None and potential_value < 0:
        raise ValueError("potential_value cannot be negative.")

    session = get_session()

    try:
        existing_account = session.scalar(
            select(Account).where(
                Account.company_name == company_name.strip()
            )
        )

        if existing_account is not None:
            raise ValueError(
                f"Account already exists: {company_name}"
            )

        account = Account(
            company_name=company_name.strip(),
            industry=industry,
            account_owner=account_owner,
            potential_value=potential_value,
            sales_stage=sales_stage,
            phone=phone,
            website=website,
            address=address,
            notes=notes,
            next_follow_up_date=next_follow_up_date,
        )

        session.add(account)
        session.commit()
        session.refresh(account)

        return account

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def list_accounts() -> list[Account]:
    """Return all accounts ordered by company name."""

    session = get_session()

    try:
        return list(
            session.scalars(
                select(Account).order_by(Account.company_name)
            ).all()
        )

    finally:
        session.close()


def search_accounts(search_term: str) -> list[Account]:
    """Search accounts by company name, industry, or sales stage."""

    if not search_term.strip():
        raise ValueError("search_term cannot be empty.")

    pattern = f"%{search_term.strip()}%"

    session = get_session()

    try:
        statement = select(Account).where(
            or_(
                Account.company_name.ilike(pattern),
                Account.industry.ilike(pattern),
                Account.sales_stage.ilike(pattern),
            )
        ).order_by(Account.company_name)

        return list(session.scalars(statement).all())

    finally:
        session.close()


def update_account_stage(
    account_id: int,
    new_stage: str,
) -> Account:
    """Update the sales stage of an account."""

    if not new_stage.strip():
        raise ValueError("new_stage cannot be empty.")

    session = get_session()

    try:
        account = session.get(Account, account_id)

        if account is None:
            raise ValueError(
                f"No account found with ID {account_id}."
            )

        account.sales_stage = new_stage.strip()
        session.commit()
        session.refresh(account)

        return account

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def update_follow_up_date(
    account_id: int,
    follow_up_date: Optional[date],
) -> Account:
    """Set or clear an account's next follow-up date."""

    session = get_session()

    try:
        account = session.get(Account, account_id)

        if account is None:
            raise ValueError(
                f"No account found with ID {account_id}."
            )

        account.next_follow_up_date = follow_up_date
        session.commit()
        session.refresh(account)

        return account

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def accounts_due_for_follow_up(
    as_of_date: Optional[date] = None,
) -> list[Account]:
    """Return accounts due for follow-up on or before a given date."""

    if as_of_date is None:
        as_of_date = date.today()

    session = get_session()

    try:
        statement = select(Account).where(
            Account.next_follow_up_date <= as_of_date
        ).order_by(Account.next_follow_up_date)

        return list(session.scalars(statement).all())

    finally:
        session.close()


def print_account(account: Account) -> None:
    """Print one account in a readable format."""

    potential_value = (
        f"${account.potential_value:,.2f}"
        if account.potential_value is not None
        else "Not set"
    )

    print(
        f"[{account.id}] "
        f"{account.company_name} | "
        f"{account.industry or 'Industry not set'} | "
        f"Stage: {account.sales_stage} | "
        f"Potential: {potential_value} | "
        f"Follow-up: {account.next_follow_up_date or 'Not set'}"
    )


if __name__ == "__main__":
    create_tables()

    print("\nAll accounts")
    print("------------")

    accounts = list_accounts()

    for account in accounts:
        print_account(account)

    print("\nHealthcare accounts")
    print("-------------------")

    for account in search_accounts("Healthcare"):
        print_account(account)

    print("\nAccounts due for follow-up")
    print("--------------------------")

    for account in accounts_due_for_follow_up():
        print_account(account)
