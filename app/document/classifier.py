# app/document/classifiers.py

import re

class DocumentClassifier:
    """Identify document type from content"""
    
    def classify(self, text: str) -> str:
        """Classify document based on text content"""
        text_upper = text.upper()
        
        if re.search(r'DEC NO|CUSTOMS DECLARATION|بيان جمركي|DECLARATION', text_upper):
            return 'declaration'
        if re.search(r'INVOICE|INV[-\s]?\d+|COMMERCIAL INVOICE', text_upper):
            return 'invoice'
        if re.search(r'CERTIFICATE OF ORIGIN|ORIGINATE IN THE COUNTRY|COO', text_upper):
            return 'country_of_origin'
        if re.search(r'PACKING LIST|PACKAGES|PACKED', text_upper):
            return 'packing_list'
        if re.search(r'BILL OF LADING|BOL|AIR WAYBILL|AWB', text_upper):
            return 'bol_aws'
        if re.search(r'DELIVERY ORDER|DO[-\s]?\d+', text_upper):
            return 'delivery_order'
        
        return 'unknown'