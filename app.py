from flask import Flask
from flask_login import LoginManager
from models import db, User
from config import config
import os

app = Flask(__name__)
app.config.from_object(config['development'])

# folders
os.makedirs("instance", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# register routes
from routes import auth_bp, farmers_bp, dashboard_bp, admin_bp, export_bp

app.register_blueprint(auth_bp)
app.register_blueprint(farmers_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(export_bp)

def init_db():
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", email="admin@test.com", role="admin")
            admin.set_password("Admin@123")
            db.session.add(admin)

        db.session.commit()

if __name__ == "__main__":
    init_db()
    import os

port = int(os.environ.get("PORT", 5000))

app.run(host="0.0.0.0", port=port)