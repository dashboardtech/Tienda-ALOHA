# Tienda ALOHA - Sugerencias de Mejora

Este documento contiene un análisis profundo del código y recomendaciones de mejora organizadas por prioridad.

---

## Resumen Ejecutivo

| Categoría | Estado | Problemas Críticos |
|-----------|--------|-------------------|
| Seguridad | ⚠️ | 2FA roto, print statements, rate limiting débil |
| Arquitectura | ❌ | Blueprints gigantes, sin capa de servicios |
| Rendimiento | ⚠️ | N+1 queries, índices faltantes, sin paginación |
| Testing | ❌ | 1.6/10 cobertura, sin CI/CD |
| Código | ⚠️ | 50+ duplicaciones, funciones complejas |

---

## 1. SEGURIDAD - CRÍTICO

### 1.1 Bug en 2FA (CRÍTICO)

**Archivo**: `app/security.py:83`

```python
# ACTUAL (ROTO):
if current_app.config['ADMIN_2FA_REQUIRED'] and not verify_2fa():
    # verify_2fa() requiere 2 parámetros pero se llama sin ninguno

# CORRECCIÓN:
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        if current_app.config.get('ADMIN_2FA_REQUIRED'):
            token = request.form.get('totp_token') or request.headers.get('X-TOTP-Token')
            if not token or not verify_2fa(token, current_user.totp_secret):
                abort(403)
        return f(*args, **kwargs)
    return decorated_function
```

### 1.2 Print Statements Exponen Información Sensible (CRÍTICO)

**Archivos afectados**: `blueprints/auth.py`, `blueprints/shop.py`, `blueprints/admin.py`

```python
# ELIMINAR estos prints:
print(f"Intentando login con usuario: {form.username.data}")  # auth.py:57
print(f"Usuario encontrado: {user.username}")                  # auth.py:61
print(f"Usuario actual: {current_user.id} (Admin: {current_user.is_admin})")  # shop.py:918

# REEMPLAZAR con logging estructurado:
import logging
logger = logging.getLogger(__name__)
logger.info("Login attempt", extra={'username': form.username.data})
```

### 1.3 Rate Limiting Basado en Sesión (ALTO)

**Archivo**: `app/security.py:98-108`

```python
# ACTUAL (VULNERABLE - puede modificarse por cliente):
attempts = session.get(key, [])

# CORRECCIÓN - usar Redis o base de datos:
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@limiter.limit("5 per minute")
def login():
    ...
```

### 1.4 CSP Demasiado Permisivo (MEDIO)

**Archivo**: `app/__init__.py:179-183`

```python
# ACTUAL:
"default-src 'self' 'unsafe-inline' 'unsafe-eval'"

# CORRECCIÓN (remover unsafe-inline y unsafe-eval gradualmente):
"default-src 'self'; script-src 'self' 'nonce-{nonce}'; style-src 'self' 'nonce-{nonce}'"
```

### 1.5 Validación de Contraseñas Inconsistente (MEDIO)

**Archivos**: `blueprints/user.py:69-88`, `blueprints/admin.py`

```python
# AGREGAR validación en change_password:
from app.security import validate_password_strength

@user_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    new_password = request.form.get('new_password')

    # AGREGAR esta validación:
    is_valid, message = validate_password_strength(new_password)
    if not is_valid:
        flash(message, 'error')
        return redirect(url_for('user.profile'))

    current_user.set_password(new_password)
```

### 1.6 Validación de Archivos Incompleta (MEDIO)

**Archivo**: `blueprints/admin.py:749`

```python
# AGREGAR validación de contenido:
import imghdr

def validate_image(file):
    header = file.read(512)
    file.seek(0)
    format = imghdr.what(None, header)
    if format not in ['png', 'jpeg', 'gif']:
        return False
    return True

# Usar antes de guardar:
if not validate_image(image_file):
    flash('Archivo de imagen inválido', 'error')
    return redirect(...)
```

---

## 2. ARQUITECTURA - CRÍTICO

### 2.1 Blueprints Demasiado Grandes

| Blueprint | Líneas | Rutas | Estado |
|-----------|--------|-------|--------|
| admin.py | 1,929 | 33 | ❌ Dividir urgente |
| shop.py | 1,029 | 20+ | ❌ Dividir urgente |
| user.py | 135 | 5 | ✅ OK |
| auth.py | 177 | 3 | ✅ OK |

**Solución - Crear nuevos blueprints**:

