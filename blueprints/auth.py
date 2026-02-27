"""
Blueprint para manejo de autenticación de usuarios
Incluye: login, logout, registro
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Length, Email
from datetime import datetime

# Importaciones absolutas
from app.models import User, Center
from app.extensions import db
from app.utils.centers import collect_center_choices, normalize_center_slug
from utils import normalize_email


def validate_password_strength(password):
    """Validate password meets security requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

# Crear el blueprint de autenticación
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Formularios
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    center = SelectField('Center', validators=[DataRequired()], choices=[])


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    if current_user.is_authenticated:
        return redirect(url_for('shop.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            user.last_login = datetime.now()
            db.session.commit()

            remember = bool(request.form.get('remember'))
            if login_user(user, remember=remember):
                flash('¡Bienvenido de nuevo!', 'success')
                return redirect(url_for('shop.index'))
            else:
                flash('Error al iniciar sesión', 'error')
        else:
            flash('Usuario o contraseña incorrectos', 'error')

    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión del usuario"""
    session.clear()
    logout_user()
    return redirect(url_for('shop.index'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro de nuevos usuarios"""
    if current_user.is_authenticated:
        return redirect(url_for('shop.index'))

    form = RegisterForm()
    center_choices, centers_map = collect_center_choices()
    form.center.choices = center_choices

    if form.validate_on_submit():
        # Validar unicidad de username y email para evitar errores 500 por constraints
        existing_username = User.query.filter_by(username=form.username.data).first()
        normalized_email = normalize_email(form.email.data)
        existing_email = User.query.filter_by(email=normalized_email).first() if normalized_email else None

        center_slug = normalize_center_slug(form.center.data)
        if center_slug not in centers_map:
            flash('El centro seleccionado no es válido', 'warning')
            return render_template('register.html', form=form)

        center_record = Center.query.filter_by(slug=center_slug).first() if center_slug else None

        # Generic error message to prevent user enumeration
        if existing_username or existing_email:
            flash('El nombre de usuario o correo electrónico ya está registrado. Si ya tienes una cuenta, inicia sesión.', 'warning')
            return render_template('register.html', form=form)

        user = User(
            username=form.username.data,
            center=center_record.slug if center_record else center_slug,
            balance=0.0,
            created_at=datetime.now(),
            email=normalized_email,
            last_login=datetime.now()
        )
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al registrar usuario: {e}")
            flash('No se pudo completar el registro. Intenta de nuevo o contacta al administrador.', 'danger')
            return render_template('register.html', form=form)

        flash('¡Registro exitoso! Ahora puedes iniciar sesión', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@auth_bp.route('/force_password_change', methods=['GET', 'POST'])
@login_required
def force_password_change():
    """Solicitar cambio de contraseña al primer inicio de sesión."""
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        is_valid, msg = validate_password_strength(new_password)
        if not new_password or not is_valid:
            flash(msg if new_password else 'La nueva contraseña es requerida.', 'error')
            return render_template('force_password_change.html')
        if new_password != confirm_password:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('force_password_change.html')
        try:
            current_user.set_password(new_password)
            # Desactivar la bandera de cambio obligatorio si existe
            try:
                current_user.must_change_password = False
            except Exception:
                pass
            db.session.commit()
            flash('Contraseña actualizada correctamente.', 'success')
            return redirect(url_for('shop.index'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al actualizar contraseña obligatoria: {e}")
            flash('No se pudo actualizar la contraseña. Intenta de nuevo.', 'error')
            return render_template('force_password_change.html')

    return render_template('force_password_change.html')
