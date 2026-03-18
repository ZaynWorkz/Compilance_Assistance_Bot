
"""
Smart validator that handles mandatory and optional documents
"""

from typing import Dict, Any, List, Tuple

class SmartValidator:
    """
    Validates documents intelligently:
    - Mandatory: Declaration, Invoice, COO, MAWB
    - Optional: Packing List, Delivery Order
    - Chain validation: COO must reference correct invoice
    """
    
    # app/validation/smart_validator.py - Update

class SmartValidator:
    def __init__(self):
        self.mandatory_docs = ['declaration', 'invoice', 'coo', 'mawb']
        self.optional_docs = ['packing_list', 'delivery_order']
    
    def validate(self, documents: Dict[str, Any]) -> Dict[str, Any]:

        result = {
            'status': 'success',
            'missing_mandatory': [],
            'missing_optional': [],
            'mismatches': [],
            'chain_valid': True,
            'summary': {}
        }
        
        # Check mandatory docs
        uploaded_types = list(documents.keys())
        for doc in self.mandatory_docs:
            if doc not in uploaded_types:
                result['missing_mandatory'].append(doc)
                result['chain_valid'] = False
        
        if result['missing_mandatory']:
            result['status'] = 'incomplete'
            return result
        
        # Run all consistency checks
        self._check_coo_invoice_chain(documents, result)
        self._check_hs_codes(documents, result)
        self._check_origin(documents, result)
        self._check_mawb_consistency(documents, result)  # ✅ NEW CHECK
        
        # Determine final status
        if not result['chain_valid']:
            result['status'] = 'failed'
        elif result['mismatches']:
            result['status'] = 'warning'
        else:
            result['status'] = 'success'
        
        return result

    def _check_mawb_consistency(self, documents, result):
        """Check MAWB consistency with other documents"""   
        
        if 'mawb' not in documents:
            return
        
        mawb_data = documents['mawb'].get('extracted_data', {})
        
        # Check against BOE if available
        if 'declaration' in documents:
            boe_data = documents['declaration'].get('extracted_data', {})
            
            # Flight number consistency
            boe_flight = boe_data.get('flight_number') or boe_data.get('vessel_flight_number')
            mawb_flight = mawb_data.get('flight_number')
            
            if boe_flight and mawb_flight and boe_flight != mawb_flight:
                result['mismatches'].append({
                    'type': 'flight_mismatch',
                    'severity': 'high',
                    'message': f'Flight mismatch: BOE says {boe_flight}, MAWB says {mawb_flight}'
                })
            
            # Packages consistency
            boe_packages = boe_data.get('packages') or boe_data.get('total_packages')
            mawb_packages = mawb_data.get('packages')
            
            if boe_packages and mawb_packages and boe_packages != mawb_packages:
                result['mismatches'].append({
                    'type': 'packages_mismatch',
                    'severity': 'medium',
                    'message': f'Package count mismatch: BOE says {boe_packages}, MAWB says {mawb_packages}'
                })
        
        # Check consignee consistency
        if 'consignee' in mawb_data:
            consignee = mawb_data['consignee']
            for doc_type in ['declaration', 'invoice', 'coo']:
                if doc_type in documents:
                    other_consignee = documents[doc_type].get('extracted_data', {}).get('consignee')
                    if other_consignee and other_consignee != consignee:
                        result['mismatches'].append({
                            'type': 'consignee_mismatch',
                            'severity': 'high',
                            'message': f'Consignee mismatch: {doc_type} says {other_consignee}, MAWB says {consignee}'
                        })

    def _check_hs_codes(self, documents: Dict, result: Dict):
        """Check HS code consistency between declaration and invoice"""
        if 'declaration' not in documents or 'invoice' not in documents:
            return
        
        decl_data = documents['declaration'].get('extracted_data', {})
        inv_data = documents['invoice'].get('extracted_data', {})
        
        # Extract HS codes from declaration
        decl_hs = decl_data.get('hs_codes', [])
        
        # Extract HS codes from invoice items
        inv_hs = []
        for item in inv_data.get('items', []):
            if 'hs_code' in item:
                inv_hs.append(item['hs_code'])
        
        # Find common codes
        common = set(decl_hs) & set(inv_hs)
        if not common and decl_hs and inv_hs:
            result['mismatches'].append({
                'type': 'hs_code_mismatch',
                'severity': 'medium',
                'message': 'No matching HS codes between declaration and invoice'
            })
    
    def _check_origin(self, documents: Dict, result: Dict):
        """Check origin country"""
        if 'coo' not in documents:
            return
        
        coo_data = documents['coo'].get('extracted_data', {})
        origin = coo_data.get('origin_country', '')
        
        if origin and 'UNITED KINGDOM' not in origin.upper():
            result['mismatches'].append({
                'type': 'origin_mismatch',
                'severity': 'high',
                'message': f"Origin is {origin}, expected United Kingdom"
            })
    
    def _check_flight(self, documents: Dict, result: Dict):
        """Check flight number consistency"""
        if 'declaration' not in documents or 'mawb' not in documents:
            return
        
        decl_data = documents['declaration'].get('extracted_data', {})
        mawb_data = documents['mawb'].get('extracted_data', {})
        
        decl_flight = decl_data.get('vessel_flight_number')
        mawb_flight = mawb_data.get('vessel_flight_number')
        
        if decl_flight and mawb_flight and decl_flight != mawb_flight:
            result['mismatches'].append({
                'type': 'flight_mismatch',
                'severity': 'medium',
                'message': f"Flight number mismatch: Declaration says {decl_flight}, MAWB says {mawb_flight}"
            })
    
    def _generate_summary(self, documents: Dict) -> Dict:
        """Generate a human-readable summary"""
        summary = {}
        
        for doc_type in self.mandatory_docs + self.optional_docs:
            if doc_type in documents:
                doc = documents[doc_type]
                data = doc.get('extracted_data', {})
                
                if doc_type == 'declaration':
                    summary['Declaration'] = {
                        'number': data.get('declaration_number', 'N/A'),
                        'flight': data.get('vessel_flight_number', 'N/A'),
                        'packages': data.get('total_packages', 'N/A')
                    }
                elif doc_type == 'invoice':
                    summary['Invoice'] = {
                        'number': data.get('invoice_number', 'N/A'),
                        'value': f"${data.get('total_value', 0):,.2f}",
                        'items': len(data.get('items', []))
                    }
                elif doc_type == 'coo':
                    summary['COO'] = {
                        'origin': data.get('origin_country', 'N/A'),
                        'invoice_ref': data.get('referenced_invoice', 'N/A')
                    }
                elif doc_type == 'mawb':
                    summary['MAWB'] = {
                        'number': data.get('bol_number', 'N/A'),
                        'flight': data.get('vessel_flight_number', 'N/A')
                    }
        
        return summary


# Quick test function
def test_validator():
    """Test the smart validator"""
    
    validator = SmartValidator()
    
    # Test case: All mandatory docs present
    docs = {
        'declaration': {'extracted_data': {'declaration_number': '101-25123867-24'}},
        'invoice': {'extracted_data': {'invoice_number': '69383'}},
        'coo': {'extracted_data': {'referenced_invoice': '69383', 'origin_country': 'United Kingdom'}},
        'mawb': {'extracted_data': {'bol_number': '501-16726323'}}
    }
    
    result = validator.validate(docs)
    print(f"✅ Test 1 - All docs: {result['status']}")
    
    # Test case: Missing COO (mandatory)
    docs_missing = {
        'declaration': {'extracted_data': {}},
        'invoice': {'extracted_data': {}},
        'mawb': {'extracted_data': {}}
    }
    
    result = validator.validate(docs_missing)
    print(f"✅ Test 2 - Missing COO: {result['status']} (missing: {result['missing_mandatory']})")
    
    # Test case: Chain break (COO references wrong invoice)
    docs_chain_break = {
        'declaration': {'extracted_data': {}},
        'invoice': {'extracted_data': {'invoice_number': '69383'}},
        'coo': {'extracted_data': {'referenced_invoice': '99999'}},
        'mawb': {'extracted_data': {}}
    }
    
    result = validator.validate(docs_chain_break)
    print(f"✅ Test 3 - Chain break: {result['status']} (mismatches: {len(result['mismatches'])})")

if __name__ == "__main__":
    test_validator()