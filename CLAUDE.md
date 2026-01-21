# CLAUDE.md - Tienda ALOHA AI Assistant Guide

This document provides comprehensive guidance for AI assistants working with the Tienda ALOHA codebase.

## Project Overview

**Tienda ALOHA** is a Flask-based e-commerce application for a toy store with multi-center (location) support, user balance systems, and an admin dashboard. The application supports discount programs per center and provides both customer and administrator interfaces.

**Language**: The codebase primarily uses Spanish for comments, variable names, and user-facing strings.

## Tech Stack

- **Backend**: Flask 3.0+, Python 3.11+
- **ORM**: SQLAlchemy with Flask-SQLAlchemy
- **Authentication**: Flask-Login with session-based auth
- **Database**: SQLite (development), PostgreSQL/MySQL (production)
- **Forms**: Flask-WTF with CSRF protection
- **Caching**: Redis (preferred) or SimpleCache fallback
- **Task Queue**: RQ (Redis Queue)
- **PDF Generation**: ReportLab
- **Security**: Bleach (sanitization), PyOTP (2FA)

## Directory Structure

```
/Tienda-ALOHA/
├── app/                    # Main Flask application package
│   ├── __init__.py        # App factory (create_app)
│   ├── models.py          # SQLAlchemy models
│   ├── config.py          # Configuration classes
│   ├── extensions.py      # Flask extensions (db, migrate, login_manager)
│   ├── forms.py           # WTForms definitions
│   ├── filters.py         # Jinja template filters
│   ├── security.py        # Security utilities
│   ├── errors.py          # Error handlers
│   └── utils/             # Utility modules
│       └── centers.py     # Center management utilities
│
├── blueprints/            # Flask blueprints
│   ├── auth.py           # Authentication (/auth)
│   ├── shop.py           # Shopping functionality (/)
│   ├── admin.py          # Admin dashboard (/admin)
│   └── user.py           # User profile (/user)
│
├── templates/             # Jinja2 HTML templates
│   ├── base.html         # Base layout
│   ├── index.html        # Product listing
│   ├── admin_dashboard.html
│   ├── admin/            # Admin-specific templates
│   └── errors/           # Error pages (404, 500)
│
├── static/               # Frontend assets
│   ├── css/             # Stylesheets (styles.css, mobile.css, themes.css)
│   ├── js/              # JavaScript files
│   └── images/          # Images and uploads
│
├── tests/                # Test suite
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── e2e/             # End-to-end tests
│
├── migrations/           # Database migration scripts
├── main.py              # Simple entry point
├── run.py               # Full entry point with advanced systems
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker configuration
└── Procfile             # Heroku deployment
```

## Key Models

### User
- `id`, `username` (unique), `email`, `password_hash`
- `is_admin`, `is_active`, `balance` (account credit)
- `center` (assigned location), `theme` (UI preference)
- `must_change_password` (force reset flag)

### Toy (Product)
- `id`, `name`, `description`, `price`
- `category`, `age_range`, `gender_category`
- `stock`, `image_url`, `is_active`
- Many-to-many with centers via `ToyCenterAvailability`

### Order
- `id`, `user_id`, `order_date`, `status`
- `subtotal_price`, `discount_percentage`, `discount_amount`
- `discounted_total`, `total_price`
- One-to-many with `OrderItem`

### Center
- `id`, `slug` (unique), `name`, `discount_percentage`

## Common Development Commands

### Running the Application

```bash
# Simple development server
python main.py

# Full server with advanced logging/caching
python run.py

# Production (Heroku)
gunicorn app:app
```

The app runs on `http://localhost:5000` by default.

### Database Operations

```bash
# Initialize/update database schema (uses Flask-Migrate)
flask db upgrade

# Create new migration after model changes
flask db migrate -m "Description of changes"

# Create tables directly (development)
python -c "from app import create_app; app = create_app(); app.app_context().push(); from app.extensions import db; db.create_all()"
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run unit tests only
python -m pytest tests/unit/

# Run specific test file
python -m pytest tests/unit/test_admin_add_toy_route.py

# Run with verbose output
python -m pytest -v tests/
```

## Blueprint Routes Reference

### Auth Blueprint (`/auth`)
- `POST /login` - User login
- `GET/POST /register` - User registration
- `GET /logout` - Session logout
- `GET/POST /force_password_change` - Mandatory password reset

### Shop Blueprint (`/`)
- `GET /` or `/index` - Product listing (paginated, 12/page)
- `GET /search` - Search/filter products
- `POST /add_to_cart` - Add item to cart
- `GET /cart` - View shopping cart
- `POST /remove_from_cart/<toy_id>` - Remove cart item
- `GET/POST /checkout` - Order checkout
- `GET /order/<order_id>` - Order summary
- `GET /order/<order_id>/pdf` - Download PDF receipt

