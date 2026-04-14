# services/auth_service.py - Authentication business logic
from models import User, ActivityLog
from flask_login import login_user, logout_user, current_user
from datetime import datetime

class AuthService:
    
    @staticmethod
    def authenticate_user(username, password, request):
        """Authenticate user and create session"""
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=True)
            
            # Log activity
            log = ActivityLog(
                user_id=user.id,
                username=user.username,
                action='login',
                details=f'User {username} logged in',
                ip_address=request.remote_addr
            )
            from models import db
            db.session.add(log)
            db.session.commit()
            
            return {'success': True, 'role': user.role, 'user': user}
        
        return {'success': False, 'error': 'Invalid credentials'}
    
    @staticmethod
    def logout_user(request):
        """Logout user"""
        if current_user.is_authenticated:
            log = ActivityLog(
                user_id=current_user.id,
                username=current_user.username,
                action='logout',
                details=f'User {current_user.username} logged out',
                ip_address=request.remote_addr
            )
            from models import db
            db.session.add(log)
            db.session.commit()
        
        logout_user()
        return {'success': True}
    
    @staticmethod
    def get_user_permissions(user):
        """Get user permissions"""
        if not user.is_authenticated:
            return {}
        
        return {
            'can_view': user.has_permission('view'),
            'can_add': user.has_permission('add'),
            'can_edit_all': user.has_permission('edit_all'),
            'can_edit_limited': user.has_permission('edit_limited'),
            'can_delete': user.has_permission('delete'),
            'can_manage_users': user.has_permission('manage_users'),
            'can_manage_fields': user.has_permission('manage_fields')
        }