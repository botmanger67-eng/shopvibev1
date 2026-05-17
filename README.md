# shopvibe

A production-ready e-commerce Flask application with SQLite, user authentication, product catalog, shopping cart, checkout, order history, and admin panel.

## Features

- **User Authentication** – Register, login, and session management with Flask-Login
- **Product Catalog** – Browse, view detail, and search products
- **Shopping Cart** – Add, remove, and update items in the cart
- **Checkout** – Place orders with order summary
- **Order History** – View past orders for logged-in users
- **Admin Panel** – Manage products, view dashboard, and edit product details
- **Responsive Design** – Built with HTML, CSS, and JavaScript

## Tech Stack

- **Backend**: Python, Flask, SQLAlchemy
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript

## Installation

Follow these steps to set up the project locally.

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/shopvibe.git
   cd shopvibe
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set environment variables**
   - `SECRET_KEY` – A secret key for Flask sessions (required).  
     Example (Linux/macOS):
     ```bash
     export SECRET_KEY="your-secret-key-here"
     ```
     On Windows (cmd):
     ```bash
     set SECRET_KEY="your-secret-key-here"
     ```

6. **Initialize the database**
   The app uses SQLite. On first run, the database will be created automatically.  
   Optionally, you can seed the database with sample data:
   ```bash
   python app.py seed
   ```
   *(If a seed command exists; otherwise the app will create tables on first request.)*

7. **Run the application**
   ```bash
   python app.py
   ```

   The app will be available at `http://127.0.0.1:5000`.

## Usage

### Running the Application
Start the Flask development server:
```bash
python app.py
```

### Accessing Routes
- **Home Page**: `http://127.0.0.1:5000/`
- **Shop**: `http://127.0.0.1:5000/shop`
- **Product Detail**: `http://127.0.0.1:5000/product/1` (replace ID)
- **Login**: `http://127.0.0.1:5000/login`
- **Register**: `http://127.0.0.1:5000/register`
- **Cart**: `http://127.0.0.1:5000/cart`
- **Checkout**: `http://127.0.0.1:5000/checkout`
- **Order History**: `http://127.0.0.1:5000/orders`
- **Admin Dashboard**: `http://127.0.0.1:5000/admin/dashboard`
- **Admin Products**: `http://127.0.0.1:5000/admin/products`
- **Admin Edit Product**: `http://127.0.0.1:5000/admin/edit_product/1` (replace ID)

### Example: Registering a New User
1. Navigate to `/register`.
2. Fill in the registration form (username, email, password).
3. Submit – you will be redirected to the login page or logged in automatically depending on implementation.

### Example: Adding a Product to Cart
1. Browse to `/shop` or a product detail page.
2. Click “Add to Cart” – item is stored in the session/cart.
3. View cart at `/cart` and proceed to checkout.

### Admin Access
The admin panel is accessible at `/admin/dashboard`.  
*Note: Admin credentials must be created manually or via a seed script. By default, the first registered user may be assigned admin role (implementation-dependent).*

## Project Structure

```
├── app.py
├── models.py
├── requirements.txt
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── shop.html
│   ├── product_detail.html
│   ├── login.html
│   ├── register.html
│   ├── cart.html
│   ├── checkout.html
│   ├── orders.html
│   └── admin/
│       ├── dashboard.html
│       ├── products.html
│       └── edit_product.html
```

## API Endpoints

This application does not expose a separate REST API. All functionality is server-rendered via Flask routes. The following is a list of available routes (HTTP methods inferred from functionality):

| Route                          | Method(s) | Description                          |
|--------------------------------|-----------|--------------------------------------|
| `/`                            | GET       | Home page                            |
| `/shop`                        | GET       | Product listing                      |
| `/product/<int:product_id>`    | GET       | Product detail page                  |
| `/login`                       | GET, POST | User login                           |
| `/register`                    | GET, POST | User registration                    |
| `/cart`                        | GET, POST | View cart (GET) / update cart (POST) |
| `/checkout`                    | GET, POST | Checkout page                        |
| `/orders`                      | GET       | Order history for logged-in user     |
| `/admin/dashboard`             | GET       | Admin dashboard                      |
| `/admin/products`              | GET       | Admin product management             |
| `/admin/edit_product/<int:id>` | GET, POST | Edit a specific product              |

*Additional routes for add/remove cart or order actions may exist; refer to `app.py` for the full list.*

## Environment Variables

| Variable     | Required | Description                                               |
|--------------|----------|-----------------------------------------------------------|
| `SECRET_KEY` | Yes      | A random string used for session encryption and CSRF protection. |

*Optional: If you change the database path, you can set `DATABASE_URL` (e.g., `sqlite:///yourdb.db`) but the app defaults to SQLite in the project root.*

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Make your changes and commit them (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a Pull Request.

Please ensure your code follows the existing style and all tests pass.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.