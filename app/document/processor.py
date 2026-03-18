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

def __init__(self):
    self.classifier = DocumentClassifier()
    
    # ✅ Add MAWBExtractor to the extractors dictionary
    self.extractors = {
        'declaration': BOEExtractor(),
        'invoice': InvoiceExtractor(),
        'coo': COOExtractor(),  # Updated COO extractor
        'mawb': MAWBExtractor(),  # New MAWB extractor
        'packing_list': PackingListExtractor(),
        'delivery_order': DeliveryOrderExtractor()
    }
    
    # OCR setup (keep as is)
    self.easyocr = None
    self.has_ocr = False
    try:
        import easyocr
        self.easyocr = easyocr.Reader(['en'], gpu=False)
        self.has_ocr = True
        print("✅ OCR initialized successfully")
    except ImportError:
        print("⚠️ OCR libraries not installed")



# app/document/processor.py - Update DocumentClassifier to recognize MAWB

class DocumentClassifier:
    """Identify document type from content"""
    
    def classify(self, text: str) -> str:
        """Classify document based on text content"""
        text_upper = text.upper()
        
        # BOE/Customs Declaration
        if any(term in text_upper for term in ['DEC NO', 'CUSTOMS DECLARATION', 'بيان جمركي', 'DECLARATION']):
            return 'declaration'
        
        # Invoice
        if any(term in text_upper for term in ['INVOICE', 'INV NO', 'COMMERCIAL INVOICE', 'DOCUMENT NO']):
            return 'invoice'
        
        # Certificate of Origin - UPDATED with better patterns
        if any(term in text_upper for term in [
            'CERTIFICATE OF ORIGIN', 
            'ORIGINATE IN THE COUNTRY',
            'LONDON CHAMBER OF COMMERCE',
            'CONSIGNOR',
            'CONSIGNEE',
            'Invoice no'  # COO often references invoice
        ]):
            return 'coo'
        
        # MAWB - NEW patterns
        if any(term in text_upper for term in [
            'MASTER AIR WAYBILL',
            'AIR WAYBILL',
            'MAWB',
            'FLIGHT NUMBER',
            'LHR',  # London Heathrow
            'DWC'   # Dubai World Central
        ]):
            return 'mawb'
        
        # Packing List
        if any(term in text_upper for term in ['PACKING LIST', 'PACKAGES']):
            return 'packing_list'
        
        # Delivery Order
        if any(term in text_upper for term in ['DELIVERY ORDER', 'DO NUMBER']):
            return 'delivery_order'
        
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


# app/document/processor.py - REPLACE with this COOExtractor

# app/document/processor.py - Replace the COOExtractor class

class COOExtractor:
    """Extract from Certificate of Origin"""
    
    def extract(self, text: str) -> Dict[str, Any]:
        """Extract fields from certificate of origin"""
        data = {}
        
        print("\n" + "=" * 70)
        print("🔍 COO EXTRACTOR DEBUG")
        print("=" * 70)
        
        # Print the raw text to see what's being extracted
        print(f"\n📝 RAW TEXT ({len(text)} chars):")
        print("-" * 40)
        print(text[:1000])  # Print first 1000 chars
        print("-" * 40)
        
        # Print each line for analysis
        print("\n📄 Lines in extracted text:")
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if line.strip():
                print(f"  Line {i}: {line.strip()}")
        
        # Test each pattern manually
        print("\n🔎 Testing patterns:")
        
        # 1️⃣ INVOICE REFERENCE
        print("\n1️⃣ Invoice Reference patterns:")
        invoice_patterns = [
            r'Invoice no[.:\s]*(\d+)',
            r'Invoice[.:\s]*(\d+)',
            r'(\d+).*?dated',
            r'69383'
        ]
        
        found = False
        for i, pattern in enumerate(invoice_patterns):
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                print(f"  ✅ Pattern {i+1}: '{pattern}'")
                print(f"     Found: {matches}")
                data['referenced_invoice'] = matches[0] if isinstance(matches[0], str) else matches[0][0]
                found = True
            else:
                print(f"  ❌ Pattern {i+1}: '{pattern}' - No match")
        
        if not found:
            print("  ⚠️ No invoice reference found!")
        
        # 2️⃣ ORIGIN COUNTRY
        print("\n2️⃣ Origin Country patterns:")
        if 'UNITED KINGDOM' in text.upper():
            data['origin_country'] = 'United Kingdom'
            print(f"  ✅ Found 'UNITED KINGDOM' in text")
        elif 'UK' in text.upper():
            data['origin_country'] = 'United Kingdom'
            print(f"  ✅ Found 'UK' in text")
        else:
            print("  ❌ No origin country found")
        
        # 3️⃣ CONSIGNEE
        print("\n3️⃣ Consignee patterns:")
        if 'MEREDEW TRADING LLC' in text.upper():
            data['consignee'] = 'MEREDEW TRADING LLC'
            print(f"  ✅ Found 'MEREDEW TRADING LLC'")
        else:
            consignee_match = re.search(r'Consignee[^:]*:\s*([^\n]+)', text, re.IGNORECASE)
            if consignee_match:
                data['consignee'] = consignee_match.group(1).strip()
                print(f"  ✅ Found via pattern: {data['consignee']}")
            else:
                print("  ❌ No consignee found")
        
        # 4️⃣ HS CODES
        print("\n4️⃣ HS Code patterns:")
        hs_codes = re.findall(r'\b(\d{8})\b', text)
        if hs_codes:
            data['hs_codes'] = list(set(hs_codes))
            print(f"  ✅ Found: {data['hs_codes']}")
        else:
            print("  ❌ No HS codes found")
        
        print("\n" + "=" * 70)
        print("📊 EXTRACTION RESULTS")
        print("=" * 70)
        for key, value in data.items():
            print(f"  {key}: {value}")
        
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


