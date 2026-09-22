from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


def utc_now() -> datetime:
    """
    Return the current UTC time as a naive datetime.

    The database uses timezone-naive DateTime columns, so the
    timezone-aware UTC value is converted to a naive UTC value.
    """

    return datetime.now(timezone.utc).replace(
        tzinfo=None
    )


class Account(Base):
    """A company or organization being developed as a sales account."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    company_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    industry: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    account_owner: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
    )

    potential_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    sales_stage: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="prospect",
        index=True,
    )

    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    website: Mapped[Optional[str]] = mapped_column(
        String(300),
        nullable=True,
    )

    address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    next_follow_up_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    contacts: Mapped[list["Contact"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )

    activities: Mapped[list["Activity"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Account("
            f"id={self.id}, "
            f"company_name={self.company_name!r}, "
            f"sales_stage={self.sales_stage!r}"
            f")>"
        )


class Contact(Base):
    """A person associated with a sales account."""

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=False,
        index=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    job_title: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
    )

    email: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        index=True,
    )

    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    is_primary: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    account: Mapped["Account"] = relationship(
        back_populates="contacts",
    )

    activities: Mapped[list["Activity"]] = relationship(
        back_populates="contact",
        cascade="all, delete-orphan",
    )

    @property
    def full_name(self) -> str:
        """Return the contact's full name."""

        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return (
            f"<Contact("
            f"id={self.id}, "
            f"full_name={self.full_name!r}, "
            f"account_id={self.account_id}"
            f")>"
        )


class Order(Base):
    """An actual sale or invoice issued to an account."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=False,
        index=True,
    )

    order_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    product_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    grace_period_days: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    account: Mapped["Account"] = relationship(
        back_populates="orders",
    )

    payments: Mapped[list["Payment"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )

    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )

    fulfillment: Mapped[Optional["Fulfillment"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        uselist=False,
    )

    @property
    def grace_period_end_date(self) -> date:
        """Return the final date allowed by the grace period."""

        return self.due_date + timedelta(
            days=self.grace_period_days
        )

    def __repr__(self) -> str:
        return (
            f"<Order("
            f"id={self.id}, "
            f"order_number={self.order_number!r}, "
            f"total_amount={self.total_amount}"
            f")>"
        )


class Payment(Base):
    """A payment received against an order."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )

    payment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    payment_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    reference: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    order: Mapped["Order"] = relationship(
        back_populates="payments",
    )

    def __repr__(self) -> str:
        return (
            f"<Payment("
            f"id={self.id}, "
            f"amount={self.amount}, "
            f"order_id={self.order_id}"
            f")>"
        )


class Alert(Base):
    """A persistent alert related to an order."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )

    alert_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MEDIUM",
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    alert_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    is_acknowledged: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    order: Mapped["Order"] = relationship(
        back_populates="alerts",
    )

    def __repr__(self) -> str:
        return (
            f"<Alert("
            f"id={self.id}, "
            f"order_id={self.order_id}, "
            f"alert_type={self.alert_type!r}, "
            f"priority={self.priority!r}"
            f")>"
        )


class Activity(Base):
    """A sales interaction or account-development activity."""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=False,
        index=True,
    )

    contact_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("contacts.id"),
        nullable=True,
        index=True,
    )

    activity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    activity_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    subject: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    next_action: Mapped[Optional[str]] = mapped_column(
        String(300),
        nullable=True,
    )

    next_action_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    account: Mapped["Account"] = relationship(
        back_populates="activities",
    )

    contact: Mapped[Optional["Contact"]] = relationship(
        back_populates="activities",
    )

    def __repr__(self) -> str:
        return (
            f"<Activity("
            f"id={self.id}, "
            f"activity_type={self.activity_type!r}, "
            f"subject={self.subject!r}"
            f")>"
        )


class Product(Base):
    """A product or service offered by the business."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    sku: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    stock_quantity: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    reorder_level: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    order_items: Mapped[list["OrderItem"]] = relationship(
        back_populates="product",
    )

    @property
    def is_low_stock(self) -> bool:
        """Return True when stock is at or below reorder level."""

        return self.stock_quantity <= self.reorder_level

    def __repr__(self) -> str:
        return (
            f"<Product("
            f"id={self.id}, "
            f"sku={self.sku!r}, "
            f"name={self.name!r}, "
            f"stock_quantity={self.stock_quantity}"
            f")>"
        )


class OrderItem(Base):
    """A product line included in an order."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        nullable=False,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    line_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    order: Mapped["Order"] = relationship(
        back_populates="items",
    )

    product: Mapped["Product"] = relationship(
        back_populates="order_items",
    )

    def __repr__(self) -> str:
        return (
            f"<OrderItem("
            f"id={self.id}, "
            f"order_id={self.order_id}, "
            f"product_id={self.product_id}, "
            f"quantity={self.quantity}, "
            f"line_total={self.line_total}"
            f")>"
        )


class Fulfillment(Base):
    """Delivery and fulfillment information for an order."""

    __tablename__ = "fulfillments"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    fulfillment_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="not_started",
        index=True,
    )

    delivery_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    delivery_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    tracking_number: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
    )

    delivery_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    customer_accepted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    order: Mapped["Order"] = relationship(
        back_populates="fulfillment",
    )

    def __repr__(self) -> str:
        return (
            f"<Fulfillment("
            f"id={self.id}, "
            f"order_id={self.order_id}, "
            f"status={self.fulfillment_status!r}"
            f")>"
        )
