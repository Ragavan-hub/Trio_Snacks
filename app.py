"""
Main Flask application for Trio Snacks Shop & POS System
"""
import os
import uuid
from datetime import datetime, timedelta
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    send_file,
    send_from_directory,
    flash,
)
from werkzeug.utils import secure_filename
from models import (
    db,
    User,
    Product,
    Order,
    OrderItem,
    Setting,
    Offer,
    format_category_label,
)
from auth import login_required, admin_required, get_current_user
from pdf_generator import generate_invoice_pdf
from config import Config, BASE_DIR

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
app.config.from_object(Config)

# Initialize SQLAlchemy
db.init_app(app)

# Ensure upload directories exist
for folder in (app.config["UPLOAD_FOLDER"], app.config["LOGO_UPLOAD_FOLDER"]):
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception:
        pass

_db_initialized = False


def allowed_file(filename: str) -> bool:
    """Validate uploaded image extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_IMAGE_EXTENSIONS"]
    )


def get_setting_value(key: str, default: str = "") -> str:
    """Fetch a setting value by key with fallback."""
    try:
        setting = Setting.query.filter_by(key=key).first()
        return setting.value if setting and setting.value is not None else default
    except Exception:
        return default


def get_effective_tax_rate() -> float:
    """Return combined tax + GST rate configured in settings."""
    try:
        tax = float(get_setting_value("tax_rate", "5.0") or 0.0)
        gst = float(get_setting_value("gst_rate", "0.0") or 0.0)
        return max(0.0, round(tax + gst, 2))
    except (ValueError, TypeError):
        return 5.0


@app.template_filter("format_category")
def format_category_filter(value: str) -> str:
    """Jinja filter to display clean category titles."""
    return format_category_label(value)


@app.context_processor
def inject_global_context():
    """Provide global shop branding and user state to all templates."""
    shop_name = get_setting_value("shop_name", "Trio Snacks")
    shop_logo = get_setting_value(
        "shop_logo", "20260103_141024_WhatsApp_Image_2026-01-03_at_12.56.07_PM.jpeg"
    )
    shop_address = get_setting_value("shop_address", "123 Main Street, City")
    shop_phone = get_setting_value("shop_phone", "+91 9876543210")
    return {
        "global_shop_name": shop_name,
        "global_shop_logo": shop_logo,
        "global_shop_address": shop_address,
        "global_shop_phone": shop_phone,
        "current_year": datetime.now().year,
    }


def init_db():
    """Initialize database tables and default seed records if missing."""
    global _db_initialized
    if _db_initialized:
        return

    try:
        with app.app_context():
            db.create_all()

            # 1. Seed default Admin & Cashier users if missing
            try:
                if not User.query.filter_by(username="admin").first():
                    admin = User(username="admin", role="admin")
                    admin.set_password("admin123")
                    db.session.add(admin)

                if not User.query.filter_by(username="cashier").first():
                    cashier = User(username="cashier", role="cashier")
                    cashier.set_password("cashier123")
                    db.session.add(cashier)

                db.session.commit()
            except Exception as exc:
                db.session.rollback()
                print(f"Error seeding default users: {exc}")

            # 2. Seed default shop settings if missing
            try:
                default_settings = {
                    "shop_name": "Trio Snacks",
                    "shop_address": "123 Main Street, City",
                    "shop_phone": "+91 9876543210",
                    "tax_rate": "5.0",
                    "gst_rate": "0.0",
                    "stock_alert_threshold": "10",
                    "invoice_footer": "Thank you for your business!",
                    "shop_logo": "20260103_141024_WhatsApp_Image_2026-01-03_at_12.56.07_PM.jpeg",
                }
                for key, value in default_settings.items():
                    if not Setting.query.filter_by(key=key).first():
                        db.session.add(Setting(key=key, value=value))
                db.session.commit()
            except Exception as exc:
                db.session.rollback()
                print(f"Error seeding settings: {exc}")

            # 3. Seed default special offers if empty
            try:
                if Offer.query.count() == 0:
                    default_offers = [
                        {
                            "title": "Buy 2 Get 1 Free",
                            "description": "On selected chips and crispy snacks",
                            "order": 0,
                        },
                        {
                            "title": "Weekend Special",
                            "description": "20% off on all fresh bakery items",
                            "order": 1,
                        },
                        {
                            "title": "Happy Hours",
                            "description": "10% discount on hot snacks (7 PM - 9 PM)",
                            "order": 2,
                        },
                    ]
                    for item in default_offers:
                        db.session.add(
                            Offer(
                                title=item["title"],
                                description=item["description"],
                                display_order=item["order"],
                                is_active=True,
                            )
                        )
                    db.session.commit()
            except Exception as exc:
                db.session.rollback()
                print(f"Error seeding offers: {exc}")

            # 4. Seed initial products if database is completely empty (e.g., fresh cloud Postgres)
            try:
                if Product.query.count() == 0:
                    initial_products = [
                        Product(
                            name="Plain Bread omelete",
                            category="Bread_omelete",
                            price=30.0,
                            stock_quantity=999,
                            description="Classic fluffy egg omelette toasted with fresh buttered bread slices and tangy tomato sauce.",
                            image_url="20260103_145537_R.jpg",
                            is_available=True,
                        ),
                        Product(
                            name="Baby corn 65",
                            category="Sixtyfive_65",
                            price=40.0,
                            stock_quantity=999,
                            description="Crispy golden-fried baby corn marinated in signature South Indian 65 spices, served with onion salad.",
                            image_url="20260103_150006_OIP.webp",
                            is_available=True,
                        ),
                    ]
                    db.session.add_all(initial_products)
                    db.session.commit()
            except Exception as exc:
                db.session.rollback()
                print(f"Error seeding initial products: {exc}")

            _db_initialized = True
    except Exception as exc:
        print(f"Database initialization warning: {exc}")


@app.before_request
def ensure_db_ready():
    """Ensure database tables and seed data exist before handling requests."""
    if not _db_initialized:
        init_db()


if not Config.IS_VERCEL:
    init_db()


# ==================== Uploaded Media Fallback Route ====================

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """Serve runtime uploaded files from /tmp on Vercel or static/images locally."""
    tmp_products = "/tmp/static/images/products"
    tmp_logos = "/tmp/static/images"
    static_products = os.path.join(BASE_DIR, "static", "images", "products")
    static_logos = os.path.join(BASE_DIR, "static", "images")

    for directory in (tmp_products, static_products, tmp_logos, static_logos):
        candidate = os.path.join(directory, filename)
        if os.path.isfile(candidate):
            return send_from_directory(directory, filename)
    return ("File not found", 404)


# ==================== Public Routes ====================

@app.route("/")
def home():
    """Public landing page showcasing brand, active offers, and popular snacks."""
    popular_rows = (
        db.session.query(
            Product, db.func.coalesce(db.func.sum(OrderItem.quantity), 0).label("total_sold")
        )
        .outerjoin(OrderItem)
        .filter(Product.is_available.is_(True))
        .group_by(Product.id)
        .order_by(db.desc("total_sold"), Product.id.asc())
        .limit(6)
        .all()
    )
    popular = [row[0] for row in popular_rows]

    shop_name = get_setting_value("shop_name", "Trio Snacks")
    shop_logo = get_setting_value(
        "shop_logo", "20260103_141024_WhatsApp_Image_2026-01-03_at_12.56.07_PM.jpeg"
    )
    offers = (
        Offer.query.filter_by(is_active=True)
        .order_by(Offer.display_order.asc(), Offer.id.asc())
        .all()
    )

    return render_template(
        "home.html",
        popular_products=popular,
        shop_name=shop_name,
        shop_logo=shop_logo,
        offers=offers,
    )


@app.route("/menu")
def menu():
    """Public interactive menu page with category filtering and search."""
    category = request.args.get("category", "all").strip()
    search = request.args.get("search", "").strip()

    query = Product.query.filter_by(is_available=True)

    if category and category != "all":
        query = query.filter_by(category=category)

    if search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
                Product.category.ilike(f"%{search}%"),
            )
        )

    products = query.order_by(Product.name.asc()).all()

    raw_categories = (
        db.session.query(Product.category)
        .filter(Product.is_available.is_(True))
        .distinct()
        .order_by(Product.category.asc())
        .all()
    )
    categories = [c[0] for c in raw_categories if c[0]]

    return render_template(
        "menu.html",
        products=products,
        categories=categories,
        current_category=category,
        search_query=search,
    )


# ==================== Authentication Routes ====================

@app.route("/login", methods=["GET", "POST"])
def login():
    """Staff login page for Admin and Cashier roles."""
    if session.get("user_id") and get_current_user():
        user = get_current_user()
        return redirect(url_for("admin_dashboard" if user.is_admin() else "billing"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            session.permanent = True

            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)

            return redirect(url_for("admin_dashboard" if user.is_admin() else "billing"))

        return render_template("login.html", error="Invalid username or password. Please try again.")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """Clear session and log out staff member."""
    session.clear()
    flash("You have been logged out safely.", "info")
    return redirect(url_for("home"))


# ==================== Billing / POS Routes ====================

@app.route("/billing")
@login_required
def billing():
    """POS Billing terminal."""
    products = Product.query.filter_by(is_available=True).order_by(Product.name.asc()).all()
    raw_categories = (
        db.session.query(Product.category)
        .filter(Product.is_available.is_(True))
        .distinct()
        .order_by(Product.category.asc())
        .all()
    )
    categories = [c[0] for c in raw_categories if c[0]]
    effective_tax_rate = get_effective_tax_rate()

    return render_template(
        "billing.html",
        products=products,
        categories=categories,
        tax_rate=effective_tax_rate,
    )


@app.route("/api/products", methods=["GET"])
@login_required
def api_products():
    """JSON endpoint to filter/search products or lookup by barcode."""
    category = request.args.get("category", "all").strip()
    search = request.args.get("search", "").strip()
    barcode = request.args.get("barcode", "").strip()

    query = Product.query.filter_by(is_available=True)

    if barcode:
        query = query.filter(
            db.or_(Product.barcode == barcode, Product.name.ilike(f"%{barcode}%"))
        )
    else:
        if category and category != "all":
            query = query.filter_by(category=category)
        if search:
            query = query.filter(
                db.or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.category.ilike(f"%{search}%"),
                )
            )

    products = query.order_by(Product.name.asc()).all()

    return jsonify(
        [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "category_display": p.category_display,
                "price": float(p.price),
                "stock": int(p.stock_quantity),
                "barcode": p.barcode or "",
                "image_url": p.image_url or "",
            }
            for p in products
        ]
    )


@app.route("/api/cart", methods=["GET"])
@login_required
def api_cart():
    """Return current session cart."""
    return jsonify({"cart": session.get("cart", {}), "tax_rate": get_effective_tax_rate()})


@app.route("/api/cart/add", methods=["POST"])
@login_required
def api_cart_add():
    """Add or increment a product in the POS session cart."""
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    try:
        quantity = int(data.get("quantity", 1))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid quantity"}), 400

    if quantity <= 0:
        return jsonify({"error": "Quantity must be at least 1"}), 400

    product = db.session.get(Product, int(product_id)) if product_id else None
    if not product or not product.is_available:
        return jsonify({"error": "Product not found or unavailable"}), 404

    cart = session.get("cart", {})
    pid_key = str(product.id)

    if pid_key in cart:
        cart[pid_key]["quantity"] += quantity
        cart[pid_key]["price"] = float(product.price)
        cart[pid_key]["name"] = product.name
    else:
        cart[pid_key] = {
            "name": product.name,
            "price": float(product.price),
            "quantity": quantity,
        }

    session["cart"] = cart
    session.modified = True
    return jsonify({"success": True, "cart": cart})


@app.route("/api/cart/update", methods=["POST"])
@login_required
def api_cart_update():
    """Update item quantity in the POS session cart."""
    data = request.get_json(silent=True) or {}
    product_id = str(data.get("product_id", ""))
    try:
        quantity = int(data.get("quantity", 1))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid quantity"}), 400

    cart = session.get("cart", {})
    if product_id not in cart:
        return jsonify({"error": "Item not in cart"}), 404

    if quantity <= 0:
        del cart[product_id]
    else:
        cart[product_id]["quantity"] = min(quantity, 999)

    session["cart"] = cart
    session.modified = True
    return jsonify({"success": True, "cart": cart})


@app.route("/api/cart/remove", methods=["POST"])
@login_required
def api_cart_remove():
    """Remove an item from the POS session cart."""
    data = request.get_json(silent=True) or {}
    product_id = str(data.get("product_id", ""))

    cart = session.get("cart", {})
    if product_id in cart:
        del cart[product_id]

    session["cart"] = cart
    session.modified = True
    return jsonify({"success": True, "cart": cart})


@app.route("/api/cart/clear", methods=["POST"])
@login_required
def api_cart_clear():
    """Empty the current POS cart."""
    session["cart"] = {}
    session.modified = True
    return jsonify({"success": True, "cart": {}})


@app.route("/api/order/process", methods=["POST"])
@login_required
def api_order_process():
    """Process POS checkout, create Order & OrderItems, and return invoice details."""
    try:
        data = request.get_json(silent=True) or {}
        cart = session.get("cart", {})

        if not cart:
            return jsonify({"error": "Cannot process an empty cart."}), 400

        customer_name = (data.get("customer_name") or "").strip()[:200]
        customer_phone = (data.get("customer_phone") or "").strip()[:20]
        try:
            discount = max(0.0, float(data.get("discount", 0) or 0.0))
        except (ValueError, TypeError):
            discount = 0.0

        effective_tax_rate = get_effective_tax_rate()

        subtotal = round(
            sum(float(item["price"]) * int(item["quantity"]) for item in cart.values()), 2
        )
        discount_amount = round(min(discount, subtotal), 2)
        taxable_amount = max(0.0, subtotal - discount_amount)
        tax_amount = round((taxable_amount * effective_tax_rate) / 100.0, 2)
        total_amount = round(taxable_amount + tax_amount, 2)

        invoice_number = (
            f"INV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        )

        order = Order(
            invoice_number=invoice_number,
            customer_name=customer_name,
            customer_phone=customer_phone,
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            created_by=session["user_id"],
        )
        db.session.add(order)
        db.session.flush()

        for product_id_str, item in cart.items():
            product_id = int(product_id_str)
            product = db.session.get(Product, product_id)
            if not product:
                db.session.rollback()
                return jsonify({"error": f"Product '{item.get('name')}' no longer exists."}), 400

            qty = int(item["quantity"])
            unit_price = float(product.price)
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=qty,
                unit_price=unit_price,
                total_price=round(unit_price * qty, 2),
            )
            db.session.add(order_item)

        db.session.commit()

        session["cart"] = {}
        session.modified = True

        return jsonify(
            {
                "success": True,
                "order_id": order.id,
                "invoice_number": invoice_number,
                "total_amount": total_amount,
                "pdf_url": url_for("invoice_pdf", order_id=order.id),
                "detail_url": url_for("order_detail", order_id=order.id),
            }
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Error processing order: {str(exc)}"}), 500


@app.route("/invoice/<int:order_id>/pdf")
@login_required
def invoice_pdf(order_id: int):
    """Generate and download printable PDF invoice."""
    order = db.session.get(Order, order_id)
    if not order:
        return ("Order not found", 404)

    user = get_current_user()
    if not user.is_admin() and order.created_by != session["user_id"]:
        return redirect(url_for("billing"))

    pdf_buffer = generate_invoice_pdf(order)
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"invoice_{order.invoice_number}.pdf",
    )


# ==================== Orders History Routes ====================

@app.route("/orders")
@login_required
def orders():
    """Orders history & sales summary page."""
    period = request.args.get("period", "all").strip()
    today = datetime.now().date()

    if period == "today":
        start_date = datetime.combine(today, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
    elif period == "week":
        start_date = datetime.combine(today - timedelta(days=7), datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
    elif period == "month":
        start_date = datetime.combine(today - timedelta(days=30), datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
    else:
        period = "all"
        start_date = None
        end_date = None

    query = Order.query
    user = get_current_user()
    if not user.is_admin():
        query = query.filter_by(created_by=session["user_id"])

    if start_date and end_date:
        query = query.filter(Order.created_at >= start_date, Order.created_at <= end_date)

    orders_list = query.order_by(Order.created_at.desc()).all()
    total_sales = sum(order.total_amount for order in orders_list)
    total_orders = len(orders_list)

    return render_template(
        "orders.html",
        orders=orders_list,
        period=period,
        total_sales=total_sales,
        total_orders=total_orders,
    )


@app.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id: int):
    """Detailed view of a single invoice/order."""
    order = db.session.get(Order, order_id)
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("orders"))

    user = get_current_user()
    if not user.is_admin() and order.created_by != session["user_id"]:
        return redirect(url_for("orders"))

    return render_template("order_detail.html", order=order)


@app.route("/orders/<int:order_id>/delete", methods=["POST"])
@admin_required
def order_delete(order_id: int):
    """Delete an order and its line items (Admin only)."""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    try:
        OrderItem.query.filter_by(order_id=order_id).delete()
        db.session.delete(order)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500


# ==================== Admin Routes ====================

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Admin analytics and store overview dashboard."""
    total_products = Product.query.filter_by(is_available=True).count()

    today = datetime.now().date()
    start_date = datetime.combine(today, datetime.min.time())
    end_date = datetime.combine(today, datetime.max.time())

    today_orders = Order.query.filter(
        Order.created_at >= start_date, Order.created_at <= end_date
    ).all()
    today_sales = sum(order.total_amount for order in today_orders)

    all_orders = Order.query.all()
    all_time_sales = sum(order.total_amount for order in all_orders)
    all_time_orders_count = len(all_orders)

    top_items = (
        db.session.query(
            Product.name,
            Product.category,
            db.func.sum(OrderItem.quantity).label("total_sold"),
            db.func.sum(OrderItem.total_price).label("total_revenue"),
        )
        .join(OrderItem)
        .group_by(Product.id)
        .order_by(db.desc("total_sold"))
        .limit(5)
        .all()
    )

    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()

    return render_template(
        "admin/dashboard.html",
        total_products=total_products,
        today_sales=today_sales,
        today_orders_count=len(today_orders),
        all_time_sales=all_time_sales,
        all_time_orders_count=all_time_orders_count,
        top_items=top_items,
        recent_orders=recent_orders,
    )


