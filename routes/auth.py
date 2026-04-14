# routes/auth.py
from flask import render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from routes import auth_bp
from services.auth_service import AuthService

@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json()
    result = AuthService.authenticate_user(
        data.get('username'), 
        data.get('password'),
        request
    )
    
    if result['success']:
        return jsonify({
            'success': True, 
            'role': result['role'],
            'redirect': url_for('dashboard.dashboard')
        })
    
    return jsonify({'success': False, 'error': result['error']}), 401

@auth_bp.route('/logout')
@login_required
def logout():
    AuthService.logout_user(request)
    return redirect(url_for('auth.login'))