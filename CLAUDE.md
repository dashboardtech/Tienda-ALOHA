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
- **Caching**: Redis (preferred) or SimpleCache fallback with custom ToyCache/CartCache
- **Task Queue**: RQ (Redis Queue)
- **PDF Generation**: ReportLab with custom fonts (Futura)
- **Security**: Bleach (sanitization), PyOTP (2FA), rate limiting
- **Backup**: Custom backup system with full/incremental support

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
│   ├── security.py        # Security utilities & log_security_event()
│   ├── errors.py          # Error handlers
│   └── utils/             # Utility modules
│       ├── centers.py     # Center management utilities
│       ├── rate_limiter.py # Rate limiting decorators
│       └── backup_system_simple.py # Backup management
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
│   ├── admin_backup.html # Backup management
│   ├── admin_edit_user.html # User editing
│   ├── admin_view_user.html # User detail view
│   ├── inventory_dashboard.html # Inventory analytics
│   ├── bulk_upload_toys.html # CSV bulk upload
│   ├── bulk_upload_preview.html # Upload preview
│   ├── balance.html      # Balance management
│   ├── add_balance.html  # Add balance form
│   ├── transfer.html     # Transfer interface
│   ├── transaction_details.html # Transaction history
│   ├── advanced_search.html # Advanced search
│   ├── pagination.html   # Pagination component
│   ├── admin/            # Admin-specific templates
│   │   └── inventory.html # Toy management
│   └── errors/           # Error pages (404, 500)
│
├── static/               # Frontend assets
│   ├── css/             # Stylesheets (styles.css, mobile.css, themes.css)
│   ├── js/              # JavaScript files
│   │   ├── main.js      # Main application JS
│   │   ├── admin.js     # Admin-specific JS
│   │   ├── mobile.js    # Mobile-specific JS
│   │   └── mobile_optimized.js # Optimized mobile
│   └── images/          # Images and uploads
│       └── toys/        # Product images (timestamped filenames)
│
├── tests/                # Test suite
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   ├── e2e/             # End-to-end tests
│   └── fixtures/        # Test fixtures
│
├── tools/               # Utility scripts and testing tools
│   └── normalize_ascii.py # ASCII normalization
│
├── orders/              # Order text files (order_1.txt, etc.)
├── migrations/          # Database migration scripts
├── main.py              # Simple entry point
├── run.py               # Full entry point with advanced systems
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker configuration
└── Procfile             # Heroku deployment
```

## Root-Level Utility Scripts

| Script | Purpose |
|--------|---------|
| `setup.py`, `init_all.py`, `init_database.py`, `init_db.py` | Database initialization |
| `create_db_tables.py`, `create_tables.py`, `create_tables_manually.py` | Table creation |
| `reset_db.py`, `fix_db.py`, `ensure_db.py`, `new_db.py` | Database maintenance |
| `advanced_search.py` | AdvancedSearchEngine implementation |
| `cache_system.py` | ToyCache and CartCache classes |
| `inventory_system.py` | InventoryManager with reports/alerts |
| `add_toys.py`, `insert_test_data.py`, `update_toys.py` | Data seeding |
| `db_diag.py`, `apply_migration.py` | Database diagnostics |
| `utils.py` | normalize_email, format_currency, order utilities |
| `pagination_helpers.py` | Pagination support |
| `email_validator.py` | Email validation |
| `promote_admin.py` | Admin promotion utility |
| `optimization_report.py`, `optimized_queries.py` | Performance analysis |

## Key Models

### User
- `id`, `username` (unique), `email`, `password_hash`
- `is_admin`, `is_active`, `balance` (account credit)
- `center` (assigned location), `theme` (UI preference)
- `must_change_password` (force reset flag)
- `profile_pic` (profile picture URL)
- `last_login` (timestamp of last login)

### Toy (Product)
- `id`, `name`, `description`, `price`
- `category`, `age_range`, `gender_category`
- `stock`, `image_url`, `is_active`
- `deleted_at` (soft delete timestamp)
- Many-to-many with centers via `ToyCenterAvailability`

### Order
- `id`, `user_id`, `order_date`, `status`
- `subtotal_price`, `discount_percentage`, `discount_amount`
- `discounted_total`, `total_price`
- `discount_center` (center that provided discount)
- `deleted_at` (soft delete timestamp)
- One-to-many with `OrderItem`

### Center
- `id`, `slug` (unique), `name`, `discount_percentage`

## Advanced Systems

### Cache System (`cache_system.py`)
- `ToyCache` - Caches product data with TTL-based expiration
- `CartCache` - Caches shopping cart data with Redis fallback
- Automatic cache invalidation on updates

### Inventory System (`inventory_system.py`)
- `InventoryManager` class for stock management
- Generates inventory reports with low-stock alerts
- Predictive analytics for stock needs
- Summary data and metrics

### Advanced Search (`advanced_search.py`)
- `AdvancedSearchEngine` with multi-filter support
- Filters: category, age_range, gender, price range, stock, sales
- Autocomplete suggestions API endpoint
- JSON responses for AJAX requests

### Backup System (`utils/backup_system_simple.py`)
- Create full/incremental backups
- Download and restore backups
- Automatic backup file management
- Admin dashboard for backup operations

### Rate Limiting (`utils/rate_limiter.py`)
- Decorators: `moderate_rate_limit`, `strict_rate_limit`, `relaxed_rate_limit`
- Applied to sensitive routes (add_toy, delete_toy, etc.)
- Configurable limits per endpoint

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

# Reset database
python reset_db.py

# Run database diagnostics
python db_diag.py
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
- `GET /search/suggestions` - API for search autocomplete
- `POST /add_to_cart` - Add item to cart
- `GET /cart` - View shopping cart
- `POST /update_cart/<int:toy_id>` - Update cart item quantity
- `POST /remove_from_cart/<toy_id>` - Remove cart item
- `GET/POST /checkout` - Order checkout
- `GET /order/<order_id>` - Order summary
- `GET /order/<order_id>/pdf` - Download PDF receipt

### Admin Blueprint (`/admin`)

**Dashboard & Stats:**
- `GET /dashboard` - Admin dashboard with stats

**Toy Management:**
- `GET/POST /add_toy` - Create product
- `GET/POST /edit_toy/<toy_id>` - Edit product
- `POST /toy_edit_new/<int:toy_id>` - Alternative edit route
- `POST /delete_toy/<toy_id>` - Delete product
- `GET /toys` - Dedicated toy management page
- `POST /toys/<int:toy_id>/centers` - Manage toy center availability
- `POST /bulk_upload_toys` - Bulk upload toys from CSV
- `POST /bulk_upload_preview` - Preview bulk upload

**Inventory:**
- `GET /inventory` - Inventory dashboard with reports
- `GET /inventory/alerts` - API for inventory alerts
- `POST /inventory/send-alerts` - Send alert notifications
- `GET /export_inventory` - Export inventory as CSV

**User Management:**
- `GET /users` - List users
- `GET /add_user` - Add user form
- `POST /add_user` - Create new user
- `GET/POST /edit_user/<int:user_id>` - Edit user details
- `GET /view_user/<int:user_id>` - View user profile
- `POST /toggle_admin/<user_id>` - Toggle admin status
- `POST /toggle_user/<int:user_id>` - Toggle user active status
- `POST /delete_user/<int:user_id>` - Delete user
- `POST /users/<int:user_id>/balance` - Update user balance (JSON API)
- `POST /adjust_balance/<int:user_id>` - Adjust balance with reason

**Order Management:**
- `GET /orders` - List all orders
- `POST /orders/<int:order_id>/delete` - Cancel order with refund
- `GET /orders/<int:order_id>/receipt` - Download receipt as text
- `GET /export_orders` - Export orders as CSV

**Center Management:**
- `GET/POST /centers` - Manage centers with metrics

**Backup Management:**
- `GET /backup` - Backup management dashboard
- `POST /backup/create` - Create new backup
- `GET /backup/download/<filename>` - Download backup file
- `POST /backup/delete/<filename>` - Delete backup file

### User Blueprint (`/user`)
- `GET /profile` - User profile & order history
- `POST /add_balance` - Add account credit
- `POST /change_password` - Change password
- `POST /update_center` - Change assigned center
- `POST /update_theme` - Save preferred theme

## Configuration

### Environment Variables
- `SECRET_KEY` - Session encryption (required in production)
- `DATABASE_URL` - Database connection string
- `REDIS_URL` - Redis connection for caching
- `FLASK_ENV` - 'development' or 'production'
- `PDF_LOGO_PATH` - Path to logo for PDF receipts
- `CSRF_SECRET_KEY` - Separate CSRF key

### Config Classes
- `Config` - Base configuration
- `DevelopmentConfig` - SQLite, debug enabled
- `ProductionConfig` - Secure cookies, HTTPS

### Security Settings
```python
SECURITY_HEADERS = {...}           # CSP and security headers
MAX_LOGIN_ATTEMPTS = 5             # Account lockout threshold
ACCOUNT_LOCKOUT_DURATION = 30      # Minutes to lock account
ADMIN_2FA_REQUIRED = True          # Enforce 2FA for admins
ADMIN_2FA_ISSUER = "TiendaALOHA"   # 2FA issuer name
```

### Password Policy
```python
PASSWORD_MIN_LENGTH = 8            # Minimum characters
PASSWORD_REQUIRE_UPPER = True      # Uppercase required
PASSWORD_REQUIRE_LOWER = True      # Lowercase required
PASSWORD_REQUIRE_NUMBERS = True    # Numbers required
```

### Age Verification
```python
MIN_AGE = 8                        # Minimum age
MAX_AGE = 18                       # Maximum age
REQUIRE_PARENTAL_CONSENT = True    # Parental consent flag
```

### Transaction Limits
```python
MAX_DAILY_TRANSACTION_AMOUNT = 50.0   # A$ per day
MAX_SINGLE_TRANSACTION_AMOUNT = 20.0  # A$ per transaction
MAX_DAILY_TRANSACTIONS = 10           # Max transactions/day
```

### Rate Limiting
```python
RATELIMIT_DEFAULT = "100/hour"     # Global rate limit
RATELIMIT_LOGIN = "5/minute"       # Login attempt limit
RATELIMIT_STORAGE_URL = "..."      # Rate limit storage backend
WTF_CSRF_TIME_LIMIT = 3600         # CSRF token expiry (seconds)
```

## Code Conventions

### Python Style
- Use descriptive Spanish names for user-facing strings
- Follow PEP 8 style guidelines
- Use type hints where beneficial
- Keep functions focused and small

### Database
- Always use `is_active` soft-delete pattern with `deleted_at` timestamp
- Include `created_at` and `updated_at` timestamps
- Use cascade delete for dependent relationships
- Query with `.filter_by(is_active=True)` for active records

### Security Best Practices
- All forms must include CSRF tokens (handled by Flask-WTF)
- Sanitize user input with `bleach.clean()`
- Use `werkzeug.security` for password hashing
- Validate file uploads (type, size)
- Never store plaintext passwords
- Log security events via `log_security_event()`
- Password strength validation: uppercase, lowercase, digits, min 8 chars
- Email normalization via `normalize_email()` in `utils.py`

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

The shopping cart is stored in the session with Redis-based CartCache fallback:

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
Theme selection saved via `POST /user/update_theme` API endpoint.

## Multi-Center System

- Each user is assigned to a `center`
- Centers have `discount_percentage` (0-100%)
- Toys can be available at multiple centers
- Users see products available at their center
- Admins see all products regardless of center
- Orders track `discount_center` for audit purposes

## Important Files to Know

| File | Purpose |
|------|---------|
| `app/__init__.py` | App factory, middleware, blueprint registration |
| `app/models.py` | All SQLAlchemy models |
| `app/config.py` | Configuration classes |
| `app/security.py` | Security utilities, log_security_event() |
| `blueprints/shop.py` | Core shopping functionality |
| `blueprints/admin.py` | Admin dashboard routes |
| `templates/base.html` | Base template with navigation |
| `static/css/styles.css` | Main stylesheet |
| `cache_system.py` | ToyCache and CartCache |
| `inventory_system.py` | InventoryManager |
| `advanced_search.py` | AdvancedSearchEngine |
| `utils.py` | normalize_email, format_currency, order utilities |

## Key Features

### CSV Export
- Orders exportable as CSV from admin dashboard (`/admin/export_orders`)
- Inventory exportable as CSV (`/admin/export_inventory`)

### Order Management
- Admin can cancel orders with automatic inventory restoration
- User balance refunded on cancellation
- Text-based receipt download for orders

### User Management
- Bulk user actions (activate, deactivate, delete)
- User balance adjustment with audit reasons
- User creation and editing by admins
- Profile picture support

### Backup System
- Create full/incremental backups
- Download and restore backups
- Automatic backup file management
- Admin dashboard at `/admin/backup`

### Balance/Transaction System
- Add balance functionality
- Adjust balance with reasons (transaction log)
- Transaction limits enforced (daily, per-transaction)

## Common Pitfalls

1. **Cart Session**: Cart is session-based; clear on logout (CartCache fallback available)
2. **Center Filtering**: Remember to filter toys by user's center
3. **CSRF**: All POST forms need CSRF tokens
4. **Soft Delete**: Use `is_active=False` and `deleted_at`, don't delete records
5. **Price Calculations**: Store both original and discounted prices
6. **Database Migrations**: Run `flask db upgrade` after model changes
7. **Rate Limiting**: Sensitive routes have rate limits applied
8. **Password Validation**: Enforce uppercase, lowercase, digits, min 8 chars
9. **Transaction Limits**: Respect daily and per-transaction amount limits
10. **Static Files**: Product images stored in `/static/images/toys/` with timestamps

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
- Ports: 5000 (local) -> 80 (external)

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

# Log security event
from app.security import log_security_event
log_security_event('event_type', user_id, details)

# Normalize email
from utils import normalize_email
email = normalize_email(user_input)
```
