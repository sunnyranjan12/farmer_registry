# routes/export.py
from flask import send_file, request, jsonify
from flask_login import login_required, current_user
from routes import export_bp
from services.farmer_service import FarmerService
from models import ActivityLog, db
import pandas as pd
import io
from datetime import datetime

@export_bp.route('/export-excel')
@login_required
def export_excel():
    farmers = FarmerService.get_all_farmers()
    
    data = []
    for f in farmers:
        custom = f.get_custom_fields()
        row = {
            'SN': f.sn,
            'Sub District': f.sub_district_name,
            'Village': f.village_name,
            'Farmer Name': f.farmer_name,
            'Father Name': f.father_name,
            'Phone': f.phone,
            'Email': f.email,
            'Aadhar Number': f.aadhar_number,
            'Bank Account': f.bank_account,
            'IFSC Code': f.ifsc_code,
            'Land Area (acre)': f.land_area,
            'Crop Type': f.crop_type,
            'Verification Status': f.verification_status,
            'Verified By': f.verified_by,
            'Verified Date': f.verified_date.strftime('%Y-%m-%d') if f.verified_date else '',
            'Created By': f.created_by,
            'Created At': f.created_at.strftime('%Y-%m-%d %H:%M') if f.created_at else ''
        }
        for key, value in custom.items():
            row[key] = value
        data.append(row)
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Farmers', index=False)
    
    output.seek(0)
    
    log = ActivityLog(
        user_id=current_user.id,
        username=current_user.username,
        action='export_excel',
        details=f'Exported {len(farmers)} farmers to Excel',
        ip_address=''
    )
    db.session.add(log)
    db.session.commit()
    
    return send_file(
        output, 
        download_name=f'farmers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx', 
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@export_bp.route('/export-filtered')
@login_required
def export_filtered():
    """Export filtered data"""
    search = request.args.get('search', '')
    village = request.args.get('village', '')
    status = request.args.get('status', '')
    
    result = FarmerService.get_farmers_paginated(1, 10000, search, village, status)
    farmers = result['items']
    
    data = []
    for f in farmers:
        row = {
            'SN': f.get('sn'),
            'Village': f.get('village_name'),
            'Farmer Name': f.get('farmer_name'),
            'Father Name': f.get('father_name'),
            'Phone': f.get('phone'),
            'Email': f.get('email'),
            'Status': f.get('verification_status')
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Filtered_Farmers', index=False)
    
    output.seek(0)
    
    return send_file(
        output, 
        download_name=f'filtered_farmers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx', 
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )