# app/database/models.py

"""
PostgreSQL database models for declarations
Run: pip install sqlalchemy psycopg2-binary
"""

from sqlalchemy import create_engine, Column, String, DateTime, Integer, Float, JSON, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

Base = declarative_base()

class Declaration(Base):
    """Main declarations table"""
    __tablename__ = 'declarations'
    
    # Primary Key
    id = Column(Integer, primary_key=True)
    declaration_number = Column(String(20), unique=True, nullable=False, index=True)
    declaration_date = Column(DateTime)
    status = Column(String(20), default='IN_PROGRESS')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_by = Column(String(100))
    submitted_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Declaration File
    declaration_file_name = Column(String(255))
    declaration_file_path = Column(Text)
    declaration_data = Column(JSONB)
    declaration_validation = Column(JSONB)
    
    # Invoice
    invoice_file_name = Column(String(255))
    invoice_file_path = Column(Text)
    invoice_number = Column(String(50))
    invoice_date = Column(DateTime)
    invoice_value = Column(Float)
    invoice_currency = Column(String(3))
    invoice_data = Column(JSONB)
    invoice_validation = Column(JSONB)
    
    # Packing List
    packing_list_file_name = Column(String(255))
    packing_list_file_path = Column(Text)
    packing_list_number = Column(String(50))
    total_packages = Column(Integer)
    gross_weight = Column(Float)
    packing_list_data = Column(JSONB)
    packing_list_validation = Column(JSONB)
    
    # BOL/AWS
    bol_file_name = Column(String(255))
    bol_file_path = Column(Text)
    bol_number = Column(String(50))
    vessel_flight_number = Column(String(50))
    port_of_loading = Column(String(100))
    port_of_discharge = Column(String(100))
    bol_data = Column(JSONB)
    bol_validation = Column(JSONB)
    
    # Country of Origin
    coo_file_name = Column(String(255))
    coo_file_path = Column(Text)
    coo_number = Column(String(50))
    origin_country = Column(String(100))
    referenced_invoice = Column(String(50))
    coo_data = Column(JSONB)
    coo_validation = Column(JSONB)
    
    # Delivery Order
    delivery_order_file_name = Column(String(255))
    delivery_order_file_path = Column(Text)
    delivery_order_number = Column(String(50))
    delivery_order_data = Column(JSONB)
    delivery_order_validation = Column(JSONB)


# Create indexes for better performance
Index('idx_declaration_number', Declaration.declaration_number)
Index('idx_status', Declaration.status)
Index('idx_created_at', Declaration.created_at)
Index('idx_invoice_number', Declaration.invoice_number)