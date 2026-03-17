# app/database/postgres_client.py

"""
PostgreSQL client for database operations
"""

import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from .models import Base, Declaration

class PostgresClient:
    """PostgreSQL database client"""
    
    def __init__(self, connection_string=None):
        """
        Initialize database connection
        connection_string: postgresql://user:pass@localhost/dbname
        """
        if connection_string is None:
            # Default for development - UPDATE WITH YOUR CREDENTIALS
            connection_string = "postgresql://postgres:postgres@localhost:5432/compliance_db"
        
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
    
    def create_declaration(self, declaration_number, declaration_date=None):
        """Create a new declaration record"""
        session = self.Session()
        try:
            decl = Declaration(
                declaration_number=declaration_number,
                declaration_date=declaration_date,
                status='IN_PROGRESS'
            )
            session.add(decl)
            session.commit()
            return decl.id
        except IntegrityError:
            session.rollback()
            # Declaration might already exist
            existing = session.query(Declaration).filter_by(
                declaration_number=declaration_number
            ).first()
            return existing.id if existing else None
        finally:
            session.close()
    
    def update_document(self, declaration_number, doc_type, file_data):
        """Update document information for a declaration"""
        session = self.Session()
        try:
            decl = session.query(Declaration).filter_by(
                declaration_number=declaration_number
            ).first()
            
            if not decl:
                return False
            
            # Map document type to database columns
            doc_mappings = {
                'declaration': {
                    'file_name': 'declaration_file_name',
                    'file_path': 'declaration_file_path',
                    'data': 'declaration_data',
                    'validation': 'declaration_validation'
                },
                'invoice': {
                    'file_name': 'invoice_file_name',
                    'file_path': 'invoice_file_path',
                    'data': 'invoice_data',
                    'validation': 'invoice_validation',
                    'number': 'invoice_number',
                    'value': 'invoice_value',
                    'currency': 'invoice_currency'
                },
                'packing_list': {
                    'file_name': 'packing_list_file_name',
                    'file_path': 'packing_list_file_path',
                    'data': 'packing_list_data',
                    'validation': 'packing_list_validation',
                    'number': 'packing_list_number',
                    'packages': 'total_packages',
                    'weight': 'gross_weight'
                },
                'bol_aws': {
                    'file_name': 'bol_file_name',
                    'file_path': 'bol_file_path',
                    'data': 'bol_data',
                    'validation': 'bol_validation',
                    'number': 'bol_number',
                    'flight': 'vessel_flight_number'
                },
                'country_of_origin': {
                    'file_name': 'coo_file_name',
                    'file_path': 'coo_file_path',
                    'data': 'coo_data',
                    'validation': 'coo_validation',
                    'number': 'coo_number',
                    'country': 'origin_country',
                    'invoice_ref': 'referenced_invoice'
                },
                'delivery_order': {
                    'file_name': 'delivery_order_file_name',
                    'file_path': 'delivery_order_file_path',
                    'data': 'delivery_order_data',
                    'validation': 'delivery_order_validation',
                    'number': 'delivery_order_number'
                }
            }
            
            if doc_type not in doc_mappings:
                return False
            
            mapping = doc_mappings[doc_type]
            
            # Set file info
            setattr(decl, mapping['file_name'], file_data.get('filename'))
            setattr(decl, mapping['file_path'], file_data.get('file_path'))
            setattr(decl, mapping['data'], file_data.get('extracted_data', {}))
            setattr(decl, mapping['validation'], file_data.get('validation', {}))
            
            # Set specific fields based on extracted data
            extracted = file_data.get('extracted_data', {})
            
            if doc_type == 'invoice':
                if 'invoice_number' in extracted:
                    decl.invoice_number = extracted['invoice_number']
                if 'total_value' in extracted:
                    decl.invoice_value = float(extracted['total_value'])
                if 'currency' in extracted:
                    decl.invoice_currency = extracted['currency']
                    
            elif doc_type == 'packing_list':
                if 'packing_list_number' in extracted:
                    decl.packing_list_number = extracted['packing_list_number']
                if 'total_packages' in extracted:
                    decl.total_packages = int(extracted['total_packages'])
                if 'gross_weight' in extracted:
                    decl.gross_weight = float(extracted['gross_weight'])
                    
            elif doc_type == 'bol_aws':
                if 'bol_number' in extracted:
                    decl.bol_number = extracted['bol_number']
                if 'vessel_flight_number' in extracted:
                    decl.vessel_flight_number = extracted['vessel_flight_number']
                    
            elif doc_type == 'country_of_origin':
                if 'coo_number' in extracted:
                    decl.coo_number = extracted['coo_number']
                if 'origin_country' in extracted:
                    decl.origin_country = extracted['origin_country']
                if 'referenced_invoice' in extracted:
                    decl.referenced_invoice = extracted['referenced_invoice']
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Database error: {e}")
            return False
        finally:
            session.close()
    
    def complete_declaration(self, declaration_number):
        """Mark declaration as completed and submitted"""
        session = self.Session()
        try:
            decl = session.query(Declaration).filter_by(
                declaration_number=declaration_number
            ).first()
            
            if decl:
                decl.status = 'SUBMITTED'
                decl.completed_at = datetime.utcnow()
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def get_declaration(self, declaration_number):
        """Retrieve declaration by number"""
        session = self.Session()
        try:
            decl = session.query(Declaration).filter_by(
                declaration_number=declaration_number
            ).first()
            
            if decl:
                return {
                    'id': decl.id,
                    'declaration_number': decl.declaration_number,
                    'status': decl.status,
                    'documents': {
                        'declaration': {
                            'file_name': decl.declaration_file_name,
                            'data': decl.declaration_data
                        } if decl.declaration_file_name else None,
                        'invoice': {
                            'file_name': decl.invoice_file_name,
                            'data': decl.invoice_data,
                            'number': decl.invoice_number,
                            'value': decl.invoice_value
                        } if decl.invoice_file_name else None,
                        # ... etc for other docs
                    }
                }
            return None
        finally:
            session.close() 