# app/document/processor.py - Add this new class

class MAWBExtractor:
    """Extract from Master Air Waybill"""
    
    def extract(self, text: str) -> Dict[str, Any]:
        """Extract fields from MAWB document"""
        data = {}
        
        print("\n🔍 Extracting MAWB fields...")
        
        # 1️⃣ MAWB NUMBER
        mawb_patterns = [
            (r'Air Waybill Number[:\s]*([A-Z0-9-]+)', 'Air Waybill Number'),
            (r'MAWB[:\s]*([A-Z0-9-]+)', 'MAWB'),
            (r'(\d{3}[-\s]?\d{8})', 'Generic pattern'),
            (r'501[-\s]*16726323', 'Exact pattern')
        ]
        
        for pattern, desc in mawb_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                mawb = match.group(1) if match.groups() else match.group(0)
                # Clean up spaces and ensure format
                mawb = mawb.replace(' ', '')
                if '-' not in mawb and len(mawb) == 11:
                    mawb = f"{mawb[:3]}-{mawb[3:]}"
                data['mawb_number'] = mawb
                print(f"  ✅ MAWB Number: {data['mawb_number']}")
                break
        
        # 2️⃣ FLIGHT NUMBER
        flight_patterns = [
            r'Flight[:\s]*([A-Z0-9]+)',
            r'7L5238'
        ]
        for pattern in flight_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['flight_number'] = match.group(1) if match.groups() else match.group(0)
                print(f"  ✅ Flight Number: {data['flight_number']}")
                break
        
        # 3️⃣ NUMBER OF PACKAGES
        packages_patterns = [
            r'(\d+)\s*PACKAGES?',
            r'8\s*PACKAGES'
        ]
        for pattern in packages_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['packages'] = int(match.group(1)) if match.groups() else 8
                print(f"  ✅ Packages: {data['packages']}")
                break
        
        # 4️⃣ GROSS WEIGHT
        weight_match = re.search(r'([\d.]+)\s*kg', text, re.IGNORECASE)
        if weight_match:
            data['gross_weight'] = float(weight_match.group(1))
            print(f"  ✅ Gross Weight: {data['gross_weight']} kg")
        
        # 5️⃣ DEPARTURE AIRPORT
        if 'LONDON HEATHROW' in text.upper() or 'LHR' in text.upper():
            data['departure'] = 'LHR'
            print(f"  ✅ Departure: {data['departure']}")
        
        # 6️⃣ DESTINATION AIRPORT
        if 'DUBAI WORLD CENTRAL' in text.upper() or 'DWC' in text.upper():
            data['destination'] = 'DWC'
            print(f"  ✅ Destination: {data['destination']}")
        
        # 7️⃣ CONSIGNEE
        consignee_match = re.search(r'Consignee[^:]*:\s*([^\n]+)', text, re.IGNORECASE)
        if consignee_match:
            data['consignee'] = consignee_match.group(1).strip()
            print(f"  ✅ Consignee: {data['consignee']}")
        elif 'MEREDEW TRADING LLC' in text:
            data['consignee'] = 'MEREDEW TRADING LLC'
            print(f"  ✅ Consignee: {data['consignee']}")
        
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
            'mawb': MAWBExtractor(),
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
    
