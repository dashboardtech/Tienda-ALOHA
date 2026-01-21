"""
Configuración global de pytest con fixtures compartidas.
"""
import pytest
from app import create_app
from app.extensions import db
from app.models import User, Toy, Order, OrderItem, Center
from app.config import Config


class TestConfig(Config):
    """Configuración para entorno de pruebas."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key-for-testing'
    SERVER_NAME = 'localhost'
    ADMIN_2FA_REQUIRED = False


@pytest.fixture
def app():
    """Crea una instancia de la aplicación para testing."""
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Cliente de prueba para hacer requests HTTP."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Sesión de base de datos para pruebas."""
    return db.session


@pytest.fixture
def admin_user(app, db_session):
    """Crea un usuario administrador para pruebas."""
    user = User(
        username='admin_test',
        email='admin@test.com',
        is_admin=True,
        balance=1000.0
    )
    user.set_password('TestPass123')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def regular_user(app, db_session):
    """Crea un usuario regular para pruebas."""
    user = User(
        username='user_test',
        email='user@test.com',
        is_admin=False,
        balance=500.0
    )
    user.set_password('TestPass123')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def admin_client(client, admin_user):
    """Cliente autenticado como administrador."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user.id)
        sess['_fresh'] = True
    return client


@pytest.fixture
def user_client(client, regular_user):
    """Cliente autenticado como usuario regular."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(regular_user.id)
        sess['_fresh'] = True
    return client


@pytest.fixture
def sample_center(app, db_session):
    """Crea un centro de prueba."""
    center = Center(
        slug='test-center',
        name='Centro de Prueba',
        discount_percentage=10.0
    )
    db_session.add(center)
    db_session.commit()
    return center


@pytest.fixture
def sample_toy(app, db_session):
    """Crea un juguete de prueba."""
    toy = Toy(
        name='Juguete de Prueba',
        description='Un juguete para testing',
        price=29.99,
        stock=100,
        category='Juguetes',
        age_range='3-6',
        gender_category='Unisex',
        is_active=True
    )
    db_session.add(toy)
    db_session.commit()
    return toy


@pytest.fixture
def sample_toys(app, db_session):
    """Crea varios juguetes de prueba."""
    toys = []
    for i in range(5):
        toy = Toy(
            name=f'Juguete {i+1}',
            description=f'Descripción del juguete {i+1}',
            price=10.00 + (i * 5),
            stock=50,
            category='Juguetes' if i % 2 == 0 else 'Muñecas',
            age_range='3-6',
            gender_category='Unisex',
            is_active=True
        )
        db_session.add(toy)
        toys.append(toy)
    db_session.commit()
    return toys


@pytest.fixture
def sample_order(app, db_session, regular_user, sample_toy):
    """Crea una orden de prueba."""
    order = Order(
        user_id=regular_user.id,
        subtotal_price=sample_toy.price,
        discount_percentage=0.0,
        discount_amount=0.0,
        discounted_total=sample_toy.price,
        total_price=sample_toy.price,
        status='completada'
    )
    db_session.add(order)
    db_session.flush()

    order_item = OrderItem(
        order_id=order.id,
        toy_id=sample_toy.id,
        quantity=1,
        price=sample_toy.price
    )
    db_session.add(order_item)
    db_session.commit()
    return order


@pytest.fixture
def cart_with_items(client, sample_toy):
    """Configura un carrito con items para pruebas."""
    with client.session_transaction() as sess:
        sess['cart'] = {
            str(sample_toy.id): {
                'quantity': 2,
                'price': float(sample_toy.price)
            }
        }
    return client