@app.route("/admin/products")
@admin_required
def admin_products():
    """Admin product catalog management."""
    products = Product.query.filter_by(is_available=True).order_by(Product.name.asc()).all()
    raw_categories = db.session.query(Product.category).distinct().all()
    categories = [c[0] for c in raw_categories if c[0]]
    return render_template("admin/products.html", products=products, categories=categories)


@app.route("/admin/products/add", methods=["POST"])
@admin_required
def admin_products_add():
    """Add a new snack product."""
    name = (request.form.get("name") or "").strip()
    category = (request.form.get("category") or "").strip()
    description = (request.form.get("description") or "").strip()

    try:
        price = max(0.0, float(request.form.get("price", 0)))
    except (ValueError, TypeError):
        flash("Invalid price entered.", "error")
        return redirect(url_for("admin_products"))

    if not name or not category:
        flash("Product name and category are required.", "error")
        return redirect(url_for("admin_products"))

    image_url = None
    if "image" in request.files:
        file = request.files["image"]
        if file and file.filename and allowed_file(file.filename):
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S_')}{secure_filename(file.filename)}"
            try:
                upload_dir = app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, filename))
                image_url = filename
            except Exception as exc:
                print(f"Image upload warning: {exc}")

    product = Product(
        name=name,
        category=category,
        price=price,
        stock_quantity=999,
        description=description,
        barcode=None,
        image_url=image_url,
        is_available=True,
    )
    db.session.add(product)
    db.session.commit()
    flash(f"Product '{name}' added to menu.", "success")
    return redirect(url_for("admin_products"))