```
blueprints/
├── auth.py          # Autenticación (actual)
├── shop.py          # Solo catálogo y búsqueda
├── cart.py          # NUEVO: Carrito y checkout
├── orders.py        # NUEVO: Gestión de órdenes
├── user.py          # Perfil de usuario (actual)
├── admin/
│   ├── __init__.py
│   ├── dashboard.py # NUEVO: Dashboard y estadísticas
│   ├── products.py  # NUEVO: CRUD de productos
│   ├── users.py     # NUEVO: Gestión de usuarios
│   ├── centers.py   # NUEVO: Gestión de centros
│   └── inventory.py # NUEVO: Inventario y reportes
```

### 2.2 Crear Capa de Servicios

```python
# CREAR: app/services/__init__.py

# app/services/order_service.py
class OrderService:
    def __init__(self, db_session):
        self.db = db_session

    def create_order(self, user, cart_items, center_slug):
        """Crea una orden con validación y cálculo de descuentos"""
        center = Center.query.filter_by(slug=center_slug).first()

        # Validar stock
        for item in cart_items:
            toy = Toy.query.get(item['toy_id'])
            if toy.stock < item['quantity']:
                raise InsufficientStockError(toy.name)

        # Calcular totales
        subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
        discount = subtotal * (center.discount_percentage / 100)

        # Crear orden
        order = Order(
            user_id=user.id,
            subtotal_price=subtotal,
            discount_percentage=center.discount_percentage,
            discount_amount=discount,
            total_price=subtotal - discount
        )

        self.db.add(order)
        return order

# app/services/cart_service.py
class CartService:
    def add_item(self, session, toy_id, quantity):
        """Agrega item al carrito con validación"""
        toy = Toy.query.get_or_404(toy_id)
        if not toy.is_active or toy.stock < quantity:
            raise InvalidCartOperationError()

        cart = session.get('cart', {})
        cart[str(toy_id)] = {
            'quantity': quantity,
            'name': toy.name,
            'price': float(toy.price)
        }
        session['cart'] = cart
        session.modified = True
        return cart

# app/services/pdf_service.py
class PDFService:
    def generate_order_receipt(self, order):
        """Genera PDF de recibo de orden"""
        # Mover las ~270 líneas de generate_pdf() aquí
        ...
```

### 2.3 Foreign Key Faltante en User.center

**Archivo**: `app/models.py:41`

```python
# ACTUAL:
center = db.Column(db.String(64), index=True)

# CORRECCIÓN:
center_id = db.Column(db.Integer, db.ForeignKey('center.id'), nullable=True)
center = db.relationship('Center', backref='users')
```

### 2.4 Extraer Decoradores de Respuesta

```python
# CREAR: app/utils/responses.py

def ajax_or_redirect(success_message, redirect_url):
    """Decorador para manejar respuestas AJAX y normales"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            result = f(*args, **kwargs)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(result)
            flash(result.get('message', success_message),
                  'success' if result.get('success') else 'error')
            return redirect(redirect_url)
        return wrapped
    return decorator

# USO:
@shop_bp.route('/add_to_cart', methods=['POST'])
@ajax_or_redirect('Producto agregado', 'shop.cart')
def add_to_cart():
    # ... lógica
    return {'success': True, 'message': 'Agregado', 'cart_count': count}
```

---

## 3. RENDIMIENTO - ALTO

### 3.1 Problemas N+1 Queries (CRÍTICO)

**Archivo**: `blueprints/shop.py:403-420`

```python
# ACTUAL (N queries):
for toy_id, item in cart.items():
    toy = Toy.query.get(int(toy_id))  # ❌ 1 query por item

# CORRECCIÓN (1 query):
toy_ids = [int(tid) for tid in cart.keys()]
toys = {t.id: t for t in Toy.query.filter(Toy.id.in_(toy_ids)).all()}

for toy_id, item in cart.items():
    toy = toys.get(int(toy_id))
```

**Archivo**: `blueprints/shop.py:787-793` (PDF generation)

```python
# ACTUAL:
for item in order.items:
    data.append([item.toy.name, ...])  # ❌ Lazy loading de toy

# CORRECCIÓN - usar eager loading:
from sqlalchemy.orm import selectinload

order = Order.query.options(
    selectinload(Order.items).selectinload(OrderItem.toy)
).get_or_404(order_id)
```

### 3.2 Índices Faltantes (CRÍTICO)

**Archivo**: `app/models.py`

