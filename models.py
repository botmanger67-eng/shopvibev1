from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication and profile."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    cart_items = db.relationship('Cart', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        """Hash and store password."""
        if not password or len(password.strip()) == 0:
            raise ValueError("Password cannot be empty.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password against hash."""
        if not password:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f'<User {self.username}>'


class Product(db.Model):
    """Product model for catalog items."""

    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    image_url = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(100), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship: cart items and order items that reference this product
    cart_items = db.relationship('Cart', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def in_stock(self) -> bool:
        """Return True if stock > 0."""
        return self.stock > 0

    @property
    def formatted_price(self) -> str:
        """Return price as currency string."""
        return f"${self.price:.2f}"

    def reduce_stock(self, quantity: int) -> None:
        """Decrement stock by given quantity. Raises ValueError if insufficient stock."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if self.stock < quantity:
            raise ValueError(f"Insufficient stock for product '{self.name}'. Available: {self.stock}, requested: {quantity}.")
        self.stock -= quantity

    def increase_stock(self, quantity: int) -> None:
        """Increment stock by given quantity."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        self.stock += quantity

    def __repr__(self) -> str:
        return f'<Product {self.name}>'


class Cart(db.Model):
    """Cart model representing user's selected products and quantities."""

    __tablename__ = 'cart'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='unique_user_product_cart'),
    )

    @property
    def total_price(self) -> float:
        """Calculate total price for this cart item."""
        return self.product.price * self.quantity

    def __repr__(self) -> str:
        return f'<Cart user_id={self.user_id} product_id={self.product_id}>'


class Order(db.Model):
    """Order model representing completed purchases."""

    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), nullable=False, default='Pending')
    shipping_address = db.Column(db.String(500), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def item_count(self) -> int:
        """Return total quantity of items in this order."""
        return sum(item.quantity for item in self.items)

    @property
    def formatted_total(self) -> str:
        """Return total amount as currency string."""
        return f"${self.total_amount:.2f}"

    def calculate_total(self) -> float:
        """Recalculate total_amount from order items."""
        total = 0.0
        for item in self.items:
            total += item.subtotal
        self.total_amount = total
        return total

    def __repr__(self) -> str:
        return f'<Order {self.id} user={self.user_id} status={self.status}>'


class OrderItem(db.Model):
    """OrderItem model representing individual products within an order."""

    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)  # price at time of order

    @property
    def subtotal(self) -> float:
        """Calculate subtotal for this line item."""
        return self.price_at_purchase * self.quantity

    @property
    def formatted_subtotal(self) -> str:
        """Return subtotal as currency string."""
        return f"${self.subtotal:.2f}"

    def __repr__(self) -> str:
        return f'<OrderItem order_id={self.order_id} product_id={self.product_id}>'