# routes/__init__.py - Route blueprints registration
from flask import Blueprint

# Create blueprints
auth_bp = Blueprint('auth', __name__)
farmers_bp = Blueprint('farmers', __name__, url_prefix='/api')
dashboard_bp = Blueprint('dashboard', __name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/api')
export_bp = Blueprint('export', __name__, url_prefix='/api')

# Import routes (will be defined in separate files)
from routes import auth, farmers, dashboard, admin, export
