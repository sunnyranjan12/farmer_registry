# routes/admin.py
from flask import request, jsonify
from flask_login import login_required, current_user
from routes import admin_bp
from models import User, CustomField, db

@admin_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    if not current_user.has_permission('manage_users'):
        return jsonify({'error': 'Permission denied'}), 403
    
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'role': u.role,
        'is_active': u.is_active,
        'created_at': u.created_at.strftime('%Y-%m-%d')
    } for u in users])

@admin_bp.route('/users', methods=['POST'])
@login_required
def create_user():
    if not current_user.has_permission('manage_users'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        role=data.get('role', 'viewer'),
        is_active=True
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/users/<int:id>', methods=['PUT'])
@login_required
def update_user(id):
    if not current_user.has_permission('manage_users'):
        return jsonify({'error': 'Permission denied'}), 403
    
    user = User.query.get_or_404(id)
    data = request.get_json()
    
    if 'role' in data:
        user.role = data['role']
    if 'is_active' in data:
        user.is_active = data['is_active']
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/users/<int:id>', methods=['DELETE'])
@login_required
def delete_user(id):
    if not current_user.has_permission('manage_users'):
        return jsonify({'error': 'Permission denied'}), 403
    
    if id == current_user.id:
        return jsonify({'error': 'Cannot delete yourself'}), 400
    
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/custom-fields', methods=['GET'])
@login_required
def get_custom_fields():
    if not current_user.has_permission('manage_fields'):
        return jsonify({'error': 'Permission denied'}), 403
    
    fields = CustomField.query.filter_by(is_active=True).order_by(CustomField.display_order).all()
    return jsonify([f.to_dict() for f in fields])

@admin_bp.route('/custom-fields', methods=['POST'])
@login_required
def add_custom_field():
    if not current_user.has_permission('manage_fields'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    field = CustomField(
        field_name=data['field_name'],
        field_label=data['field_label'],
        field_type=data.get('field_type', 'text'),
        is_mandatory=data.get('is_mandatory', False),
        display_order=data.get('display_order', 0)
    )
    db.session.add(field)
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/custom-fields/<int:id>', methods=['DELETE'])
@login_required
def delete_custom_field(id):
    if not current_user.has_permission('manage_fields'):
        return jsonify({'error': 'Permission denied'}), 403
    
    field = CustomField.query.get_or_404(id)
    field.is_active = False
    db.session.commit()
    return jsonify({'success': True})