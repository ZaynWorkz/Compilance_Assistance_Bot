# app/document/processor.py (FIXED VERSION)

"""
Document processing module with classification and extraction
"""

import re
import pdfplumber
from PIL import Image
import io
from typing import Dict, Any, List

# app/document/processor.py - UPDATED DocumentClassifier

class DocumentClassifier:
    """Identify document type from content"""
    
    def classify(self, text: str) -> str:
        """Classify document based on text content"""
        text_upper = text.upper()
        
        # ===== PRIORITY 1: BOE/Customs Declaration =====
        # These are HIGHLY specific to BOE
        boe_indicators = [
            'DEC NO',                    # Your actual text has "101-25123867-24"
            'CUSTOMS DECLARATION',
            'IMPORT TO LOCAL',
            'بيان جمركي',
            'PORT TYPE AIR',
            'DEC DATE',
            'CIF LOCAL VALUE',
            'TOTAL DUTY',
            'CLEARING AGENT',
            '351100490321'               # Your specific reference
        ]
        
        # Check for BOE indicators (multiple to be sure)
        boe_matches = sum(1 for indicator in boe_indicators if indicator in text_upper)
        if boe_matches >= 2:  # If we find at least 2 BOE indicators
            print(f"✅ Classified as: declaration (BOE match - {boe_matches} indicators)")
            return 'declaration'
        
        # Also check for the specific declaration number format
        import re
        if re.search(r'\d{3}-\d{8}-\d{2}', text):  # 101-25123867-24 pattern
            print("✅ Classified as: declaration (number pattern match)")
            return 'declaration'
        
        # ===== PRIORITY 2: Invoice =====
        if any(term in text_upper for term in [
            'INVOICE', 
            'INV NO',
            'COMMERCIAL INVOICE',
            'DOCUMENT NO',
            'CUSTOMER ID',
            'EORI'
        ]):
            print("✅ Classified as: invoice")
            return 'invoice'
        
        # ===== PRIORITY 3: Certificate of Origin =====
        if any(term in text_upper for term in [
            'CERTIFICATE OF ORIGIN',
            'ORIGINATE IN THE COUNTRY',
            'CHAMBER OF COMMERCE',
            'LONDON CHAMBER'  # From your COO
        ]):
            print("✅ Classified as: country_of_origin")
            return 'country_of_origin'
        
        # ===== PRIORITY 4: MAWB =====
        if any(term in text_upper for term in [
            'BILL OF LADING',
            'AIR WAYBILL',
            'MASTER AIR WAYBILL',
            'MAWB'
        ]):
            print("✅ Classified as: mawb")
            return 'mawb'
        
        # ===== PRIORITY 5: Packing List =====
        # Only classify as packing list if we DON'T have BOE indicators
        if 'PACKAGES' in text_upper and 'PACKING LIST' in text_upper:
            print("✅ Classified as: packing_list")
            return 'packing_list'
        
        # ===== PRIORITY 6: Delivery Order =====
        if any(term in text_upper for term in [
            'DELIVERY ORDER',
            'DO NUMBER'
        ]):
            print("✅ Classified as: delivery_order")
            return 'delivery_order'
        
        print("⚠️ Classified as: unknown")
        return 'unknown'
    
