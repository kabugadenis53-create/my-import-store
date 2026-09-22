from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import create_tables, get_session
from src.models import Alert, Order
from src.payment_manager import (
    calculate_amount_paid,
    calculate_order_status,
)


def build_payment_alert(
    order: Order,
    as_of_date: date,
    days_ahead: int,
) -> dict | None:
    """
    Build one alert for an order.

    Returns None when the order does not currently require an alert.
    """

    amount_paid = calculate_amount_paid(order)
    balance_due = order.total_amount - amount_paid

    if balance_due <= Decimal("0.00"):
        return None

    status = calculate_order_status(
        total_amount=order.total_amount,
        amount_paid=amount_paid,
        due_date=order.due_date,
        grace_period_end_date=(
            order.grace_period_end_date
        ),
        as_of_date=as_of_date,
    )

    alert_window_end = (
        as_of_date + timedelta(days=days_ahead)
    )

    if status == "overdue":
        alert_type = "OVERDUE"
        priority = "HIGH"
        message = (
            "Payment is overdue and the grace period has ended."
        )

    elif status == "due":
        alert_type = "DUE_OR_GRACE_PERIOD"
        priority = "HIGH"
        message = (
            "Payment is due or currently within the grace period."
        )

    elif order.due_date == as_of_date:
        alert_type = "DUE_TODAY"
        priority = "HIGH"
        message = "Payment is due today."

    elif order.due_date <= alert_window_end:
        alert_type = "DUE_SOON"
        priority = "MEDIUM"
        message = (
            f"Payment is due within {days_ahead} days."
        )

    elif amount_paid > Decimal("0.00"):
        alert_type = "PARTIAL_PAYMENT"
        priority = "MEDIUM"
        message = (
            "Order has an outstanding partial balance."
        )

    else:
        return None

    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "alert_type": alert_type,
        "priority": priority,
        "message": message,
        "alert_date": as_of_date,
        "total_amount": order.total_amount,
        "amount_paid": amount_paid,
        "balance_due": balance_due,
        "due_date": order.due_date,
        "grace_period_end_date": (
            order.grace_period_end_date
        ),
        "status": status,
    }


def alert_already_exists(
    session,
    order_id: int,
    alert_type: str,
    alert_date: date,
) -> bool:
    """Check whether the same alert was already stored today."""

    existing_alert = session.scalar(
        select(Alert).where(
            Alert.order_id == order_id,
            Alert.alert_type == alert_type,
            Alert.alert_date == alert_date,
        )
    )

    return existing_alert is not None


def generate_and_store_payment_alerts(
    days_ahead: int = 7,
    as_of_date: date | None = None,
) -> list[Alert]:
    """
    Generate current payment alerts and save new alerts.

    Duplicate alerts for the same order, type, and date are not created.
    """

    if days_ahead < 0:
        raise ValueError(
            "days_ahead cannot be negative."
        )

    if as_of_date is None:
        as_of_date = date.today()

    session = get_session()
    saved_alerts = []

    try:
        orders = session.scalars(
            select(Order)
            .options(selectinload(Order.payments))
            .order_by(Order.due_date, Order.order_number)
        ).all()

        for order in orders:
            alert_data = build_payment_alert(
                order=order,
                as_of_date=as_of_date,
                days_ahead=days_ahead,
            )

            if alert_data is None:
                continue

            if alert_already_exists(
                session=session,
                order_id=alert_data["order_id"],
                alert_type=alert_data["alert_type"],
                alert_date=alert_data["alert_date"],
            ):
                continue

            alert = Alert(
                order_id=alert_data["order_id"],
                alert_type=alert_data["alert_type"],
                priority=alert_data["priority"],
                message=alert_data["message"],
                alert_date=alert_data["alert_date"],
            )

            session.add(alert)
            saved_alerts.append(alert)

        session.commit()

        for alert in saved_alerts:
            session.refresh(alert)

        return saved_alerts

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def list_unacknowledged_alerts() -> list[Alert]:
    """Return all alerts that have not been acknowledged."""

    session = get_session()

    try:
        alerts = session.scalars(
            select(Alert)
            .where(Alert.is_acknowledged.is_(False))
            .order_by(
                Alert.alert_date,
                Alert.priority,
                Alert.id,
            )
        ).all()

        return list(alerts)

    finally:
        session.close()


def acknowledge_alert(alert_id: int) -> Alert:
    """Mark an alert as acknowledged."""

    session = get_session()

    try:
        alert = session.get(Alert, alert_id)

        if alert is None:
            raise ValueError(
                f"No alert found with ID {alert_id}."
            )

        alert.is_acknowledged = True
        session.commit()
        session.refresh(alert)

        return alert

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def print_alert(alert: Alert) -> None:
    """Print one persistent alert."""

    print(
        f"[{alert.id}] "
        f"[{alert.priority}] "
        f"{alert.alert_type} | "
        f"Order: {alert.order_id} | "
        f"Date: {alert.alert_date} | "
        f"Acknowledged: "
        f"{'YES' if alert.is_acknowledged else 'NO'}"
    )
    print(f"  {alert.message}")


if __name__ == "__main__":
    create_tables()

    print("\nGenerating payment alerts...")
    new_alerts = generate_and_store_payment_alerts(
        days_ahead=7
    )

    print(f"New alerts created: {len(new_alerts)}")

    print("\nUnacknowledged payment alerts")
    print("-----------------------------")

    alerts = list_unacknowledged_alerts()

    if not alerts:
        print("No unacknowledged alerts.")
    else:
        for alert in alerts:
            print_alert(alert)
