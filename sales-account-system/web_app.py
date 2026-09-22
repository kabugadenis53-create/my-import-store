import threading
import webbrowser
from datetime import date
from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_HALF_UP,
)

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    url_for,
)

from src.account_manager import (
    add_account,
    list_accounts,
    search_accounts,
)
from src.customer_alerts import get_customer_alerts
from src.database import create_tables
from src.payment_manager import (
    create_order,
    list_orders,
    record_payment,
)
from src.product_manager import (
    add_product,
    adjust_stock,
    list_low_stock_products,
    list_products,
    search_products,
)


app = Flask(__name__)


def calculate_collection_rate(
    total_sales: Decimal,
    total_collected: Decimal,
) -> Decimal:
    """Calculate collected cash as a percentage of sales."""

    if total_sales <= Decimal("0.00"):
        return Decimal("0.00")

    rate = (
        total_collected
        / total_sales
        * Decimal("100.00")
    )

    return rate.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def build_dashboard_data() -> dict:
    """Build browser-ready dashboard data."""

    accounts = list_accounts()
    orders = list_orders()
    products = list_products(active_only=True)
    low_stock_products = list_low_stock_products()
    alerts = get_customer_alerts(days_ahead=7)

    total_sales = sum(
        (
            order["total_amount"]
            for order in orders
        ),
        Decimal("0.00"),
    )

    total_collected = sum(
        (
            order["amount_paid"]
            for order in orders
        ),
        Decimal("0.00"),
    )

    total_outstanding = sum(
        (
            order["balance_due"]
            for order in orders
        ),
        Decimal("0.00"),
    )

    overdue_orders = [
        order
        for order in orders
        if order["status"] == "overdue"
    ]

    paid_orders = [
        order
        for order in orders
        if order["status"] == "paid"
    ]

    return {
        "as_of_date": date.today(),
        "accounts": accounts,
        "orders": orders,
        "products": products,
        "low_stock_products": low_stock_products,
        "alerts": alerts,
        "total_accounts": len(accounts),
        "total_products": len(products),
        "total_orders": len(orders),
        "total_sales": total_sales,
        "total_collected": total_collected,
        "total_outstanding": total_outstanding,
        "collection_rate": calculate_collection_rate(
            total_sales=total_sales,
            total_collected=total_collected,
        ),
        "paid_orders": len(paid_orders),
        "overdue_orders": len(overdue_orders),
    }


@app.template_filter("money")
def money_filter(value) -> str:
    """Format values as currency."""

    if value is None:
        value = Decimal("0.00")

    return f"${Decimal(value):,.2f}"


@app.template_filter("date_value")
def date_filter(value) -> str:
    """Format date values."""

    if value is None:
        return "Not set"

    return value.strftime("%Y-%m-%d")


@app.route("/")
def dashboard():
    """Render the main sales dashboard."""

    data = build_dashboard_data()

    return render_template(
        "dashboard.html",
        data=data,
    )


@app.route("/accounts")
def accounts_page():
    """Display and search customer accounts."""

    search_term = request.args.get(
        "q",
        "",
    ).strip()

    if search_term:
        accounts = search_accounts(search_term)
    else:
        accounts = list_accounts()

    return render_template(
        "accounts.html",
        accounts=accounts,
        search_term=search_term,
    )


@app.route(
    "/accounts/new",
    methods=["GET", "POST"],
)
def new_account():
    """Create a new sales account."""

    error = None

    if request.method == "POST":
        company_name = request.form.get(
            "company_name",
            "",
        ).strip()

        industry = request.form.get(
            "industry",
            "",
        ).strip() or None

        account_owner = request.form.get(
            "account_owner",
            "",
        ).strip() or None

        phone = request.form.get(
            "phone",
            "",
        ).strip() or None

        website = request.form.get(
            "website",
            "",
        ).strip() or None

        address = request.form.get(
            "address",
            "",
        ).strip() or None

        notes = request.form.get(
            "notes",
            "",
        ).strip() or None

        sales_stage = request.form.get(
            "sales_stage",
            "prospect",
        ).strip()

        potential_value_text = request.form.get(
            "potential_value",
            "",
        ).strip()

        follow_up_text = request.form.get(
            "next_follow_up_date",
            "",
        ).strip()

        try:
            potential_value = (
                Decimal(potential_value_text)
                if potential_value_text
                else None
            )

            follow_up_date = (
                date.fromisoformat(follow_up_text)
                if follow_up_text
                else None
            )

            add_account(
                company_name=company_name,
                industry=industry,
                account_owner=account_owner,
                potential_value=potential_value,
                sales_stage=sales_stage,
                phone=phone,
                website=website,
                address=address,
                notes=notes,
                next_follow_up_date=follow_up_date,
            )

            return redirect(
                url_for("accounts_page")
            )

        except (
            ValueError,
            TypeError,
            InvalidOperation,
        ) as exc:
            error = str(exc)

    return render_template(
        "account_form.html",
        error=error,
    )


@app.route("/orders")
def orders_page():
    """Display all orders and payment statuses."""

    orders = list_orders()

    return render_template(
        "orders.html",
        orders=orders,
    )