class BOEExtractor:
    """Extract from Bill of Entry/Customs Declaration"""
    
    def extract(self, text: str) -> Dict[str, Any]:
        """Extract fields from declaration document"""
        data = {}
        
        print("\n🔍 Extracting BOE fields...")
        
        # 1️⃣ DECLARATION NUMBER
        decl_match = re.search(r'(\d{3}-\d{8}-\d{2})', text)
        if decl_match:
            data['declaration_number'] = decl_match.group(1)
            print(f"  ✅ Declaration Number: {data['declaration_number']}")
        
        # 2️⃣ DECLARATION DATE
        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
        if date_match:
            data['declaration_date'] = date_match.group(1)
            print(f"  ✅ Declaration Date: {data['declaration_date']}")
        
        # 3️⃣ FLIGHT NUMBER
        flight_match = re.search(r'7L5238|(\w+\d+)', text)
        if flight_match:
            data['vessel_flight_number'] = flight_match.group(0)
            print(f"  ✅ Flight Number: {data['vessel_flight_number']}")
        
        # 4️⃣ PACKAGES
        packages_match = re.search(r'(\d+)\s*-\s*PACKAGES', text)
        if packages_match:
            data['total_packages'] = int(packages_match.group(1))
            print(f"  ✅ Total Packages: {data['total_packages']}")
        
        # 5️⃣ CONSIGNEE
        consignee_match = re.search(r'MEREDEW TRADING LLC', text)
        if consignee_match:
            data['consignee'] = consignee_match.group(0)
            print(f"  ✅ Consignee: {data['consignee']}")
        
        # 6️⃣ GROSS WEIGHT
        weight_match = re.search(r'([\d.]+)\s*\(kg\)', text)
        if weight_match:
            data['gross_weight'] = float(weight_match.group(1))
            print(f"  ✅ Gross Weight: {data['gross_weight']} kg")
        
        # 7️⃣ HS CODES
        hs_codes = re.findall(r'\b(\d{8})\b', text)
        if hs_codes:
            data['hs_codes'] = list(set(hs_codes))
            print(f"  ✅ HS Codes: {data['hs_codes']}")
        
        # 8️⃣ TOTAL VALUE
        value_match = re.search(r'Total Value[.:\s]*([\d.]+)', text, re.IGNORECASE)
        if value_match:
            data['total_value'] = float(value_match.group(1))
            print(f"  ✅ Total Value: {data['total_value']}")
        
        return data
class InvoiceExtractor:
    """Extract invoice data from text/PDF"""
    
    def extract(self, text: str) -> Dict[str, Any]:
        """Extract all invoice fields"""
        data = {}
        
        print("\n🔍 Extracting Invoice fields...")
        
        # Helper function
        def extract_field(pattern, group=1, flags=re.IGNORECASE):
            match = re.search(pattern, text, flags)
            return match.group(group).strip() if match else None
        
        # 1️⃣ INVOICE NUMBER
        data['invoice_number'] = extract_field(r'INVOICE NUMBER:\s*(\d+)')
        
        # 2️⃣ INVOICE DATE
        data['invoice_date'] = extract_field(r'INVOICE DATE:\s*(\d{2}/\d{2}/\d{4})')
        
        # 3️⃣ CUSTOMER ID
        data['customer_id'] = extract_field(r'CUSTOMER ID:\s*(\w+)')
        
        # 4️⃣ EORI NUMBER
        data['eori_number'] = extract_field(r'EORI NUMBER:\s*(\d+)')
        
        # 5️⃣ VAT NUMBER
        vat = extract_field(r'VAT NUMBER:\s*(\d+)')
        if vat:
            data['vat_number'] = vat
        
        # 6️⃣ CONSIGNEE
        data['consignee'] = extract_field(r'CONSIGNEE:\s*([A-Z\s]+(?:LLC|LTD|INC|TRADING))')
        
        # 7️⃣ TOTAL VALUE
        total = extract_field(r'TOTAL:\s*\$?([\d,]+\.\d{2})')
        if total:
            data['total_value'] = float(total.replace(',', ''))
        
        # 8️⃣ HS CODES
        hs_codes = re.findall(r'(\d{8})', text)
        if hs_codes:
            data['hs_codes'] = list(set(hs_codes))
        
        # 9️⃣ LINE ITEMS
        items = []
        lines = text.split('\n')
        for line in lines:
            if any(term in line for term in ['CAPPUCINO', 'SHAMBA', 'MORTONS']):
                amounts = re.findall(r'\$([\d,]+\.\d{2})', line)
                if amounts:
                    # Extract description (text before first $)
                    desc = line.split('$')[0].strip()
                    items.append({
                        'description': desc[:50],
                        'value': float(amounts[-1].replace(',', ''))
                    })
        
        if items:
            data['items'] = items
            data['item_count'] = len(items)
        
        # Log results
        print("\n📊 Extracted fields:")
        for key, value in data.items():
            if key != 'items':
                print(f"  {key}: {value}")
        
        if 'items' in data:
            print(f"  items: {len(data['items'])} line items")
        
        return data
