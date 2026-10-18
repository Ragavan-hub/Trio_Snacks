"""
Database models for the Trio Snacks POS & Shop application
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

CATEGORY_LABELS = {
    "Bread_omelete": "Bread Omelette",
    "bread_omelete": "Bread Omelette",
    "Bread Omelette": "Bread Omelette",
    "Sixtyfive_65": "Sixty Five (65)",
    "sixtyfive_65": "Sixty Five (65)",
    "Sixty Five (65)": "Sixty Five (65)",
    "sandwitch": "Sandwich",
    "Sandwitch": "Sandwich",
    "Sandwich": "Sandwich",
    "Bakery": "Bakery",
    "bakery": "Bakery",
    "Drinks": "Drinks & Beverages",
    "drinks": "Drinks & Beverages",
    "Snacks": "Crispy Snacks",
    "snacks": "Crispy Snacks",
    "Sweets": "Sweets & Desserts",
    "sweets": "Sweets & Desserts",
}


def format_category_label(raw_category: str) -> str:
    """Convert raw database category key into a human-friendly display name."""
    if not raw_category:
        return "General"
    if raw_category in CATEGORY_LABELS:
        return CATEGORY_LABELS[raw_category]
    return raw_category.replace("_", " ").strip().title()


class User(db.Model):
    """User model for admin and cashier accounts"""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="cashier")  # admin or cashier
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship("Order", backref="user", lazy=True)

    def set_password(self, password: str) -> None:
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        return check_password_hash(self.password_hash, password)

    def is_admin(self) -> bool:
        """Return True if user has admin privileges"""
        return self.role == "admin"

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"


class Product(db.Model):
    """Product model for snacks inventory & menu"""
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, default=999, nullable=False)
    description = db.Column(db.Text, default="")
    image_url = db.Column(db.String(255))
    barcode = db.Column(db.String(100), unique=True, index=True, nullable=True)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order_items = db.relationship("OrderItem", backref="product", lazy=True)

    @property
    def category_display(self) -> str:
        """Clean human-readable category label"""
        return format_category_label(self.category)

    def is_low_stock(self, threshold: int = 10) -> bool:
        """Check if product is low on stock"""
        return self.stock_quantity <= threshold

    def __repr__(self) -> str:
        return f"<Product {self.name}>"


class Order(db.Model):
    """Order model for POS bills/invoices"""
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_name = db.Column(db.String(200), default="")
    customer_phone = db.Column(db.String(20), default="")
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    tax_amount = db.Column(db.Float, nullable=False, default=0.0)
    discount_amount = db.Column(db.Float, nullable=False, default=0.0)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    items = db.relationship(
        "OrderItem", backref="order", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Order {self.invoice_number}>"


class OrderItem(db.Model):
    """OrderItem model for line items in each order"""
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    @property
    def product_name(self) -> str:
        """Safe product name lookup even if product record was archived"""
        return self.product.name if self.product else f"Item #{self.product_id}"

    def __repr__(self) -> str:
        return f"<OrderItem {self.id}>"


class Setting(db.Model):
    """Setting model for store configuration"""
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Setting {self.key}>"


class Offer(db.Model):
    """Offer model for promotional banners on the home page"""
    __tablename__ = "offers"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Offer {self.title}>"
