import os
from datetime import timedelta

def _get_persistent_key(env_var, filename):
    """Get a secret key from env, file, or generate and persist one."""
    key = os.environ.get(env_var)
    if key:
        return key
    key_file = os.path.join(os.path.dirname(__file__), '..', 'instance', filename)
    key_file = os.path.abspath(key_file)
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    key = os.urandom(32)
    os.makedirs(os.path.dirname(key_file), exist_ok=True)
    with open(key_file, 'wb') as f:
        f.write(key)
    return key


class Config:
    # Security Keys - persistent across restarts
    SECRET_KEY = _get_persistent_key('SECRET_KEY', '.secret_key')
    CSRF_SECRET_KEY = _get_persistent_key('CSRF_SECRET_KEY', '.csrf_secret_key')
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Session Security
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Database Configuration
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'instance', 'tiendita.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload Security
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max-limit
    UPLOAD_FOLDER = os.path.join('static', 'images', 'toys')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # PDF/Receipt assets
    PDF_LOGO_PATH = os.environ.get('PDF_LOGO_PATH')
    
    # Password Security
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPER = True
    PASSWORD_REQUIRE_LOWER = True
    PASSWORD_REQUIRE_NUMBERS = True
    
    # Rate Limiting
    RATELIMIT_DEFAULT = '100/hour'
    RATELIMIT_LOGIN = '5/minute'
    RATELIMIT_STORAGE_URL = 'memory://'
    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_DURATION = 30  # minutes
    
    # Two-Factor Authentication
    ADMIN_2FA_REQUIRED = True
    ADMIN_2FA_ISSUER = 'Tienditas-Aloha'
    ADMIN_2FA_SECRET_LENGTH = 32
    
    # Age Verification
    MIN_AGE = 8
    MAX_AGE = 18
    REQUIRE_PARENTAL_CONSENT = True
    
    # Transaction Limits
    MAX_DAILY_TRANSACTION_AMOUNT = 50.0
    MAX_SINGLE_TRANSACTION_AMOUNT = 20.0
    MAX_DAILY_TRANSACTIONS = 10
    
    # Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Logging Configuration
    SECURITY_LOG_FILENAME = 'security.log'
    TRANSACTION_LOG_FILENAME = 'transactions.log'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    TEMPLATES_AUTO_RELOAD = True
    
    # Override some security settings for development
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True

    # Ensure development uses the correct database file
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'tiendita-dev.db')

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PREFERRED_URL_SCHEME = 'https'
