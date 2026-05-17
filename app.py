import os
import uuid
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, Union

from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

from models import db, User, Product, Order, OrderItem, CartItem

# ----------------------------------------------------------------------
# Application Factory
# ----------------------------------------------------------------------

def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Default config
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", os.urandom(24).hex()),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///ecommerce.db"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config is not None:
        app.config.update(test_config)

    # Initialize extensions
    db.init_app(app)

    with app.app_context():
        db.create_all()
        # Create admin user if not exists
        if not User.query.filter_by(username="admin").first():
            admin = User(
                username="admin",
                email="admin@example.com",
                password=generate_password_hash("admin123"),
                is_admin=True,
            )
            db.session.add(admin)
            db.session.commit()

    # ------------------------------------------------------------------
    # Helper Functions
    # ------------------------------------------------------------------

    def get_cart_from_session() -> List[Dict[str, Any]]:
        """Retrieve the cart from the Flask session."""
        return session.get("cart", [])

    def save_cart_to_session(cart: List[Dict[str, Any]]) -> None:
        """Save the cart to the Flask session."""
        session["cart"] = cart

    def get_product_or_404(product_id: int) -> Product:
        """Fetch a product by ID or return 404."""
        product = Product.query.get(product_id)
        if product is None:
            abort(404, description="Product not found")
        return product

    def login_required(f: Any) -> Any:
        """Decorator to require user login."""
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            if "user_id" not in session:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("login"))
            # Attach user object to g
            g.user = User.query.get(session["user_id"])
            if g.user is None:
                session.pop("user_id", None)
                flash("User not found. Please log in again.", "danger")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return decorated_function

    def admin_required(f: Any) -> Any:
        """Decorator to require admin privileges."""
        @wraps(f)
        @login_required
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            if not g.user.is_admin:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function

    def calculate_cart_total(cart: List[Dict[str, Any]]) -> float:
        """Calculate the total price of items in the cart."""
        total = 0.0
        for item in cart:
            product = Product.query.get(item["product_id"])
            if product:
                total += product.price * item["quantity"]
        return round(total, 2)

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @app.route("/")
    def index() -> str:
        """Render the homepage."""
        featured_products = Product.query.filter_by(is_featured=True).limit(6).all()
        return render_template("index.html", featured_products=featured_products)

    @app.route("/shop")
    def shop() -> str:
        """Display the product catalog."""
        page = request.args.get("page", 1, type=int)
        per_page = 12
        category = request.args.get("category")
        search = request.args.get("search")

        query = Product.query
        if category:
            query = query.filter_by(category=category)
        if search:
            query = query.filter(Product.name.ilike(f"%{search}%"))

        pagination = query.order_by(Product.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        products = pagination.items
        categories = [c[0] for c in Product.query.with_entities(Product.category).distinct()]

        return render_template(
            "shop.html",
            products=products,
            pagination=pagination,
            categories=categories,
        )

    @app.route("/product/<int:product_id>")
    def product_detail(product_id: int) -> str:
        """Show a single product's details."""
        product = get_product_or_404(product_id)
        return render_template("product_detail.html", product=product)

    @app.route("/register", methods=["GET", "POST"])
    def register() -> Union[str, "Response"]:
        """Handle user registration."""
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            # Validation
            errors = []
            if not username or len(username) < 3:
                errors.append("Username must be at least 3 characters.")
            if not email or "@" not in email:
                errors.append("Please provide a valid email address.")
            if not password or len(password) < 6:
                errors.append("Password must be at least 6 characters.")
            if password != confirm_password:
                errors.append("Passwords do not match.")
            if User.query.filter_by(username=username).first():
                errors.append("Username already taken.")
            if User.query.filter_by(email=email).first():
                errors.append("Email already registered.")

            if errors:
                for err in errors:
                    flash(err, "danger")
                return render_template("register.html")

            # Create user
            user = User(
                username=username,
                email=email,
                password=generate_password_hash(password),
            )
            try:
                db.session.add(user)
                db.session.commit()
                flash("Registration successful! Please login.", "success")
                return redirect(url_for("login"))
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred: {str(e)}", "danger")
                return render_template("register.html")

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login() -> Union[str, "Response"]:
        """Handle user login."""
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = User.query.filter_by(username=username).first()

            if user and check_password_hash(user.password, password):
                session["user_id"] = user.id
                session.permanent = True
                flash("Login successful!", "success")
                next_page = request.args.get("next")
                return redirect(next_page or url_for("index"))
            else:
                flash("Invalid username or password.", "danger")
                return render_template("login.html")

        return render_template("login.html")

    @app.route("/logout")
    def logout() -> "Response":
        """Log out the current user."""
        session.pop("user_id", None)
        flash("You have been logged out.", "info")
        return redirect(url_for("index"))

    @app.route("/cart")
    def cart() -> str:
        """View the shopping cart."""
        cart_data = get_cart_from_session()
        cart_items = []
        total = 0.0

        for item in cart_data:
            product = Product.query.get(item["product_id"])
            if product:
                subtotal = product.price * item["quantity"]
                total += subtotal
                cart_items.append({
                    "product": product,
                    "quantity": item["quantity"],
                    "subtotal": subtotal,
                })

        total = round(total, 2)
        return render_template("cart.html", cart_items=cart_items, total=total)

    @app.route("/cart/add", methods=["POST"])
    def add_to_cart() -> Union["Response", Tuple[str, int]]:
        """Add an item to the cart."""
        product_id = request.form.get("product_id", type=int)
        quantity = request.form.get("quantity", 1, type=int)

        if not product_id:
            abort(400, "Product ID required")

        product = Product.query.get(product_id)
        if not product:
            abort(404, "Product not found")

        quantity = max(1, min(quantity, 10))  # Limit quantity between 1 and 10

        cart = get_cart_from_session()
        for item in cart:
            if item["product_id"] == product_id:
                item["quantity"] += quantity
                if item["quantity"] > 10:
                    item["quantity"] = 10
                save_cart_to_session(cart)
                flash(f"Updated {product.name} quantity in cart.", "info")
                return redirect(url_for("cart"))

        cart.append({"product_id": product_id, "quantity": quantity})
        save_cart_to_session(cart)
        flash(f"Added {product.name} to cart.", "success")
        return redirect(url_for("cart"))

    @app.route("/cart/update", methods=["POST"])
    def update_cart() -> Union["Response", Tuple[str, int]]:
        """Update cart item quantities."""
        product_id = request.form.get("product_id", type=int)
        quantity = request.form.get("quantity", 1, type=int)

        if not product_id:
            abort(400, "Product ID required")

        quantity = max(1, min(quantity, 10))

        cart = get_cart_from_session()
        for item in cart:
            if item["product_id"] == product_id:
                item["quantity"] = quantity
                break
        save_cart_to_session(cart)
        flash("Cart updated.", "info")
        return redirect(url_for("cart"))

    @app.route("/cart/remove/<int:product_id>", methods=["POST"])
    def remove_from_cart(product_id: int) -> "Response":
        """Remove an item from the cart."""
        cart = get_cart_from_session()
        cart = [item for item in cart if item["product_id"] != product_id]
        save_cart_to_session(cart)
        flash("Item removed from cart.", "info")
        return redirect(url_for("cart"))

    @app.route("/checkout", methods=["GET", "POST"])
    @login_required
    def checkout() -> Union[str, "Response"]:
        """Handle the checkout process."""
        cart_data = get_cart_from_session()
        if not cart_data:
            flash("Your cart is empty.", "warning")
            return redirect(url_for("cart"))

        total = calculate_cart_total(cart_data)

        if request.method == "POST":
            # Process payment (simplified)
            # In a real app, integrate with Stripe/PayPal etc.
            # For now, just create order.

            # Validate shipping info (example)
            shipping_address = request.form.get("shipping_address", "").strip()
            if not shipping_address:
                flash("Shipping address is required.", "danger")
                return render_template("checkout.html", total=total)

            # Create order
            order = Order(
                user_id=g.user.id,
                total_amount=total,
                shipping_address=shipping_address,
                status="pending",
                created_at=datetime.utcnow()
            )

            try:
                db.session.add(order)
                db.session.flush()  # Get order id

                # Create order items
                for item in cart_data:
                    product = Product.query.get(item["product_id"])
                    if product:
                        order_item = OrderItem(
                            order_id=order.id,
                            product_id=product.id,
                            quantity=item["quantity"],
                            price=product.price,
                        )
                        db.session.add(order_item)

                db.session.commit()
                # Clear cart
                save_cart_to_session([])
                flash("Order placed successfully!", "success")
                return redirect(url_for("orders"))
            except Exception as e:
                db.session.rollback()
                flash(f"Checkout failed: {str(e)}", "danger")
                return render_template("checkout.html", total=total)

        return render_template("checkout.html", total=total)

    @app.route("/orders")
    @login_required
    def orders() -> str:
        """View user's order history."""
        user_orders = (
            Order.query.filter_by(user_id=g.user.id)
            .order_by(Order.created_at.desc())
            .all()
        )
        return render_template("orders.html", orders=user_orders)

    # ------------------------------------------------------------------
    # Admin Routes
    # ------------------------------------------------------------------

    @app.route("/admin")
    @admin_required
    def admin_dashboard() -> str:
        """Admin dashboard."""
        total_users = User.query.count()
        total_products = Product.query.count()
        total_orders = Order.query.count()
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        return render_template(
            "admin/dashboard.html",
            total_users=total_users,
            total_products=total_products,
            total_orders=total_orders,
            recent_orders=recent_orders,
        )

    @app.route("/admin/products")
    @admin_required
    def admin_products() -> str:
        """List all products for admin."""
        page = request.args.get("page", 1, type=int)
        per_page = 20
        pagination = Product.query.order_by(Product.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        products = pagination.items
        return render_template(
            "admin/products.html", products=products, pagination=pagination
        )

    @app.route("/admin/products/add", methods=["GET", "POST"])
    @admin_required
    def admin_add_product() -> Union[str, "Response"]:
        """Add a new product."""
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            description = request.form.get("description", "").strip()
            price = request.form.get("price", type=float)
            category = request.form.get("category", "").strip()
            image_url = request.form.get("image_url", "").strip()
            stock = request.form.get("stock", 0, type=int)
            is_featured = request.form.get("is_featured") == "on"

            errors = []
            if not name:
                errors.append("Product name is required.")
            if price is None or price <= 0:
                errors.append("Valid price is required.")
            if not category:
                errors.append("Category is required.")

            if errors:
                for err in errors:
                    flash(err, "danger")
                return render_template("admin/edit_product.html", product=None)

            product = Product(
                name=name,
                description=description,
                price=price,
                category=category,
                image_url=image_url,
                stock=stock,
                is_featured=is_featured,
                created_at=datetime.utcnow(),
            )
            try:
                db.session.add(product)
                db.session.commit()
                flash("Product added successfully.", "success")
                return redirect(url_for("admin_products"))
            except Exception as e:
                db.session.rollback()
                flash(f"Error adding product: {str(e)}", "danger")
                return render_template("admin/edit_product.html", product=None)

        return render_template("admin/edit_product.html", product=None)

    @app.route("/admin/products/edit/<int:product_id>", methods=["GET", "POST"])
    @admin_required
    def admin_edit_product(product_id: int) -> Union[str, "Response"]:
        """Edit an existing product."""
        product = get_product_or_404(product_id)

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            description = request.form.get("description", "").strip()
            price = request.form.get("price", type=float)
            category = request.form.get("category", "").strip()
            image_url = request.form.get("image_url", "").strip()
            stock = request.form.get("stock", 0, type=int)
            is_featured = request.form.get("is_featured") == "on"

            errors = []
            if not name:
                errors.append("Product name is required.")
            if price is None or price <= 0:
                errors.append("Valid price is required.")

            if errors:
                for err in errors:
                    flash(err, "danger")
                return render_template("admin/edit_product.html", product=product)

            try:
                product.name = name
                product.description = description
                product.price = price
                product.category = category
                product.image_url = image_url
                product.stock = stock
                product