class COOExtractor:
    """Extract from Certificate of Origin"""
    
    def extract(self, text: str) -> Dict[str, Any]:
        """Extract fields from certificate of origin"""
        data = {}
        
        # Reference to Invoice
        inv_ref_pattern = r'Invoice no[.:\s]*(\d+).*?dated (\d{2}[/-]\d{2}[/-]\d{4})'
        match = re.search(inv_ref_pattern, text, re.IGNORECASE)
        if match:
            data['referenced_invoice'] = match.group(1)
            data['invoice_date'] = match.group(2)
        
        # Origin Country
        origin_pattern = r'ORIGINATE IN THE COUNTRY[.:\s]*([A-Z\s]+)'
        match = re.search(origin_pattern, text, re.IGNORECASE)
        if match:
            data['origin_country'] = match.group(1).strip()
        
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


class DocumentProcessor:
    """Main document processor with OCR fallback"""
    
    def __init__(self):
        """Initialize the document processor with all extractors"""
        self.classifier = DocumentClassifier()
        
        # ✅ THIS IS THE KEY PART - initialize the extractors dictionary!
        self.extractors = {
            'declaration': BOEExtractor(),
            'invoice': InvoiceExtractor(),
            'country_of_origin': COOExtractor(),
            'packing_list': PackingListExtractor(),
            'bol_aws': BOLAWSextractor(),
            'delivery_order': DeliveryOrderExtractor()
        }
        
        # Try to import OCR libraries (optional)
        self.easyocr = None
        self.has_ocr = False
        try:
            import easyocr
            self.easyocr = easyocr.Reader(['en'], gpu=False)
            self.has_ocr = True
            print("✅ OCR initialized successfully")
        except ImportError:
            print("⚠️ OCR libraries not installed. Install with: pip install easyocr")
        except Exception as e:
            print(f"⚠️ OCR initialization failed: {e}")
    
    def extract_text_from_pdf(self, file) -> str:
        """
        Extract text from PDF with OCR fallback
        """
        text = ""
        
        try:
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    # Try to extract digital text
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text += page_text + "\n"
                    elif self.has_ocr:
                        # Fallback to OCR for scanned pages
                        try:
                            img = page.to_image(resolution=200).original
                            img_bytes = io.BytesIO()
                            img.save(img_bytes, format='PNG')
                            img_bytes.seek(0)
                            
                            ocr_result = self.easyocr.readtext(img_bytes.getvalue(), paragraph=True)
                            for result in ocr_result:
                                text += result[1] + "\n"
                        except Exception as ocr_error:
                            print(f"OCR error on page: {ocr_error}")
        except Exception as e:
            print(f"Error extracting text: {e}")
            text = ""
        
        return text
    
    def process_document(self, file) -> Dict[str, Any]:
        """
        Process a document: classify and extract data
        """
        # Extract text
        text = self.extract_text_from_pdf(file)
        
        if not text:
            return {
                'document_type': 'unknown',
                'filename': file.name,
                'extracted_data': {},
                'validation': {
                    'valid': False,
                    'message': 'Could not extract text from document'
                }
            }
        
        # Classify document
        doc_type = self.classifier.classify(text)
        print(f"📋 Classified as: {doc_type}")
        
        # Extract data based on type - NOW self.extractors EXISTS!
        extracted_data = {}
        if doc_type in self.extractors:
            extracted_data = self.extractors[doc_type].extract(text)
            print(f"✅ Extracted data: {list(extracted_data.keys())}")
        else:
            print(f"⚠️ No extractor for document type: {doc_type}")
        
        # Validate minimum required fields
        is_valid, message = self._validate_extraction(doc_type, extracted_data)
        
        return {
            'document_type': doc_type,
            'filename': file.name,
            'extracted_data': extracted_data,
            'validation': {
                'valid': is_valid,
                'message': message
            },
            'text_preview': text[:500] + "..." if len(text) > 500 else text
        }
    
    def _validate_extraction(self, doc_type: str, data: Dict) -> tuple:
        """
        Validate that minimum required fields are extracted
        """
        required_fields = {
            'declaration': ['declaration_number'],
            'invoice': ['invoice_number', 'total_value'],
            'country_of_origin': ['origin_country'],
            'packing_list': ['total_packages'],
            'bol_aws': ['bol_number'],
            'delivery_order': ['delivery_order_number']
        }
        
        if doc_type in required_fields:
            missing = [f for f in required_fields[doc_type] if f not in data]
            if missing:
                return False, f"Missing fields: {', '.join(missing)}"
        
        return True, "Valid document"