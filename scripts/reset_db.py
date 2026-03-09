"""
Script para reiniciar la base de datos.

Este script elimina la base de datos existente y crea una nueva con las tablas necesarias.
"""
import os
from app import create_app, db
from app.models import User, Toy, Order, OrderItem

ADMIN_DEFAULT_PASSWORD = os.environ.get('ADMIN_DEFAULT_PASSWORD')
if not ADMIN_DEFAULT_PASSWORD:
    raise RuntimeError("ADMIN_DEFAULT_PASSWORD environment variable must be set")

def reset_database():
    """Elimina la base de datos existente y crea una nueva con las tablas necesarias."""
    app = create_app()
    
    with app.app_context():
        # Eliminar la base de datos existente
        db_path = os.path.join('instance', 'tiendita-dev.db')
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"✅ Base de datos existente eliminada: {db_path}")
        
        # Crear las tablas
        print("🔨 Creando tablas...")
        db.create_all()
        
        # Crear un usuario administrador
        admin = User(
            username='admin',
            email='admin@aloha.com',
            is_admin=True,
            balance=1000.0,
            center='David',
            is_active=True
        )
        admin.set_password(ADMIN_DEFAULT_PASSWORD)
        db.session.add(admin)
        
        # Crear algunos juguetes de ejemplo
        toys = [
            {
                'name': 'Pulseras Mágicas',
                'description': 'Pulseras con lentejuelas reversibles.',
                'price': 25.0,
                'category': 'Niña',
                'stock': 10,
                'is_active': True
            },
            {
                'name': 'Coche de Carreras',
                'description': 'Coche de carreras a control remoto.',
                'price': 50.0,
                'category': 'Niño',
                'stock': 5,
                'is_active': True
            },
            {
                'name': 'Rompecabezas 1000 Piezas',
                'description': 'Rompecabezas educativo de 1000 piezas.',
                'price': 35.0,
                'category': 'Familiar',
                'stock': 8,
                'is_active': True
            }
        ]
        
        for toy_data in toys:
            toy = Toy(**toy_data)
            db.session.add(toy)
        
        # Guardar los cambios
        db.session.commit()
        print("✅ Base de datos reiniciada exitosamente.")
        print(f"👤 Usuario administrador creado:")
        print(f"   Username: admin")
        print(f"   Password: (set via ADMIN_DEFAULT_PASSWORD env var)")
        print(f"📦 {len(toys)} juguetes de ejemplo creados.")

if __name__ == "__main__":
    reset_database()
