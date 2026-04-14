# models.py - Database models
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='viewer')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        permissions = {
            'view': ['viewer', 'editor', 'admin'],
            'add': ['editor', 'admin'],
            'edit_all': ['editor', 'admin'],
            'edit_limited': ['viewer'],  # Can edit only phone/email
            'delete': ['admin'],
            'manage_users': ['admin'],
            'manage_fields': ['admin']
        }
        return self.role in permissions.get(permission, [])

class Farmer(db.Model):
    __tablename__ = 'farmers'
    
    id = db.Column(db.Integer, primary_key=True)
    sn = db.Column(db.Integer, nullable=False)
    sub_district_name = db.Column(db.String(100), nullable=False, default='Ghazipur')
    village_name = db.Column(db.String(100), nullable=False)
    farmer_name = db.Column(db.String(200), nullable=False)
    father_name = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    aadhar_number = db.Column(db.String(20))
    bank_account = db.Column(db.String(30))
    ifsc_code = db.Column(db.String(20))
    land_area = db.Column(db.Float)
    crop_type = db.Column(db.String(100))
    verification_status = db.Column(db.String(50), default='pending')
    verified_by = db.Column(db.String(100))
    verified_date = db.Column(db.DateTime)
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    custom_fields = db.Column(db.Text, default='{}')
    
    def get_custom_fields(self):
        return json.loads(self.custom_fields) if self.custom_fields else {}
    
    def set_custom_fields(self, data):
        self.custom_fields = json.dumps(data)
    
    def to_dict(self, include_custom=True):
        data = {
            'id': self.id,
            'sn': self.sn,
            'sub_district_name': self.sub_district_name,
            'village_name': self.village_name,
            'farmer_name': self.farmer_name,
            'father_name': self.father_name,
            'phone': self.phone,
            'email': self.email,
            'aadhar_number': self.aadhar_number,
            'bank_account': self.bank_account,
            'ifsc_code': self.ifsc_code,
            'land_area': self.land_area,
            'crop_type': self.crop_type,
            'verification_status': self.verification_status,
            'verified_by': self.verified_by,
            'verified_date': self.verified_date.isoformat() if self.verified_date else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_custom:
            data['custom_fields'] = self.get_custom_fields()
        return data

class CustomField(db.Model):
    __tablename__ = 'custom_fields'
    
    id = db.Column(db.Integer, primary_key=True)
    field_name = db.Column(db.String(100), nullable=False)
    field_label = db.Column(db.String(100), nullable=False)
    field_type = db.Column(db.String(50), default='text')
    is_mandatory = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'field_name': self.field_name,
            'field_label': self.field_label,
            'field_type': self.field_type,
            'is_mandatory': self.is_mandatory
        }

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    username = db.Column(db.String(80))
    action = db.Column(db.String(200))
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'action': self.action,
            'details': self.details,
            'time': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }