# app/document/extractors.py

import re
from typing import Dict, Any


class BOEExtractor:
    """Extract from Bill of Entry/Customs Declaration"""
    
    def extract(self, text: str) -> Dict[str, Any]:
        """Extract fields from declaration document"""
        data = {}
        
        # Declaration Number (Pattern: 101-25123867-24)
        decl_pattern = r'DEC[-\s]?NO[.:\s]*(\d{3}-\d{8}-\d{2})'
        match = re.search(decl_pattern, text, re.IGNORECASE)
        if match:
            data['declaration_number'] = match.group(1)
        
        # Declaration Date
        date_pattern = r'DEC[-\s]?DATE[.:\s]*(\d{2}[/-]\d{2}[/-]\d{4})'
        match = re.search(date_pattern, text, re.IGNORECASE)
        if match:
            data['declaration_date'] = match.group(1).replace('/', '-')
        
        # Consignee
        consignee_pattern = r'CONSIGNEE[./:]*\s*([A-Z\s]+(?:LLC|LTD|INC|TRADING))'
        match = re.search(consignee_pattern, text, re.IGNORECASE)
        if match:
            data['consignee'] = match.group(1).strip()
        
        # Gross Weight
        weight_pattern = r'GROSS WEIGHT[.:\s]*([\d.]+)\s*\(?kg\)?'
        match = re.search(weight_pattern, text, re.IGNORECASE)
        if match:
            data['gross_weight'] = float(match.group(1))
        
        return data


# app/document/processor.py - UPDATED InvoiceExtractor

class InvoiceExtractor:
    """Extract from Invoice - UPDATED with correct patterns"""
    
    def extract(self, text: str) -> Dict[str, Any]:
        """Extract fields from invoice document"""
        data = {}
        
        # 1️⃣ INVOICE NUMBER - Pattern: "Document No: 69383"
        print("\n🔍 Extracting Invoice fields...")
        
        inv_pattern = r'Document\s*No[.:\s]*(\d+)'
        match = re.search(inv_pattern, text, re.IGNORECASE)
        if match:
            data['invoice_number'] = match.group(1)
            print(f"  ✅ Invoice Number: {data['invoice_number']}")
        else:
            print("  ❌ Invoice Number not found")
        
        # 2️⃣ INVOICE DATE - Pattern: "Date: 23/07/2024"
        date_pattern = r'Date[.:\s]*(\d{2}/\d{2}/\d{4})'
        match = re.search(date_pattern, text)
        if match:
            data['invoice_date'] = match.group(1)
            print(f"  ✅ Invoice Date: {data['invoice_date']}")
        else:
            print("  ❌ Invoice Date not found")
        
        # 3️⃣ EORI NUMBER - Pattern: "EORI No: 229694662000"
        eori_pattern = r'EORI\s*No[.:\s]*(\d+)'
        match = re.search(eori_pattern, text, re.IGNORECASE)
        if match:
            data['eori_number'] = match.group(1)
            print(f"  ✅ EORI Number: {data['eori_number']}")
        else:
            print("  ❌ EORI Number not found")
        
        # 4️⃣ CUSTOMER ID - Pattern: "Customer ID: MET003"
        cust_pattern = r'Customer\s*ID[.:\s]*(\w+)'
        match = re.search(cust_pattern, text, re.IGNORECASE)
        if match:
            data['customer_id'] = match.group(1)
            print(f"  ✅ Customer ID: {data['customer_id']}")
        else:
            print("  ❌ Customer ID not found")
        
        # 5️⃣ VAT NUMBER - Pattern: "VAT Regn No. 229 6946 62"
        vat_pattern = r'VAT\s*Regn\s*No[.:\s]*([\d\s]+)'
        match = re.search(vat_pattern, text, re.IGNORECASE)
        if match:
            # Remove spaces from VAT number
            vat_number = match.group(1).replace(' ', '')
            data['vat_number'] = vat_number
            print(f"  ✅ VAT Number: {data['vat_number']}")
        else:
            print("  ❌ VAT Number not found")
        
        # 6️⃣ TOTAL VALUE - Looking for the table value
        # From your PDF: "Value USD ($)" and then "$14,620.80", "$1,562.40", "$14,169.50" and total "$30,352.70"
        total_value_pattern = r'\$?([\d,]+\.\d{2})\s*$'
        
        # Find all dollar amounts
        dollar_amounts = re.findall(r'\$?([\d,]+\.\d{2})', text)
        if dollar_amounts:
            # The last amount is usually the total
            if len(dollar_amounts) >= 3:
                data['total_value'] = float(dollar_amounts[-1].replace(',', ''))
                print(f"  ✅ Total Value: ${data['total_value']:,.2f}")
                
                # Also capture line items
                items = []
                line_pattern = r'([A-Z\s]+?)\s+(\d+)\s+\d+\s+\d+\s+\$?([\d,]+\.\d{2})'
                for match in re.finditer(line_pattern, text):
                    items.append({
                        'description': match.group(1).strip(),
                        'quantity': int(match.group(2)),
                        'value': float(match.group(3).replace(',', ''))
                    })
                if items:
                    data['items'] = items
                    print(f"  ✅ Found {len(items)} line items")
        else:
            print("  ❌ Total Value not found")
        
        # 7️⃣ CONSIGNEE - "SEND TO: MEREDEW TRADING LLC"
        consignee_pattern = r'SEND\s*TO[.:\s]*([A-Z\s]+(?:LLC|LTD|INC|TRADING))'
        match = re.search(consignee_pattern, text, re.IGNORECASE)
        if match:
            data['consignee'] = match.group(1).strip()
            print(f"  ✅ Consignee: {data['consignee']}")
        
        return data

# app/document/processor.py - UPDATED COOExtractor

class COOExtractor:
    """Extract from Certificate of Origin"""
    
    def extract(self, text: str) -> Dict[str, Any]:
        """Extract fields from certificate of origin"""
        data = {}
        
        print("\n🔍 Extracting COO fields...")
        
        # 1️⃣ COUNTRY OF ORIGIN - PRIMARY KEY! (UNITED KINGDOM)
        # Look for UNITED KINGDOM in the document
        uk_pattern = r'(UNITED KINGDOM|UK)'
        match = re.search(uk_pattern, text, re.IGNORECASE)
        if match:
            data['origin_country'] = 'United Kingdom'  # Standardize to full name
            print(f"  ✅ Country of Origin: {data['origin_country']}")
        else:
            # Try alternative patterns
            origin_pattern = r'ORIGINATE IN THE COUNTRY[.\n]*([A-Z\s]+)'
            match = re.search(origin_pattern, text, re.IGNORECASE)
            if match:
                country = match.group(1).strip()
                # Clean up the country name
                if 'UNITED KINGDOM' in country.upper():
                    data['origin_country'] = 'United Kingdom'
                else:
                    data['origin_country'] = country.title()
                print(f"  ✅ Country of Origin: {data['origin_country']}")
            else:
                # Look in Consignor section
                consignor_section = re.search(r'Consignor[.\n]*([A-Za-z0-9\s,&]+)', text, re.IGNORECASE)
                if consignor_section:
                    consignor_text = consignor_section.group(1)
                    if 'UNITED KINGDOM' in consignor_text.upper():
                        data['origin_country'] = 'United Kingdom'
                        print(f"  ✅ Country of Origin (from Consignor): {data['origin_country']}")
                    else:
                        print("  ❌ Country of Origin not found")
                else:
                    print("  ❌ Country of Origin not found")
        
        # 2️⃣ CONSIGNOR (Exporter)
        consignor_pattern = r'1\s*Consignor[.\n]*([A-Za-z0-9\s,&]+)(?=\d+\s*Consignee)'
        match = re.search(consignor_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            data['consignor'] = match.group(1).strip()
            print(f"  ✅ Consignor: {data['consignor'][:50]}...")
        
        # 3️⃣ CONSIGNEE (Importer)
        consignee_pattern = r'2\s*Consignee[.\n]*([A-Za-z0-9\s,&]+)(?=\d+\s*Transport|$)'
        match = re.search(consignee_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            data['consignee'] = match.group(1).strip()
            print(f"  ✅ Consignee: {data['consignee']}")
        
        # 4️⃣ INVOICE REFERENCE - CRITICAL FOR CHAIN VALIDATION
        invoice_pattern = r'Invoice\s*no\s*(\d+)\s*dated\s*(\d{2}/\d{2}/\d{4})'
        match = re.search(invoice_pattern, text, re.IGNORECASE)
        if match:
            data['referenced_invoice'] = match.group(1)
            data['invoice_date'] = match.group(2)
            print(f"  ✅ Referenced Invoice: {data['referenced_invoice']}")
            print(f"  ✅ Invoice Date: {data['invoice_date']}")
        
        # 5️⃣ CERTIFICATE NUMBER (if available)
        cert_pattern = r'(?:Certificate|Reference|No)[.:\s]*([A-Z0-9-]+)'
        match = re.search(cert_pattern, text, re.IGNORECASE)
        if match:
            data['certificate_number'] = match.group(1)
            print(f"  ✅ Certificate Number: {data['certificate_number']}")
        
        # 6️⃣ AUTHORISED SIGNATORY
        signatory_pattern = r'Authorised Signatory[.\n]*([A-Za-z\s]+)'
        match = re.search(signatory_pattern, text, re.IGNORECASE)
        if match:
            data['signatory'] = match.group(1).strip()
            print(f"  ✅ Signatory: {data['signatory']}")
        
        # 7️⃣ ISSUING AUTHORITY
        authority_pattern = r'(LONDON CHAMBER OF COMMERCE AND INDUSTRY)'
        match = re.search(authority_pattern, text, re.IGNORECASE)
        if match:
            data['issuing_authority'] = match.group(1)
            print(f"  ✅ Issuing Authority: {data['issuing_authority']}")
        
        # 8️⃣ VERIFICATION URL
        url_pattern = r'(https?://[^\s]+)'
        match = re.search(url_pattern, text)
        if match:
            data['verification_url'] = match.group(1)
            print(f"  ✅ Verification URL: {data['verification_url']}")
        
        return data
class PackingListExtractor:
    """Extract from Packing List"""
    
    def extract(self, text: str) -> Dict[str, Any]:
        """Extract fields from packing list"""
        data = {}
        
        # Total Packages
        packages_pattern = r'(?:TOTAL|NUMBER OF)?\s*PACKAGES[.:\s]*(\d+)'
        match = re.search(packages_pattern, text, re.IGNORECASE)
        if match:
            data['total_packages'] = int(match.group(1))
        
        # Gross Weight
        weight_pattern = r'GROSS WEIGHT[.:\s]*([\d.]+)\s*kg'
        match = re.search(weight_pattern, text, re.IGNORECASE)
        if match:
            data['gross_weight'] = float(match.group(1))
        
        return data


class BOLAWSextractor :
    """Extract from Bill of Lading / Airway Bill"""
    
    def extract(self, text: str) -> Dict[str, Any]:
        """Extract fields from BOL/AWS"""
        data = {}
        
        # BOL Number
        bol_pattern = r'(?:BOL|AWB|MAWB)[\s#:]*(\d+)'
        match = re.search(bol_pattern, text, re.IGNORECASE)
        if match:
            data['bol_number'] = match.group(1)
        
        # Flight/Vessel Number
        flight_pattern = r'(?:FLIGHT|VOYAGE)[\s#:]*([A-Z0-9]+)'
        match = re.search(flight_pattern, text, re.IGNORECASE)
        if match:
            data['vessel_flight_number'] = match.group(1)
        
        return data


class DeliveryOrderExtractor:
    """Extract from Delivery Order"""
    
    def extract(self, text: str) -> Dict[str, Any]:
        """Extract fields from delivery order"""
        data = {}
        
        # DO Number
        do_pattern = r'DELIVERY ORDER[.\s#:]*NO[.:\s]*([A-Z0-9-]+)'
        match = re.search(do_pattern, text, re.IGNORECASE)
        if match:
            data['delivery_order_number'] = match.group(1)
        
        return data