@app.route(
    "/orders/new",
    methods=["GET", "POST"],
)
def new_order():
    """Create a new sales order."""

    error = None
    accounts = list_accounts()

    if request.method == "POST":
        account_id_text = request.form.get(
            "account_id",
            "",
        ).strip()

        order_number = request.form.get(
            "order_number",
            "",
        ).strip()

        product_description = request.form.get(
            "product_description",
            "",
        ).strip()

        order_date_text = request.form.get(
            "order_date",
            "",
        ).strip()

        due_date_text = request.form.get(
            "due_date",
            "",
        ).strip()

        total_amount_text = request.form.get(
            "total_amount",
            "",
        ).strip()

        grace_period_text = request.form.get(
            "grace_period_days",
            "0",
        ).strip()

        notes = request.form.get(
            "notes",
            "",
        ).strip() or None

        try:
            account_id = int(account_id_text)

            order_date = date.fromisoformat(
                order_date_text
            )

            due_date = date.fromisoformat(
                due_date_text
            )

            total_amount = Decimal(
                total_amount_text
            )

            grace_period_days = int(
                grace_period_text or "0"
            )

            create_order(
                account_id=account_id,
                order_number=order_number,
                product_description=(
                    product_description
                ),
                order_date=order_date,
                due_date=due_date,
                total_amount=total_amount,
                grace_period_days=(
                    grace_period_days
                ),
                notes=notes,
            )

            return redirect(
                url_for("orders_page")
            )

        except (
            ValueError,
            TypeError,
            InvalidOperation,
        ) as exc:
            error = str(exc)

    return render_template(
        "order_form.html",
        accounts=accounts,
        error=error,
    )


@app.route(
    "/payments/new",
    methods=["GET", "POST"],
)
def new_payment():
    """Record a payment against an order."""

    error = None
    orders = list_orders()

    unpaid_orders = [
        order
        for order in orders
        if order["balance_due"] > Decimal("0.00")
    ]

    if request.method == "POST":
        order_id_text = request.form.get(
            "order_id",
            "",
        ).strip()

        payment_date_text = request.form.get(
            "payment_date",
            "",
        ).strip()

        amount_text = request.form.get(
            "amount",
            "",
        ).strip()

        payment_method = request.form.get(
            "payment_method",
            "",
        ).strip() or None

        reference = request.form.get(
            "reference",
            "",
        ).strip() or None

        notes = request.form.get(
            "notes",
            "",
        ).strip() or None

        try:
            order_id = int(order_id_text)

            payment_date = date.fromisoformat(
                payment_date_text
            )

            amount = Decimal(amount_text)

            record_payment(
                order_id=order_id,
                payment_date=payment_date,
                amount=amount,
                payment_method=payment_method,
                reference=reference,
                notes=notes,
            )

            return redirect(
                url_for("orders_page")
            )

        except (
            ValueError,
            TypeError,
            InvalidOperation,
        ) as exc:
            error = str(exc)

    return render_template(
        "payment_form.html",
        orders=unpaid_orders,
        error=error,
    )


@app.route("/products")
def products_page():
    """Display and search products."""

    search_term = request.args.get(
        "q",
        "",
    ).strip()

    show_low_stock = (
        request.args.get("low_stock") == "1"
    )

    if show_low_stock:
        products = list_low_stock_products()
    elif search_term:
        products = search_products(search_term)
    else:
        products = list_products(
            active_only=False
        )

    return render_template(
        "products.html",
        products=products,
        search_term=search_term,
        show_low_stock=show_low_stock,
    )


@app.route(
    "/products/new",
    methods=["GET", "POST"],
)
def new_product():
    """Create a new product."""

    error = None

    if request.method == "POST":
        sku = request.form.get(
            "sku",
            "",
        ).strip()

        name = request.form.get(
            "name",
            "",
        ).strip()

        category = request.form.get(
            "category",
            "",
        ).strip() or None

        description = request.form.get(
            "description",
            "",
        ).strip() or None

        unit_price_text = request.form.get(
            "unit_price",
            "",
        ).strip()

        stock_quantity_text = request.form.get(
            "stock_quantity",
            "0",
        ).strip()

        reorder_level_text = request.form.get(
            "reorder_level",
            "0",
        ).strip()

        try:
            unit_price = Decimal(
                unit_price_text
            )

            stock_quantity = int(
                stock_quantity_text or "0"
            )

            reorder_level = int(
                reorder_level_text or "0"
            )

            add_product(
                sku=sku,
                name=name,
                unit_price=unit_price,
                stock_quantity=stock_quantity,
                reorder_level=reorder_level,
                category=category,
                description=description,
            )

            return redirect(
                url_for("products_page")
            )

        except (
            ValueError,
            TypeError,
            InvalidOperation,
        ) as exc:
            error = str(exc)

    return render_template(
        "product_form.html",
        error=error,
    )


@app.route(
    "/products/stock",
    methods=["GET", "POST"],
)
def adjust_product_stock():
    """Increase or decrease product stock."""

    error = None
    products = list_products(
        active_only=False
    )

    if request.method == "POST":
        product_id_text = request.form.get(
            "product_id",
            "",
        ).strip()

        quantity_change_text = request.form.get(
            "quantity_change",
            "",
        ).strip()

        try:
            product_id = int(product_id_text)

            quantity_change = int(
                quantity_change_text
            )

            adjust_stock(
                product_id=product_id,
                quantity_change=quantity_change,
            )

            return redirect(
                url_for("products_page")
            )

        except (
            ValueError,
            TypeError,
        ) as exc:
            error = str(exc)

    return render_template(
        "stock_form.html",
        products=products,
        error=error,
    )


@app.route("/alerts")
def alerts_page():
    """Display customer and operational alerts."""

    alerts = get_customer_alerts(
        days_ahead=7
    )

    return render_template(
        "alerts.html",
        alerts=alerts,
    )


@app.route("/health")
def health():
    """Return a simple application health response."""

    return {
        "status": "healthy",
        "database": "connected",
    }


def open_browser() -> None:
    """Open the dashboard in the default browser."""

    webbrowser.open_new(
        "http://127.0.0.1:5000/"
     )


if __name__ == "__main__":
    create_tables()

    threading.Timer(
        1.0,
        open_browser,
    ).start()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False,
    )
