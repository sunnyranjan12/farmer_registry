# routes/farmers.py
from flask import request, jsonify
from flask_login import login_required, current_user
from routes import farmers_bp
from services.farmer_service import FarmerService
from models import Farmer, CustomField, db
from config import config
import os
import pandas as pd
import io
from werkzeug.utils import secure_filename

@farmers_bp.route('/farmers', methods=['GET'])
@login_required
def get_farmers():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', config['default'].ITEMS_PER_PAGE, type=int)
    search = request.args.get('search', '')
    village = request.args.get('village', '')
    status = request.args.get('status', '')
    sort_by = request.args.get('sort_by', 'sn')
    sort_order = request.args.get('sort_order', 'asc')
    
    result = FarmerService.get_farmers_paginated(
        page, per_page, search, village, status, sort_by, sort_order
    )
    return jsonify(result)

@farmers_bp.route('/farmer/<int:id>', methods=['GET'])
@login_required
def get_farmer(id):
    farmer = Farmer.query.get_or_404(id)
    return jsonify(farmer.to_dict())

@farmers_bp.route('/farmer', methods=['POST'])
@login_required
def create_farmer():
    if not current_user.has_permission('add'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    print("=" * 50)
    print("Received POST data for new farmer:")
    print(data)
    print("=" * 50)
    
    # Validate required fields
    if not data.get('farmer_name'):
        return jsonify({'error': 'Farmer name is required'}), 400
    if not data.get('village_name'):
        return jsonify({'error': 'Village name is required'}), 400
    
    try:
        farmer = FarmerService.create_farmer(data, current_user)
        print(f"Farmer created successfully with ID: {farmer.id}, SN: {farmer.sn}")
        return jsonify({'success': True, 'id': farmer.id, 'sn': farmer.sn})
    except Exception as e:
        print(f"Error creating farmer: {str(e)}")
        return jsonify({'error': str(e)}), 500

@farmers_bp.route('/farmer/<int:id>', methods=['PUT'])
@login_required
def update_farmer(id):
    if not (current_user.has_permission('edit_all') or current_user.has_permission('edit_limited')):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    farmer = FarmerService.update_farmer(id, data, current_user)
    return jsonify({'success': True})

@farmers_bp.route('/farmer/<int:id>', methods=['DELETE'])
@login_required
def delete_farmer(id):
    if not current_user.has_permission('delete'):
        return jsonify({'error': 'Permission denied'}), 403
    
    FarmerService.delete_farmer(id, current_user)
    return jsonify({'success': True})

@farmers_bp.route('/villages')
@login_required
def get_villages():
    villages = FarmerService.get_all_villages()
    return jsonify(villages)

@farmers_bp.route('/custom-fields-active')
@login_required
def get_active_custom_fields():
    """Get active custom fields for form display"""
    fields = CustomField.query.filter_by(is_active=True).order_by(CustomField.display_order).all()
    return jsonify([f.to_dict() for f in fields])

@farmers_bp.route('/bulk-upload', methods=['POST'])
@login_required
def bulk_upload():
    from flask import current_app
    if not current_user.has_permission('bulk_upload'):
        return jsonify({'error': 'Permission denied'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Create uploads folder if not exists
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    result = FarmerService.bulk_upload_farmers(filepath, current_user)
    
    # Clean up uploaded file
    try:
        os.remove(filepath)
    except:
        pass
    
    return jsonify(result)

@farmers_bp.route('/download-template')
@login_required
def download_template():
    df = FarmerService.download_template()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Template', index=False)
    output.seek(0)
    
    from flask import send_file
    return send_file(
        output, 
        as_attachment=True, 
        download_name='farmer_upload_template.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )