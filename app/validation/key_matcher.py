from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import re
from datetime import datetime

@dataclass
class ValidationResult:
    """Structured validation result"""
    status: str  # 'success' or 'error'
    mismatches: List[Dict[str, Any]] = field(default_factory=list)
    missing_documents: List[str] = field(default_factory=list)
    declaration_number: Optional[str] = None
    document_specific_errors: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

class ValidationEngine:
    """Core validation engine for document compliance"""
    
    def __init__(self):
        self.declaration_pattern = re.compile(r'^DEC-\d{4}-\d{6}$')  # Example pattern
        self.primary_key_fields = {
            'declaration': ['declaration_number', 'consignee', 'exporter'],
            'invoice': ['invoice_number', 'declaration_number', 'total_amount'],
            'packing_list': ['packing_list_number', 'declaration_number', 'total_packages'],
            'bol_aws': ['bol_number', 'declaration_number', 'vessel_name'],
            'country_of_origin': ['certificate_number', 'declaration_number', 'country'],
            'delivery_order': ['do_number', 'declaration_number', 'consignee']
        }
    
    def validate_all_documents(self, 
                               declaration_number: str, 
                               uploaded_documents: Dict[str, Dict[str, Any]]) -> ValidationResult:
        """
        Comprehensive validation of all uploaded documents
        """
        result = ValidationResult()
        
        # Step 1: Check for missing mandatory documents
        result.missing_documents = self._check_missing_documents(uploaded_documents)
        if result.missing_documents:
            result.status = 'error'
            return result
        
        # Step 2: Validate declaration number format
        if not self._validate_declaration_format(declaration_number):
            result.status = 'error'
            result.document_specific_errors['declaration'] = ['Invalid declaration number format']
            return result
        
        result.declaration_number = declaration_number
        
        # Step 3: Validate each document individually
        for doc_id, doc_data in uploaded_documents.items():
            doc_errors = self._validate_single_document(doc_data)
            if doc_errors:
                result.document_specific_errors[doc_data['document_type']] = doc_errors
                result.status = 'error'
        
        # Step 4: Check primary key consistency across documents
        mismatches = self._check_primary_key_consistency(declaration_number, uploaded_documents)
        if mismatches:
            result.mismatches = mismatches
            result.status = 'error'
        
        # If no errors found, set status to success
        if result.status != 'error':
            result.status = 'success'
        
        return result
    
    def _check_missing_documents(self, uploaded_documents: Dict[str, Dict[str, Any]]) -> List[str]:
        """Check for missing mandatory documents"""
        mandatory_docs = [
            'declaration', 'invoice', 'packing_list', 
            'bol_aws', 'country_of_origin', 'delivery_order'
        ]
        
        uploaded_types = {doc['document_type'] for doc in uploaded_documents.values()}
        missing = [doc for doc in mandatory_docs if doc not in uploaded_types]
        
        return missing
    
    def _validate_declaration_format(self, declaration_number: str) -> bool:
        """Validate declaration number format"""
        if not declaration_number:
            return False
        
        # Mock validation - in production, this would be more sophisticated
        return bool(self.declaration_pattern.match(declaration_number))
    
    def _validate_single_document(self, document_data: Dict[str, Any]) -> List[str]:
        """Validate individual document format and required fields"""
        errors = []
        doc_type = document_data.get('document_type')
        extracted_data = document_data.get('extracted_data', {})
        
        # Check if document has required fields based on type
        required_fields = self.primary_key_fields.get(doc_type, [])
        
        for field in required_fields:
            if field not in extracted_data or not extracted_data[field]:
                errors.append(f"Missing required field: {field}")
        
        return errors
    
    def _check_primary_key_consistency(self, 
                                        declaration_number: str, 
                                        uploaded_documents: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check if primary keys match across all documents
        Returns list of mismatches found
        """
        mismatches = []
        
        # All documents should reference the same declaration number
        for doc_id, doc_data in uploaded_documents.items():
            doc_type = doc_data['document_type']
            extracted_data = doc_data.get('extracted_data', {})
            
            # Check declaration number in each document
            doc_decl_number = extracted_data.get('declaration_number')
            
            if doc_decl_number and doc_decl_number != declaration_number:
                mismatches.append({
                    'document_type': doc_type,
                    'document_id': doc_id,
                    'field': 'declaration_number',
                    'expected': declaration_number,
                    'found': doc_decl_number,
                    'severity': 'high'
                })
            
            # Additional cross-document consistency checks
            if doc_type == 'invoice':
                self._check_invoice_consistency(doc_data, uploaded_documents, mismatches)
            elif doc_type == 'packing_list':
                self._check_packing_list_consistency(doc_data, uploaded_documents, mismatches)
        
        return mismatches
    
    def _check_invoice_consistency(self, 
                                    invoice_data: Dict[str, Any], 
                                    all_documents: Dict[str, Dict[str, Any]], 
                                    mismatches: List[Dict[str, Any]]):
        """Check invoice consistency with other documents"""
        invoice_extracted = invoice_data.get('extracted_data', {})
        
        # Check against packing list
        for doc_id, doc_data in all_documents.items():
            if doc_data['document_type'] == 'packing_list':
                packing_extracted = doc_data.get('extracted_data', {})
                
                # Total amount should match
                if invoice_extracted.get('total_amount') != packing_extracted.get('total_value'):
                    mismatches.append({
                        'document_type': 'invoice_vs_packing',
                        'field': 'total_amount',
                        'expected': packing_extracted.get('total_value'),
                        'found': invoice_extracted.get('total_amount'),
                        'severity': 'medium'
                    })
    
    def _check_packing_list_consistency(self, 
                                         packing_data: Dict[str, Any], 
                                         all_documents: Dict[str, Dict[str, Any]], 
                                         mismatches: List[Dict[str, Any]]):
        """Check packing list consistency with other documents"""
        packing_extracted = packing_data.get('extracted_data', {})
        
        # Check against BOL/AWS
        for doc_id, doc_data in all_documents.items():
            if doc_data['document_type'] == 'bol_aws':
                bol_extracted = doc_data.get('extracted_data', {})
                
                # Package count should match
                if packing_extracted.get('total_packages') != bol_extracted.get('package_count'):
                    mismatches.append({
                        'document_type': 'packing_vs_bol',
                        'field': 'package_count',
                        'expected': bol_extracted.get('package_count'),
                        'found': packing_extracted.get('total_packages'),
                        'severity': 'high'
                    })

# app/validation/key_matcher.py

class PrimaryKeyMatcher:
    """Advanced primary key matching across documents"""
    
    def __init__(self):
        self.key_hierarchies = {
            'primary': ['declaration_number', 'shipment_id', 'container_number'],
            'secondary': ['invoice_number', 'bol_number', 'do_number'],
            'tertiary': ['consignee', 'exporter', 'vessel_name']
        }
    
    def match_documents(self, documents: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform hierarchical matching of document keys
        Returns matching results with confidence scores
        """
        results = {
            'matched_keys': {},
            'conflicts': [],
            'confidence_score': 1.0
        }
        
        # Extract all keys from documents
        all_keys = self._extract_all_keys(documents)
        
        # Check primary key consistency
        primary_keys = all_keys.get('primary', [])
        if len(set(primary_keys)) > 1:
            results['conflicts'].append({
                'level': 'primary',
                'keys': list(set(primary_keys)),
                'severity': 'critical'
            })
            results['confidence_score'] *= 0.3
        elif primary_keys:
            results['matched_keys']['primary'] = primary_keys[0]
        
        # Check secondary keys
        secondary_keys = all_keys.get('secondary', [])
        if len(set(secondary_keys)) > 1:
            results['conflicts'].append({
                'level': 'secondary',
                'keys': list(set(secondary_keys)),
                'severity': 'high'
            })
            results['confidence_score'] *= 0.7
        
        return results
    
    def _extract_all_keys(self, documents: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """Extract all keys from documents by hierarchy level"""
        extracted = {
            'primary': [],
            'secondary': [],
            'tertiary': []
        }
        
        for doc_id, doc_data in documents.items():
            extracted_data = doc_data.get('extracted_data', {})
            
            for level, keys in self.key_hierarchies.items():
                for key in keys:
                    if key in extracted_data and extracted_data[key]:
                        extracted[level].append(str(extracted_data[key]))
        
        return extracted