```python
# AGREGAR a OrderItem:
class OrderItem(db.Model):
    __table_args__ = (
        db.Index('idx_orderitem_order_toy', 'order_id', 'toy_id'),
    )

# AGREGAR a Order:
class Order(db.Model):
    __table_args__ = (
        db.Index('idx_order_active_date', 'is_active', 'order_date'),
    )

# AGREGAR a User:
class User(db.Model):
    __table_args__ = (
        db.Index('idx_user_active_created', 'is_active', 'created_at'),
    )
```

### 3.3 Búsqueda Sin Paginación (ALTO)

**Archivo**: `blueprints/shop.py:223`

```python
# ACTUAL:
toys = toys_query.all()  # ❌ Carga TODOS los resultados

# CORRECCIÓN:
page = request.args.get('page', 1, type=int)
toys = toys_query.paginate(page=page, per_page=12, error_out=False)
```

### 3.4 Cachear Categorías y Centros (MEDIO)

```python
# AGREGAR a blueprints/shop.py:
from flask_caching import Cache
cache = Cache()

@cache.cached(timeout=3600, key_prefix='toy_categories')
def get_categories():
    return db.session.query(Toy.category).filter(
        Toy.is_active == True,
        Toy.category.isnot(None)
    ).distinct().all()

# AGREGAR a app/__init__.py context_processor:
@cache.cached(timeout=3600, key_prefix='all_centers')
def get_all_centers():
    return Center.query.order_by(Center.name.asc()).all()
```

### 3.5 Configurar Connection Pooling (MEDIO)

**Archivo**: `app/config.py`

```python
# AGREGAR:
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 20,
    'pool_timeout': 30
}
```

### 3.6 Exportaciones Usan Demasiada Memoria (BAJO)

**Archivo**: `blueprints/admin.py:1710-1722`

```python
# ACTUAL:
orders = Order.query.all()  # ❌ Todo en memoria
output = io.StringIO()
# ... escribe todo

# CORRECCIÓN - usar streaming:
def generate_csv():
    yield 'ID,Fecha,Total\n'
    for order in Order.query.yield_per(100):
        yield f'{order.id},{order.order_date},{order.total_price}\n'

return Response(
    generate_csv(),
    mimetype='text/csv',
    headers={'Content-Disposition': 'attachment;filename=orders.csv'}
)
```

---

## 4. TESTING - CRÍTICO

### 4.1 Estado Actual

| Métrica | Valor | Objetivo |
|---------|-------|----------|
| Unit Tests | 6 archivos | 30+ |
| Integration Tests | 0 | 15+ |
| E2E Tests | 25 (duplicados) | 10 focalizados |
| Cobertura | ~15% | 70%+ |
| CI/CD | ❌ Ninguno | GitHub Actions |

### 4.2 Crear conftest.py (CRÍTICO)

```python
# CREAR: tests/conftest.py
import pytest
from app import create_app
from app.extensions import db
from app.models import User, Toy, Center
from app.config import Config

class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db_session(app):
    return db.session

@pytest.fixture
def admin_user(app, db_session):
    user = User(username='admin', email='admin@test.com', is_admin=True)
    user.set_password('TestPass123')
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def regular_user(app, db_session):
    user = User(username='user', email='user@test.com', is_admin=False)
    user.set_password('TestPass123')
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def admin_client(client, admin_user):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user.id)
        sess['_fresh'] = True
    return client

@pytest.fixture
def sample_center(app, db_session):
    center = Center(slug='test-center', name='Test Center', discount_percentage=10)
    db_session.add(center)
    db_session.commit()
    return center

@pytest.fixture
def sample_toy(app, db_session):
    toy = Toy(
        name='Test Toy',
        description='A test toy',
        price=29.99,
        stock=100,
        category='Juguetes',
        is_active=True
    )
    db_session.add(toy)
    db_session.commit()
    return toy
```

### 4.3 Agregar pytest a Dependencias (CRÍTICO)

**Archivo**: `requirements.txt`

```
# AGREGAR:
pytest>=7.0
pytest-cov>=3.0
pytest-flask>=1.2
```

### 4.4 Crear GitHub Actions (CRÍTICO)

```yaml
# CREAR: .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-flask

    - name: Run tests with coverage
      run: |
        pytest tests/ -v --cov=app --cov=blueprints --cov-report=xml --cov-report=term

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
```

### 4.5 Tests Críticos Faltantes

