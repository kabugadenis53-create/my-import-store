from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.database import create_tables, get_session
from src.models import Account, Activity


STAGE_POINTS = {
    "lead": 10,
    "prospect": 20,
    "qualified": 35,
    "proposal": 50,
    "negotiation": 65,
    "closed_won": 80,
    "customer": 75,
    "closed_lost": 0,
}


def calculate_account_score(
    account: Account,
    activity_count: int,
    latest_activity_date: date | None,
    as_of_date: date | None = None,
) -> dict:
    """
    Calculate a prioritization score for one account.

    Maximum possible score: 100.

    The score is composed of:

    - Potential value: up to 30 points
    - Sales stage: up to 30 points
    - Follow-up urgency: up to 20 points
    - Recent activity: up to 10 points
    - Contact coverage: up to 10 points
    """

    if as_of_date is None:
        as_of_date = date.today()

    score = 0
    reasons = []

    # Potential-value component: maximum 30 points.
    potential_value = account.potential_value or Decimal("0.00")

    if potential_value >= Decimal("100000.00"):
        value_points = 30
    elif potential_value >= Decimal("50000.00"):
        value_points = 22
    elif potential_value >= Decimal("25000.00"):
        value_points = 15
    elif potential_value > Decimal("0.00"):
        value_points = 8
    else:
        value_points = 0

    score += value_points

    if value_points > 0:
        reasons.append(
            f"potential value contributes {value_points} points"
        )

    # Sales-stage component: maximum 30 points.
    stage = (account.sales_stage or "prospect").lower()
    stage_points = STAGE_POINTS.get(stage, 10)

    score += min(stage_points, 30)

    if stage_points > 0:
        reasons.append(
            f"{stage} stage contributes "
            f"{min(stage_points, 30)} points"
        )

    # Follow-up urgency: maximum 20 points.
    if account.next_follow_up_date is None:
        follow_up_points = 0
    elif account.next_follow_up_date < as_of_date:
        follow_up_points = 20
        reasons.append("follow-up is overdue")
    elif account.next_follow_up_date == as_of_date:
        follow_up_points = 18
        reasons.append("follow-up is due today")
    elif account.next_follow_up_date <= (
        as_of_date + timedelta(days=7)
    ):
        follow_up_points = 12
        reasons.append("follow-up is due within 7 days")
    else:
        follow_up_points = 5

    score += follow_up_points

    # Activity component: maximum 10 points.
    if latest_activity_date is None:
        activity_points = 0
        reasons.append("no sales activity recorded")
    else:
        days_since_activity = (
            as_of_date - latest_activity_date
        ).days

        if days_since_activity <= 7:
            activity_points = 10
            reasons.append("activity recorded within 7 days")
        elif days_since_activity <= 30:
            activity_points = 6
            reasons.append("activity recorded within 30 days")
        else:
            activity_points = 2
            reasons.append("sales activity is becoming old")

    score += activity_points

    # Contact-coverage component: maximum 10 points.
    contact_count = len(account.contacts)
    has_primary_contact = any(
        contact.is_primary
        for contact in account.contacts
    )

    if has_primary_contact and contact_count >= 2:
        contact_points = 10
        reasons.append("primary and secondary contacts identified")
    elif has_primary_contact:
        contact_points = 7
        reasons.append("primary contact identified")
    elif contact_count > 0:
        contact_points = 4
        reasons.append("contact exists but no primary contact is set")
    else:
        contact_points = 0
        reasons.append("no contact recorded")

    score += contact_points

    score = min(score, 100)

    if score >= 75:
        priority = "HIGH"
    elif score >= 50:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    return {
        "account_id": account.id,
        "company_name": account.company_name,
        "industry": account.industry,
        "sales_stage": account.sales_stage,
        "potential_value": potential_value,
        "score": score,
        "priority": priority,
        "activity_count": activity_count,
        "latest_activity_date": latest_activity_date,
        "reasons": reasons,
    }


def score_all_accounts(
    as_of_date: date | None = None,
) -> list[dict]:
    """Score all accounts and return them from highest to lowest."""

    if as_of_date is None:
        as_of_date = date.today()

    session = get_session()

    try:
        accounts = session.scalars(
            select(Account)
            .options(selectinload(Account.contacts))
            .order_by(Account.company_name)
        ).all()

        scored_accounts = []

        for account in accounts:
            activity_count = session.scalar(
                select(func.count(Activity.id)).where(
                    Activity.account_id == account.id
                )
            ) or 0

            latest_activity_date = session.scalar(
                select(func.max(Activity.activity_date)).where(
                    Activity.account_id == account.id
                )
            )

            score = calculate_account_score(
                account=account,
                activity_count=activity_count,
                latest_activity_date=latest_activity_date,
                as_of_date=as_of_date,
            )

            scored_accounts.append(score)

        return sorted(
            scored_accounts,
            key=lambda item: (
                -item["score"],
                -item["potential_value"],
                item["company_name"],
            ),
        )

    finally:
        session.close()


def print_account_score(scored_account: dict) -> None:
    """Print one account score."""

    print(
        f"[{scored_account['account_id']}] "
        f"{scored_account['company_name']} | "
        f"Score: {scored_account['score']}/100 | "
        f"Priority: {scored_account['priority']} | "
        f"Stage: {scored_account['sales_stage']} | "
        f"Potential: "
        f"${scored_account['potential_value']:,.2f}"
    )

    print(
        f"  Activities: "
        f"{scored_account['activity_count']} | "
        f"Latest activity: "
        f"{scored_account['latest_activity_date'] or 'None'}"
    )

    print(
        "  Reasons: "
        + "; ".join(scored_account["reasons"])
    )


if __name__ == "__main__":
    create_tables()

    print("\nPrioritized accounts")
    print("--------------------")

    scored_accounts = score_all_accounts()

    if not scored_accounts:
        print("No accounts found.")
    else:
        for scored_account in scored_accounts:
            print_account_score(scored_account)
