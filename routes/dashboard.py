# routes/dashboard.py
from flask import render_template, jsonify
from flask_login import login_required, current_user
from routes import dashboard_bp
from services.farmer_service import FarmerService
from models import ActivityLog

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@dashboard_bp.route('/api/dashboard-stats')
@login_required
def dashboard_stats():
    stats = FarmerService.get_dashboard_stats()
    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    
    return jsonify({
        **stats,
        'recent_activities': [log.to_dict() for log in recent_logs]
    })