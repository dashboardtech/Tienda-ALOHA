import os
import sys
from datetime import datetime

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Toy

ADMIN_DEFAULT_PASSWORD = os.environ.get('ADMIN_DEFAULT_PASSWORD')
if not ADMIN_DEFAULT_PASSWORD:
    raise RuntimeError("ADMIN_DEFAULT_PASSWORD environment variable must be set")

# Crear la aplicación
app = create_app()

def init_all():
    with app.app_context():
        print("\n🗑️ Limpiando base de datos...")
        
        # Asegurarse de que el directorio instance exista
        os.makedirs('instance', exist_ok=True)
        
        # Eliminar base de datos existente
        db_path = os.path.join('instance', 'tiendita.db')
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"✅ Base de datos existente eliminada: {db_path}")
        
        # Crear tablas
        print("🔨 Creando tablas...")
        db.create_all()
        db.session.commit()
        print("✅ Tablas creadas")
        
        # Crear admin
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
        db.session.commit()
        print("\n👤 Usuario admin creado:")
        print("Username: admin")
        print("Password: (set via ADMIN_DEFAULT_PASSWORD env var)")
        
        # Crear juguetes
        toys = [
            {
                "name": "Pulseras Mágicas",
                "description": "Pulseras con lentejuelas reversibles.",
                "category": "Niña",
                "price": 25.0,
                "image_url": "/static/images/toys/default_toy.png"
            },
            {
                "name": "Carro Hot Wheels",
                "description": "Carro de colección Hot Wheels.",
                "category": "Niño",
                "price": 15.0,
                "image_url": "/static/images/toys/default_toy.png"
            },
            {
                "name": "Cubo Rubik",
                "description": "Cubo mágico para resolver.",
                "category": "Mixta",
                "price": 20.0,
                "image_url": "/static/images/toys/default_toy.png"
            }
        ]
        
        for toy_data in toys:
            toy = Toy(**toy_data)
            db.session.add(toy)
        
        db.session.commit()
        print("\n✅ Juguetes creados")
        
        # Verificar todo
        print("\n=== Verificación Final ===")
        print(f"Usuarios: {User.query.count()}")
        print(f"Juguetes: {Toy.query.count()}")
        
        admin = User.query.filter_by(username='admin').first()
        if admin and admin.check_password(ADMIN_DEFAULT_PASSWORD):
            print("✅ Admin verificado correctamente")
        else:
            print("❌ Error en la verificación del admin")

if __name__ == '__main__':
    init_all()