```python
# CREAR: tests/unit/test_models.py
def test_user_password_hashing(app, db_session):
    user = User(username='test', email='test@test.com')
    user.set_password('SecurePass123')
    assert user.password_hash != 'SecurePass123'
    assert user.check_password('SecurePass123')
    assert not user.check_password('WrongPass')

def test_order_total_calculation(app, db_session, sample_toy):
    order = Order(user_id=1, subtotal_price=100, discount_percentage=10)
    assert order.discount_amount == 10
    assert order.total_price == 90

# CREAR: tests/unit/test_security.py
def test_password_strength_validation():
    from app.security import validate_password_strength

    assert not validate_password_strength('short')[0]
    assert not validate_password_strength('nouppercase123')[0]
    assert not validate_password_strength('NOLOWERCASE123')[0]
    assert not validate_password_strength('NoNumbers')[0]
    assert validate_password_strength('ValidPass123')[0]

def test_unauthorized_admin_access(client):
    response = client.get('/admin/dashboard')
    assert response.status_code in [401, 403, 302]

# CREAR: tests/integration/test_order_flow.py
def test_complete_order_flow(admin_client, sample_toy, sample_center, db_session):
    # Agregar al carrito
    response = admin_client.post('/add_to_cart', data={
        'toy_id': sample_toy.id,
        'quantity': 2
    })
    assert response.status_code == 200

    # Checkout
    response = admin_client.post('/checkout', data={
        'center': sample_center.slug
    })
    assert response.status_code == 302

    # Verificar orden creada
    order = Order.query.first()
    assert order is not None
    assert order.total_price == sample_toy.price * 2 * 0.9  # 10% descuento

    # Verificar stock reducido
    db_session.refresh(sample_toy)
    assert sample_toy.stock == 98
```

---

## 5. DUPLICACIÓN DE CÓDIGO - MEDIO

### 5.1 format_currency Definido 3 Veces

**Archivos**: `app/filters.py`, `app/__init__.py`, `blueprints/shop.py`

```python
# SOLUCIÓN: Usar solo app/filters.py y eliminar las otras definiciones

# En blueprints/shop.py:637-639 ELIMINAR:
# def format_currency(amount):
#     return f"A$ {amount:,.2f}"

# En app/__init__.py ELIMINAR format_currency_value duplicado
```

### 5.2 Patrón AJAX Repetido 50+ Veces

```python
# ACTUAL (repetido en todas partes):
if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    return jsonify({'success': True, 'message': message})

# CREAR app/utils/responses.py:
def is_ajax_request():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def json_or_flash(data, redirect_url):
    if is_ajax_request():
        return jsonify(data)
    flash(data.get('message', ''), 'success' if data.get('success') else 'error')
    return redirect(redirect_url)
```

### 5.3 TestConfig Duplicado en 6 Tests

Ver sección 4.2 - resolver con `conftest.py` compartido.

---

## 6. PRIORIZACIÓN DE TAREAS

### Semana 1 - Críticos

- [ ] Corregir bug de 2FA en `app/security.py`
- [ ] Eliminar todos los `print()` statements
- [ ] Crear `tests/conftest.py`
- [ ] Agregar pytest a `requirements.txt`
- [ ] Crear `.github/workflows/tests.yml`

### Semana 2 - Altos

- [ ] Agregar índices a modelos (OrderItem, Order, User)
- [ ] Corregir N+1 queries en cart y checkout
- [ ] Implementar paginación en búsqueda
- [ ] Crear tests unitarios para modelos
- [ ] Implementar rate limiting con Redis/Flask-Limiter

### Semana 3-4 - Medios

- [ ] Dividir `blueprints/admin.py` en módulos
- [ ] Crear capa de servicios (OrderService, CartService)
- [ ] Cachear categorías y centros
- [ ] Consolidar función `format_currency`
- [ ] Crear tests de integración

### Mes 2+ - Mejoras

- [ ] Migrar User.center a foreign key
- [ ] Extraer generación PDF a servicio
- [ ] Implementar streaming para exportaciones
- [ ] Configurar connection pooling
- [ ] Mejorar CSP headers

---

## 7. COMANDOS ÚTILES

```bash
# Ejecutar tests
python -m pytest tests/ -v

# Con cobertura
python -m pytest tests/ --cov=app --cov=blueprints --cov-report=html

# Solo tests unitarios
python -m pytest tests/unit/ -v

# Buscar print statements
grep -r "print(" blueprints/ app/ --include="*.py"

# Verificar imports no usados
pip install autoflake
autoflake --check app/ blueprints/

# Formatear código
pip install black
black app/ blueprints/ tests/

# Verificar tipos
pip install mypy
mypy app/ blueprints/
```

---

## Contacto

Para dudas sobre estas mejoras, consultar la documentación en `CLAUDE.md` o revisar los archivos específicos mencionados en cada sección.
