#!/usr/bin/env python3
"""
🚀 TIENDITA ALOHA - PUNTO DE ENTRADA PRINCIPAL
Sistema de e-commerce con logging avanzado, cache inteligente y monitoreo de performance.

Versión: 2.0
Última actualización: 2025-01-04
"""
import os
import sys
import io
from pathlib import Path

# Fix Windows headless/encoding issues
try:
    if not sys.stdout or not hasattr(sys.stdout, 'buffer') or sys.stdout.buffer is None:
        # Headless mode: redirect to log file
        log_path = Path(__file__).parent / 'instance' / 'app.log'
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_file = open(log_path, 'a', encoding='utf-8')
        sys.stdout = log_file
        sys.stderr = log_file
    elif sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

# Agregar el directorio actual al path para importaciones antes de importar "app"
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app

# Configuración de host y puerto con valores por defecto
APP_HOST = os.getenv("APP_HOST", "192.168.0.51")
APP_PORT = int(os.getenv("APP_PORT", 5070))

def initialize_advanced_systems(app):
    """Inicializar sistemas avanzados de la aplicación"""
    print("🔧 Initializing systems...")
    print("✅ Application ready")

def setup_environment():
    """Configurar variables de entorno y directorios necesarios"""
    # Variables de entorno por defecto
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_DEBUG', '1')
    
    # Crear directorios necesarios
    base_dir = Path(__file__).parent
    directories = [
        base_dir / 'instance',
        base_dir / 'instance' / 'logs',
        base_dir / 'instance' / 'backups',
        base_dir / 'static' / 'images' / 'toys'
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    print("📁 Directory structure verified")

def print_startup_banner():
    """Mostrar banner de inicio con información del sistema"""
    banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                    🎮 TIENDITA ALOHA 🎮                     ║
║                                                              ║
║  Sistema de E-commerce Avanzado                             ║
║  Versión: 2.0 | Estado: Production Ready ✅                ║
║                                                              ║
║  Características:                                           ║
║  • 📊 Logging avanzado con rotación automática              ║
║  • ⚡ Cache inteligente con Redis/Memory                    ║
║  • 💾 Sistema de backup automático                          ║
║  • 🔒 Rate limiting y seguridad CSRF                       ║
║  • 📱 Diseño responsive y moderno                          ║
║  • 🎯 Panel administrativo completo                        ║
║                                                              ║
║  URL: http://{APP_HOST}:{APP_PORT}                                ║
║  Admin: http://{APP_HOST}:{APP_PORT}/admin                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Función principal de la aplicación"""
    try:
        # Mostrar banner de inicio
        print_startup_banner()
        
        # Configurar entorno
        setup_environment()
        
        # Crear la aplicación Flask
        print("🏗️ Creating Flask application...")
        app = create_app()
        
        # Inicializar sistemas avanzados
        initialize_advanced_systems(app)
        
        print("\n🚀 Starting Flask development server...")
        print(f"📱 Access the application at: http://{APP_HOST}:{APP_PORT}")
        print(f"🔧 Admin panel at: http://{APP_HOST}:{APP_PORT}/admin")
        print("\n💡 Press Ctrl+C to stop the server\n")

        # Ejecutar la aplicación
        app.run(
            host=APP_HOST,
            port=APP_PORT,
            debug=False,
            use_reloader=True,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")

    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