@app.route("/admin/products/<int:product_id>/edit", methods=["POST"])
@admin_required
def admin_products_edit(product_id: int):
    """Update an existing product."""
    product = db.session.get(Product, product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("admin_products"))

    name = (request.form.get("name") or "").strip()
    category = (request.form.get("category") or "").strip()
    description = (request.form.get("description") or "").strip()

    try:
        price = max(0.0, float(request.form.get("price", product.price)))
    except (ValueError, TypeError):
        flash("Invalid price value.", "error")
        return redirect(url_for("admin_products"))

    if name:
        product.name = name
    if category:
        product.category = category
    product.price = price
    product.description = description
    product.is_available = True
    product.updated_at = datetime.utcnow()

    if "image" in request.files:
        file = request.files["image"]
        if file and file.filename and allowed_file(file.filename):
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S_')}{secure_filename(file.filename)}"
            try:
                upload_dir = app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, filename))
                product.image_url = filename
            except Exception as exc:
                print(f"Product image update warning: {exc}")

    db.session.commit()
    flash(f"Product '{product.name}' updated.", "success")
    return redirect(url_for("admin_products"))


@app.route("/admin/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def admin_products_delete(product_id: int):
    """Safely delete or archive a product without breaking historical invoices."""
    product = db.session.get(Product, product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("admin_products"))

    product_name = product.name
    has_orders = OrderItem.query.filter_by(product_id=product.id).first() is not None

    try:
        if has_orders:
            # Soft-archive so past invoices retain product name reference
            product.is_available = False
            db.session.commit()
            flash(
                f"'{product_name}' was removed from the active menu (preserved in past invoices).",
                "success",
            )
        else:
            db.session.delete(product)
            db.session.commit()
            flash(f"Product '{product_name}' deleted.", "success")
    except Exception as exc:
        db.session.rollback()
        flash(f"Could not remove product: {exc}", "error")

    return redirect(url_for("admin_products"))


@app.route("/admin/offers")
@admin_required
def admin_offers():
    """Manage promotional offers displayed on the home page."""
    offers = Offer.query.order_by(Offer.display_order.asc(), Offer.id.asc()).all()
    return render_template("admin/offers.html", offers=offers)


@app.route("/admin/offers/add", methods=["POST"])
@admin_required
def admin_offers_add():
    """Create a new promotional offer."""
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    try:
        display_order = int(request.form.get("display_order", 0) or 0)
    except ValueError:
        display_order = 0
    is_active = request.form.get("is_active") == "on"

    if not title or not description:
        flash("Offer title and description are required.", "error")
        return redirect(url_for("admin_offers"))

    offer = Offer(
        title=title,
        description=description,
        display_order=display_order,
        is_active=is_active,
    )
    db.session.add(offer)
    db.session.commit()
    flash(f"Offer '{title}' created.", "success")
    return redirect(url_for("admin_offers"))


@app.route("/admin/offers/<int:offer_id>/edit", methods=["POST"])
@admin_required
def admin_offers_edit(offer_id: int):
    """Update an existing promotional offer."""
    offer = db.session.get(Offer, offer_id)
    if not offer:
        flash("Offer not found.", "error")
        return redirect(url_for("admin_offers"))

    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    try:
        display_order = int(request.form.get("display_order", 0) or 0)
    except ValueError:
        display_order = 0

    if title:
        offer.title = title
    if description:
        offer.description = description
    offer.display_order = display_order
    offer.is_active = request.form.get("is_active") == "on"
    offer.updated_at = datetime.utcnow()

    db.session.commit()
    flash(f"Offer '{offer.title}' updated.", "success")
    return redirect(url_for("admin_offers"))


@app.route("/admin/offers/<int:offer_id>/delete", methods=["POST"])
@admin_required
def admin_offers_delete(offer_id: int):
    """Delete a promotional offer."""
    offer = db.session.get(Offer, offer_id)
    if offer:
        title = offer.title
        db.session.delete(offer)
        db.session.commit()
        flash(f"Offer '{title}' deleted.", "success")
    return redirect(url_for("admin_offers"))


@app.route("/admin/settings")
@admin_required
def admin_settings():
    """Store & billing configuration page."""
    settings = {s.key: s.value for s in Setting.query.all()}
    return render_template("admin/settings.html", settings=settings)


@app.route("/admin/settings/update", methods=["POST"])
@admin_required
def admin_settings_update():
    """Update store branding and tax/billing settings."""
    if "logo" in request.files:
        file = request.files["logo"]
        if file and file.filename and allowed_file(file.filename):
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S_')}{secure_filename(file.filename)}"
            try:
                logo_dir = app.config["LOGO_UPLOAD_FOLDER"]
                os.makedirs(logo_dir, exist_ok=True)
                file.save(os.path.join(logo_dir, filename))

                logo_setting = Setting.query.filter_by(key="shop_logo").first()
                if logo_setting:
                    logo_setting.value = filename
                else:
                    db.session.add(Setting(key="shop_logo", value=filename))
            except Exception as exc:
                print(f"Logo upload warning: {exc}")

    setting_keys = [
        "shop_name",
        "shop_address",
        "shop_phone",
        "tax_rate",
        "gst_rate",
        "stock_alert_threshold",
        "invoice_footer",
    ]
    for key in setting_keys:
        if key in request.form:
            value = (request.form.get(key) or "").strip()
            setting = Setting.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                db.session.add(Setting(key=key, value=value))

    db.session.commit()
    flash("Store settings saved.", "success")
    return redirect(url_for("admin_settings"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=not Config.IS_VERCEL)
