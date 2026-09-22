from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from src.database import create_tables, get_session
from src.models import Account, Contact


def add_contact(
    account_id: int,
    first_name: str,
    last_name: str,
    job_title: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    is_primary: bool = False,
    notes: Optional[str] = None,
) -> Contact:
    """Create and save a contact for an account."""

    first_name = first_name.strip()
    last_name = last_name.strip()

    if not first_name:
        raise ValueError("first_name cannot be empty.")

    if not last_name:
        raise ValueError("last_name cannot be empty.")

    if email is not None:
        email = email.strip().lower()

        if email and "@" not in email:
            raise ValueError("email must contain '@'.")

    session = get_session()

    try:
        account = session.get(Account, account_id)

        if account is None:
            raise ValueError(
                f"No account found with ID {account_id}."
            )

        if email:
            existing_contact = session.scalar(
                select(Contact).where(
                    Contact.email == email
                )
            )

            if existing_contact is not None:
                raise ValueError(
                    f"A contact with this email already exists: {email}"
                )

        if is_primary:
            existing_primary = session.scalars(
                select(Contact).where(
                    Contact.account_id == account_id,
                    Contact.is_primary.is_(True),
                )
            ).all()

            for contact in existing_primary:
                contact.is_primary = False

        contact = Contact(
            account_id=account_id,
            first_name=first_name,
            last_name=last_name,
            job_title=job_title,
            email=email or None,
            phone=phone,
            is_primary=is_primary,
            notes=notes,
        )

        session.add(contact)
        session.commit()
        session.refresh(contact)

        return contact

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def list_account_contacts(
    account_id: int,
) -> list[Contact]:
    """Return all contacts for one account."""

    session = get_session()

    try:
        account = session.get(Account, account_id)

        if account is None:
            raise ValueError(
                f"No account found with ID {account_id}."
            )

        contacts = session.scalars(
            select(Contact)
            .where(Contact.account_id == account_id)
            .order_by(
                Contact.is_primary.desc(),
                Contact.last_name,
                Contact.first_name,
            )
        ).all()

        return list(contacts)

    finally:
        session.close()


def search_contacts(
    search_term: str,
) -> list[Contact]:
    """Search contacts by name, email, job title, or phone."""

    search_term = search_term.strip()

    if not search_term:
        raise ValueError("search_term cannot be empty.")

    pattern = f"%{search_term}%"

    session = get_session()

    try:
        contacts = session.scalars(
            select(Contact)
            .options(selectinload(Contact.account))
            .where(
                or_(
                    Contact.first_name.ilike(pattern),
                    Contact.last_name.ilike(pattern),
                    Contact.email.ilike(pattern),
                    Contact.job_title.ilike(pattern),
                    Contact.phone.ilike(pattern),
                )
            )
            .order_by(
                Contact.last_name,
                Contact.first_name,
            )
        ).all()

        return list(contacts)

    finally:
        session.close()


def set_primary_contact(
    contact_id: int,
) -> Contact:
    """Make one contact primary for its account."""

    session = get_session()

    try:
        contact = session.get(Contact, contact_id)

        if contact is None:
            raise ValueError(
                f"No contact found with ID {contact_id}."
            )

        other_contacts = session.scalars(
            select(Contact).where(
                Contact.account_id == contact.account_id,
                Contact.id != contact.id,
            )
        ).all()

        for other_contact in other_contacts:
            other_contact.is_primary = False

        contact.is_primary = True

        session.commit()
        session.refresh(contact)

        return contact

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def update_contact(
    contact_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    job_title: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    notes: Optional[str] = None,
) -> Contact:
    """Update editable contact fields."""

    session = get_session()

    try:
        contact = session.get(Contact, contact_id)

        if contact is None:
            raise ValueError(
                f"No contact found with ID {contact_id}."
            )

        if first_name is not None:
            first_name = first_name.strip()

            if not first_name:
                raise ValueError(
                    "first_name cannot be empty."
                )

            contact.first_name = first_name

        if last_name is not None:
            last_name = last_name.strip()

            if not last_name:
                raise ValueError(
                    "last_name cannot be empty."
                )

            contact.last_name = last_name

        if job_title is not None:
            contact.job_title = job_title.strip() or None

        if email is not None:
            normalized_email = email.strip().lower()

            if normalized_email and "@" not in normalized_email:
                raise ValueError(
                    "email must contain '@'."
                )

            duplicate = session.scalar(
                select(Contact).where(
                    Contact.email == normalized_email,
                    Contact.id != contact_id,
                )
            )

            if duplicate is not None:
                raise ValueError(
                    "Another contact already uses this email."
                )

            contact.email = normalized_email or None

        if phone is not None:
            contact.phone = phone.strip() or None

        if notes is not None:
            contact.notes = notes.strip() or None

        session.commit()
        session.refresh(contact)

        return contact

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def print_contact(contact: Contact) -> None:
    """Print a contact in a readable format."""

    account_name = "Unknown account"

    if contact.account is not None:
        account_name = contact.account.company_name

    primary_label = "PRIMARY" if contact.is_primary else "SECONDARY"

    print(
        f"[{contact.id}] "
        f"{contact.full_name} | "
        f"{contact.job_title or 'No title'} | "
        f"{contact.email or 'No email'} | "
        f"Account: {account_name} | "
        f"{primary_label}"
    )


if __name__ == "__main__":
    create_tables()

    print("\nAll contacts")
    print("------------")

    session = get_session()

    try:
        contacts = session.scalars(
            select(Contact)
            .options(selectinload(Contact.account))
            .order_by(
                Contact.last_name,
                Contact.first_name,
            )
        ).all()

        if not contacts:
            print("No contacts found.")
        else:
            for contact in contacts:
                print_contact(contact)

    finally:
        session.close()

    print("\nContact search: 'manager'")
    print("--------------------------")

    for contact in search_contacts("manager"):
        print_contact(contact)
