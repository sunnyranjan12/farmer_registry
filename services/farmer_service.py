# services/farmer_service.py
from models import Farmer, CustomField, ActivityLog, db
from datetime import datetime
import json
import pandas as pd
import os

class FarmerService:
    
    @staticmethod
    def get_next_sn():
        max_sn = db.session.query(db.func.max(Farmer.sn)).scalar()
        return (max_sn or 0) + 1
    
    @staticmethod
    def create_farmer(data, current_user):
        print("Creating farmer with data:", data)  # Debug print
        
        # Handle empty strings as None for numeric fields
        land_area = data.get('land_area')
        if land_area == '' or land_area is None:
            land_area = None
        else:
            try:
                land_area = float(land_area)
            except (ValueError, TypeError):
                land_area = None
        
        farmer = Farmer(
            sn=FarmerService.get_next_sn(),
            sub_district_name=data.get('sub_district_name', 'Ghazipur'),
            village_name=data.get('village_name', ''),
            farmer_name=data.get('farmer_name', ''),
            father_name=data.get('father_name', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            aadhar_number=data.get('aadhar_number', ''),
            bank_account=data.get('bank_account', ''),
            ifsc_code=data.get('ifsc_code', ''),
            land_area=land_area,
            crop_type=data.get('crop_type', ''),
            verification_status='pending',
            created_by=current_user.username,
            custom_fields=json.dumps(data.get('custom_fields', {}))
        )
        
        db.session.add(farmer)
        db.session.commit()
        
        print(f"Farmer saved with ID: {farmer.id}, SN: {farmer.sn}")  # Debug print
        
        FarmerService._log_activity(current_user.id, current_user.username, 
                                     'create_farmer', f'Created farmer: {farmer.farmer_name} (SN: {farmer.sn})')
        
        return farmer
    
    @staticmethod
    def update_farmer(farmer_id, data, current_user):
        farmer = Farmer.query.get_or_404(farmer_id)
        
        if current_user.role == 'viewer':
            if 'phone' in data:
                farmer.phone = data['phone']
            if 'email' in data:
                farmer.email = data['email']
        else:
            farmer.village_name = data.get('village_name', farmer.village_name)
            farmer.farmer_name = data.get('farmer_name', farmer.farmer_name)
            farmer.father_name = data.get('father_name', farmer.father_name)
            farmer.phone = data.get('phone', farmer.phone)
            farmer.email = data.get('email', farmer.email)
            farmer.aadhar_number = data.get('aadhar_number', farmer.aadhar_number)
            farmer.bank_account = data.get('bank_account', farmer.bank_account)
            farmer.ifsc_code = data.get('ifsc_code', farmer.ifsc_code)
            
            land_area = data.get('land_area')
            if land_area == '' or land_area is None:
                farmer.land_area = None
            else:
                try:
                    farmer.land_area = float(land_area)
                except (ValueError, TypeError):
                    pass
            
            farmer.crop_type = data.get('crop_type', farmer.crop_type)
            
            if 'verification_status' in data and current_user.role == 'admin':
                farmer.verification_status = data['verification_status']
                farmer.verified_by = current_user.username
                farmer.verified_date = datetime.utcnow()
            
            farmer.custom_fields = json.dumps(data.get('custom_fields', {}))
        
        farmer.updated_at = datetime.utcnow()
        db.session.commit()
        
        FarmerService._log_activity(current_user.id, current_user.username,
                                     'update_farmer', f'Updated farmer: {farmer.farmer_name} (SN: {farmer.sn})')
        
        return farmer
    
    @staticmethod
    def delete_farmer(farmer_id, current_user):
        farmer = Farmer.query.get_or_404(farmer_id)
        
        FarmerService._log_activity(current_user.id, current_user.username,
                                     'delete_farmer', f'Deleted farmer: {farmer.farmer_name} (SN: {farmer.sn})')
        
        db.session.delete(farmer)
        db.session.commit()
        return True
    
    @staticmethod
    def get_farmers_paginated(page, per_page, search='', village='', status='', sort_by='sn', sort_order='asc'):
        query = Farmer.query
        
        if search:
            query = query.filter(
                db.or_(
                    Farmer.farmer_name.contains(search),
                    Farmer.father_name.contains(search),
                    Farmer.village_name.contains(search),
                    Farmer.phone.contains(search)
                )
            )
        if village:
            query = query.filter_by(village_name=village)
        if status:
            query = query.filter_by(verification_status=status)
        
        if sort_order == 'asc':
            query = query.order_by(getattr(Farmer, sort_by).asc())
        else:
            query = query.order_by(getattr(Farmer, sort_by).desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'items': [f.to_dict() for f in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page
        }
    
    @staticmethod
    def get_all_farmers():
        """Get all farmers for export"""
        return Farmer.query.order_by(Farmer.sn).all()
    
    @staticmethod
    def get_all_villages():
        villages = db.session.query(Farmer.village_name).distinct().order_by(Farmer.village_name).all()
        return [v[0] for v in villages if v[0]]
    
    @staticmethod
    def get_dashboard_stats():
        total = Farmer.query.count()
        verified = Farmer.query.filter_by(verification_status='verified').count()
        pending = Farmer.query.filter_by(verification_status='pending').count()
        
        village_stats = db.session.query(
            Farmer.village_name, db.func.count(Farmer.id)
        ).group_by(Farmer.village_name).all()
        
        return {
            'total_farmers': total,
            'verified_farmers': verified,
            'pending_farmers': pending,
            'village_stats': [{'village': v[0], 'count': v[1]} for v in village_stats]
        }
    
    @staticmethod
    def bulk_upload_farmers(file_path, current_user):
        """Bulk upload farmers from Excel/CSV file"""
        try:
            # Read file based on extension
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            success_count = 0
            error_count = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    # Try different possible column names
                    farmer_name = None
                    village_name = None
                    father_name = ''
                    phone = ''
                    email = ''
                    
                    for col in df.columns:
                        col_lower = col.lower()
                        if 'farmer' in col_lower and 'name' in col_lower:
                            farmer_name = str(row[col]) if not pd.isna(row[col]) else ''
                        if 'village' in col_lower:
                            village_name = str(row[col]) if not pd.isna(row[col]) else ''
                        if 'father' in col_lower:
                            father_name = str(row[col]) if not pd.isna(row[col]) else ''
                        if 'phone' in col_lower:
                            phone = str(row[col]) if not pd.isna(row[col]) else ''
                        if 'email' in col_lower:
                            email = str(row[col]) if not pd.isna(row[col]) else ''
                    
                    # If column detection failed, use index positions
                    if not farmer_name and len(df.columns) > 0:
                        farmer_name = str(row[df.columns[0]]) if not pd.isna(row[df.columns[0]]) else ''
                    if not village_name and len(df.columns) > 1:
                        village_name = str(row[df.columns[1]]) if not pd.isna(row[df.columns[1]]) else ''
                    
                    if not farmer_name or farmer_name == 'nan':
                        error_count += 1
                        errors.append(f"Row {idx+2}: Farmer Name is required")
                        continue
                    
                    if not village_name or village_name == 'nan':
                        village_name = 'Unknown'
                    
                    farmer = Farmer(
                        sn=FarmerService.get_next_sn(),
                        sub_district_name='Ghazipur',
                        village_name=village_name,
                        farmer_name=farmer_name,
                        father_name=father_name if father_name != 'nan' else '',
                        phone=phone if phone != 'nan' else '',
                        email=email if email != 'nan' else '',
                        verification_status='pending',
                        created_by=current_user.username
                    )
                    db.session.add(farmer)
                    success_count += 1
                    
                    # Commit every 100 records
                    if success_count % 100 == 0:
                        db.session.commit()
                        
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {idx+2}: {str(e)}")
            
            db.session.commit()
            
            FarmerService._log_activity(current_user.id, current_user.username,
                                         'bulk_upload', f'Bulk uploaded {success_count} farmers, {error_count} errors')
            
            return {
                'success': True,
                'uploaded': success_count,
                'errors': error_count,
                'error_details': errors[:20]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def download_template():
        """Download Excel template for bulk upload"""
        template_data = {
            'Farmer Name': ['John Doe'],
            'Village Name': ['Example Village'],
            'Father Name': ['Father Name'],
            'Phone': ['1234567890'],
            'Email': ['example@email.com'],
            'Aadhar Number': ['123456789012'],
            'Bank Account': ['1234567890'],
            'IFSC Code': ['SBIN0012345'],
            'Land Area (acres)': [2.5],
            'Crop Type': ['Wheat']
        }
        df = pd.DataFrame(template_data)
        return df
    
    @staticmethod
    def _log_activity(user_id, username, action, details):
        log = ActivityLog(
            user_id=user_id,
            username=username,
            action=action,
            details=details,
            ip_address=''
        )
        db.session.add(log)
        db.session.commit()