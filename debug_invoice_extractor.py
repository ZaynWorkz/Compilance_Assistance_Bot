# test_invoice_pdf_direct.py

import sys
from pathlib import Path
import pdfplumber
import re
from typing import Dict, Any, List

def extract_from_pdf(file_path: str) -> Dict[str, Any]:
    """Extract invoice data directly from PDF"""
    
    print("=" * 60)
    print("📄 TESTING INVOICE PDF EXTRACTION")
    print("=" * 60)
    print(f"📂 File: {file_path}")
    
    # Extract text from PDF
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    
    print(f"\n📝 Raw extracted text:")
    print("-" * 40)
    print(text)
    print("-" * 40)
    
    # Now extract fields
    data = {}
    
    # Helper function
    def extract(pattern, group=1):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(group) if match else None
    
    # 1️⃣ INVOICE NUMBER
    data['invoice_number'] = extract(r'INVOICE NUMBER:\s*(\d+)')
    
    # 2️⃣ INVOICE DATE
    data['invoice_date'] = extract(r'INVOICE DATE:\s*(\d{2}/\d{2}/\d{4})')
    
    # 3️⃣ CUSTOMER ID
    data['customer_id'] = extract(r'CUSTOMER ID:\s*(\w+)')
    
    # 4️⃣ EORI NUMBER
    data['eori_number'] = extract(r'EORI NUMBER:\s*(\d+)')
    
    # 5️⃣ VAT NUMBER
    vat = extract(r'VAT NUMBER:\s*(\d+)')
    if vat:
        data['vat_number'] = vat
    
    # 6️⃣ CONSIGNEE
    data['consignee'] = extract(r'CONSIGNEE:\s*([A-Z\s]+(?:LLC|LTD|INC|TRADING))')
    
    # 7️⃣ TOTAL VALUE
    total = extract(r'TOTAL:\s*\$?([\d,]+\.\d{2})')
    if total:
        data['total_value'] = float(total.replace(',', ''))
    
    # 8️⃣ HS CODES
    hs_codes = re.findall(r'(\d{8})', text)
    if hs_codes:
        data['hs_codes'] = list(set(hs_codes))
    
    # 9️⃣ LINE ITEMS
    items = []
    # Look for item lines
    lines = text.split('\n')
    for line in lines:
        if 'CAPPUCINO' in line or 'SHAMBA' in line or 'MORTONS' in line:
            # Extract dollar amounts from the line
            amounts = re.findall(r'\$([\d,]+\.\d{2})', line)
            if len(amounts) >= 2:
                items.append({
                    'description': line.split('$')[0].strip()[:30],
                    'unit_price': float(amounts[0].replace(',', '')),
                    'value': float(amounts[-1].replace(',', ''))
                })
    
    if items:
        data['items'] = items
        data['item_count'] = len(items)
    
    # Display results
    print("\n📊 EXTRACTED DATA:")
    print("-" * 40)
    for key, value in data.items():
        if key != 'items':
            print(f"{key}: {value}")
    
    if 'items' in data:
        print(f"\n📦 ITEMS:")
        for item in data['items']:
            print(f"  • {item['description']}: ${item['value']:,.2f}")
    
    return data

if __name__ == "__main__":
    # Update this path to your file
    file_path = r"V:/Portresq/Compilance_Assistace_Bot/docs_/INVOICE_GEN_.pdf.pdf"
    result = extract_from_pdf(file_path)