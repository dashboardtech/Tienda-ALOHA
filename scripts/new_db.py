from app import app, db
from models import User, Toy
from datetime import datetime
import os
import shutil

ADMIN_DEFAULT_PASSWORD = os.environ.get('ADMIN_DEFAULT_PASSWORD')
if not ADMIN_DEFAULT_PASSWORD:
    raise RuntimeError("ADMIN_DEFAULT_PASSWORD environment variable must be set")

def create_new_db():
    with app.app_context():
        print("\n🔄 Creando nueva base de datos...")
        
        # 1. Eliminar directorio instance y su contenido
        print("\n1️⃣ Limpiando directorios...")
        if os.path.exists('instance'):
            shutil.rmtree('instance')
        if os.path.exists('migrations'):
            shutil.rmtree('migrations')
        if os.path.exists('flask_session'):
            shutil.rmtree('flask_session')
        print("✅ Directorios eliminados")
        
        # 2. Crear directorio instance
        print("\n2️⃣ Creando directorio instance...")
        os.makedirs('instance')
        print("✅ Directorio instance creado")
        
        # 3. Eliminar todas las tablas y crearlas de nuevo
        print("\n3️⃣ Creando tablas...")
        db.drop_all()
        db.create_all()
        print("✅ Tablas creadas")
        
        # 4. Crear admin
        print("\n4️⃣ Creando admin...")
        admin = User(
            username='admin',
            is_admin=True,
            balance=1000.0,
            center='David',
            created_at=datetime.now(),
            last_login=datetime.now()
        )
        admin.set_password(ADMIN_DEFAULT_PASSWORD)
        db.session.add(admin)
        
        try:
            db.session.commit()
            print("✅ Admin creado")
        except Exception as e:
            print(f"❌ Error al crear admin: {str(e)}")
            db.session.rollback()
            return False
        
        # 5. Crear juguetes
        print("\n5️⃣ Creando juguetes...")
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
        
        try:
            db.session.commit()
            print(f"✅ {len(toys)} juguetes creados")
        except Exception as e:
            print(f"❌ Error al crear juguetes: {str(e)}")
            db.session.rollback()
            return False
        
        # 6. Verificar
        print("\n6️⃣ Verificando...")
        admin_check = User.query.filter_by(username='admin').first()
        toys_check = Toy.query.all()
        
        if admin_check and admin_check.is_admin:
            print("✅ Admin verificado")
            print(f"- Username: {admin_check.username}")
            print(f"- Is Admin: {admin_check.is_admin}")
            print(f"- Balance: {admin_check.balance}")
        else:
            print("❌ Error: Admin no encontrado")
            return False
        
        print(f"\n✅ Juguetes verificados: {len(toys_check)}")
        for toy in toys_check:
            print(f"- {toy.name} ({toy.category}): {toy.price}")
        
        print("\n✨ Base de datos creada exitosamente")
        return True

if __name__ == '__main__':
    # Detener el servidor Flask si está corriendo
    print("⚠️ Asegúrate de que el servidor Flask esté detenido")
    input("Presiona Enter para continuar...")
    
    # Crear nueva base de datos
    if create_new_db():
        print("\n🚀 Todo listo. Ahora puedes iniciar el servidor Flask")
        print("\n👤 Credenciales de admin:")
        print("Username: admin")
        print("Password: (set via ADMIN_DEFAULT_PASSWORD env var)")
    else:
        print("\n❌ Hubo errores durante la creación")