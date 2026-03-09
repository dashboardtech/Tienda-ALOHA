"""
Blueprint para funcionalidades de usuario
Incluye: perfil, balance, cambio de contraseña, actualización de centro, historial de órdenes
"""

from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, current_app
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.orm import selectinload

# Importaciones absolutas
from app.models import Toy, Order, OrderItem, User, Center
from app.extensions import db
from app.filters import format_currency
from app.security import validate_password_strength
from app.balance import atomic_add_balance, is_duplicate_operation

# Crear el blueprint de usuario
user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/profile')
@login_required
def profile():
    """Página de perfil del usuario con historial de órdenes"""
    # Obtener las órdenes del usuario ordenadas por fecha descendente
    orders = Order.query.filter_by(user_id=current_user.id)\
        .options(selectinload(Order.items))\
        .order_by(desc(Order.order_date)).all()
    
    # Formatear las órdenes para la vista
    formatted_orders = []
    for order in orders:
        formatted_orders.append({
            'id': order.id,
            'order_date': order.order_date.strftime('%d/%m/%Y %H:%M'),
            'total': format_currency(order.total_price),
            'status': order.status,
            'item_count': sum(item.quantity for item in order.items)
        })
    
    return render_template('profile.html', orders=formatted_orders)

@user_bp.route('/add_balance', methods=['POST'])
@login_required
def add_balance():
    """Agregar balance al usuario - solo administradores pueden agregar balance"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Solo administradores pueden agregar balance'}), 403

    try:
        user_id = request.form.get('user_id', current_user.id, type=int)
        target_user = User.query.get(user_id) if current_user.is_admin else current_user
        if not target_user:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404

        amount = Decimal(request.form.get('amount', '0'))
        if amount <= 0 or amount > Decimal('9999.99'):
            return jsonify({'success': False, 'message': 'Cantidad inválida (debe ser entre 0.01 y 9999.99)'}), 400
        if amount != amount.quantize(Decimal('0.01')):
            return jsonify({'success': False, 'message': 'Máximo 2 decimales permitidos'}), 400

        if is_duplicate_operation(target_user.id, amount, 'add_balance'):
            return jsonify({'success': False, 'message': 'Operación duplicada detectada. Espera unos segundos.'}), 409

        target_user = atomic_add_balance(target_user.id, amount)
        db.session.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'Se agregaron A$ {amount:.2f} al balance de {target_user.username}',
                'new_balance': f"A$ {target_user.balance:.2f}"
            })

        flash(f'Se agregaron A$ {amount:.2f} al balance de {target_user.username}', 'success')
        return redirect(url_for('user.profile'))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al agregar balance: {e}")
        return jsonify({'success': False, 'message': 'Error al procesar la operación'}), 400

@user_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Cambiar contraseña del usuario"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not current_user.check_password(current_password):
        flash('Contraseña actual incorrecta', 'error')
        return redirect(url_for('user.profile'))

    if new_password != confirm_password:
        flash('Las contraseñas nuevas no coinciden', 'error')
        return redirect(url_for('user.profile'))

    # Validate password strength before setting
    is_strong, message = validate_password_strength(new_password)
    if not is_strong:
        flash(message, 'error')
        return redirect(url_for('user.profile'))

    current_user.set_password(new_password)
    db.session.commit()
    flash('Contraseña actualizada correctamente', 'success')
    return redirect(url_for('user.profile'))

@user_bp.route('/update_center', methods=['POST'])
@login_required
def update_center():
    """Actualizar centro del usuario"""
    data = request.get_json()
    new_center = (data.get('center') or '').strip().lower()

    if not new_center:
        return jsonify({'success': False, 'message': 'Centro inválido'}), 400

    center_record = Center.query.filter_by(slug=new_center).first()
    if not center_record:
        return jsonify({'success': False, 'message': 'Centro no encontrado'}), 404

    try:
        current_user.center = center_record.slug
        db.session.commit()
        return jsonify({'success': True})
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error(f"Error al actualizar centro: {exc}")
        return jsonify({'success': False, 'message': 'No se pudo actualizar el centro'}), 500

@user_bp.route('/update_theme', methods=['POST'])
@login_required
def update_theme():
    """Guardar preferencia de tema del usuario actual."""
    try:
        data = request.get_json() or {}
        theme = (data.get('theme') or '').strip()
        allowed = {
            'aloha-light', 'aloha-dark', 'cherry-blossom', 'underwater', 'halloween', 'patriotic'
        }
        if theme not in allowed:
            return jsonify({'success': False, 'message': 'Tema inválido'}), 400
        current_user.theme = theme
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al actualizar tema: {e}")
        return jsonify({'success': False, 'message': 'No se pudo actualizar el tema'}), 400

# Helper function para los templates
def get_toy(toy_id):
    """Helper function to get toy by id"""
    return Toy.query.get(int(toy_id))