### Admin Blueprint (`/admin`)
- `GET /dashboard` - Admin dashboard with stats
- `GET/POST /add_toy` - Create product
- `GET/POST /edit_toy/<toy_id>` - Edit product
- `POST /delete_toy/<toy_id>` - Delete product
- `GET /users` - List users
- `POST /toggle_admin/<user_id>` - Toggle admin status
- `GET/POST /centers` - Manage centers
- `GET /orders` - List all orders
- `GET /inventory` - Inventory dashboard

### User Blueprint (`/user`)
- `GET /profile` - User profile & order history
- `POST /add_balance` - Add account credit
- `POST /change_password` - Change password
- `POST /update_center` - Change assigned center

## Code Conventions

### Python Style
- Use descriptive Spanish names for user-facing strings
- Follow PEP 8 style guidelines
- Use type hints where beneficial
- Keep functions focused and small

### Database
- Always use `is_active` soft-delete pattern
- Include `created_at` and `updated_at` timestamps
- Use cascade delete for dependent relationships
- Query with `.filter_by(is_active=True)` for active records

### Security Best Practices
- All forms must include CSRF tokens (handled by Flask-WTF)
- Sanitize user input with `bleach.clean()`
- Use `werkzeug.security` for password hashing
- Validate file uploads (type, size)
- Never store plaintext passwords

### Templates
- Extend `base.html` for consistent layout
- Use `{{ format_currency(value) }}` for money display
- Include CSRF token in all forms: `{{ form.csrf_token }}`
- Use flash messages for user feedback

### Error Handling
- Use `try/except` for database operations
- Log security events via `log_security_event()`
- Return appropriate HTTP status codes
- Provide user-friendly error messages

## Session-Based Cart

The shopping cart is stored in the session:

```python
# Structure
session['cart'] = {
    'toy_id': {
        'quantity': int,
        'name': str,
        'price': float
    }
}

# Access cart count in templates via context processor
{{ cart_count }}
```

## Configuration

### Environment Variables
- `SECRET_KEY` - Session encryption (required in production)
- `DATABASE_URL` - Database connection string
- `REDIS_URL` - Redis connection for caching
- `FLASK_ENV` - 'development' or 'production'
- `PDF_LOGO_PATH` - Path to logo for PDF receipts

### Config Classes
- `Config` - Base configuration
- `DevelopmentConfig` - SQLite, debug enabled
- `ProductionConfig` - Secure cookies, HTTPS

## Testing Guidelines

### Unit Tests
- Test individual functions and methods
- Mock external dependencies
- Located in `tests/unit/`

### Integration Tests
- Test component interactions
- Use test database
- Located in `tests/integration/`

### E2E Tests
- Full user flow testing
- Test authentication, cart, checkout
- Located in `tests/e2e/`

### Test Fixtures
Use pytest fixtures for common setup:

```python
@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app

@pytest.fixture
def client(app):
    return app.test_client()
```

## Theme System

Users can select UI themes stored in the database:
- `aloha-light` (default)
- `aloha-dark`
- `cherry-blossom`
- `underwater`
- `halloween`
- `patriotic`

Applied via `data-theme` attribute on `<html>` element.

## Multi-Center System

- Each user is assigned to a `center`
- Centers have `discount_percentage` (0-100%)
- Toys can be available at multiple centers
- Users see products available at their center
- Admins see all products regardless of center

## Important Files to Know

| File | Purpose |
|------|---------|
| `app/__init__.py` | App factory, middleware, blueprint registration |
| `app/models.py` | All SQLAlchemy models |
| `app/config.py` | Configuration classes |
| `blueprints/shop.py` | Core shopping functionality |
| `blueprints/admin.py` | Admin dashboard routes |
| `templates/base.html` | Base template with navigation |
| `static/css/styles.css` | Main stylesheet |

## Common Pitfalls

1. **Cart Session**: Cart is session-based; clear on logout
2. **Center Filtering**: Remember to filter toys by user's center
3. **CSRF**: All POST forms need CSRF tokens
4. **Soft Delete**: Use `is_active=False`, don't delete records
5. **Price Calculations**: Store both original and discounted prices
6. **Database Migrations**: Run `flask db upgrade` after model changes

## Git Workflow

- Main branch: `main`
- Feature branches: `feature/description`
- Bug fixes: `fix/description`
- Always run tests before committing
- Use descriptive commit messages

## Deployment

### Docker
```bash
docker build -t tienda-aloha .
docker run -p 5000:5000 tienda-aloha
```

### Heroku
- Uses `Procfile`: `web: gunicorn app:app`
- Python version in `runtime.txt`: `python-3.9.18`

### Replit
- Configured via `.replit` file
- Ports: 5000 (local) → 80 (external)

## Quick Reference

```python
# Import app factory
from app import create_app

# Import models
from app.models import User, Toy, Order, Center

# Import extensions
from app.extensions import db, login_manager

# Format currency in templates
{{ format_currency(price) }}  # Returns "A$ 10.00"

# Check admin status
@login_required
def admin_route():
    if not current_user.is_admin:
        abort(403)
```
