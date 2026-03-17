'''
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.document.processor import DocumentProcessor
import pdfplumber
import re

def debug_boe_extraction(file_path):
    """Debug BOE extraction to see what text is actually extracted"""
    
    print("=" * 60)
    print("🔍 BOE EXTRACTION DEBUGGER")
    print("=" * 60)
    
    # Open the PDF and extract raw text
    with open(file_path, 'rb') as f:
        processor = DocumentProcessor()
        text = processor.extract_text_from_pdf(f)
    
    print(f"\n📄 Raw extracted text ({len(text)} characters):")
    print("-" * 40)
    print(text[:2000])  # Show first 2000 chars
    print("-" * 40)
    
    # Try to find key fields with various patterns
    print("\n🔎 Testing regex patterns:")
    print("-" * 40)
    
    patterns = {
        'declaration_number': [
            r'DEC NO\.?\s*(\d{3}-\d{8}-\d{2})',
            r'DEC[-\s]?NO[.:\s]*(\d{3}-\d{8}-\d{2})',
            r'(\d{3}-\d{8}-\d{2})',
            r'رقم البيان.*?(\d{3}-\d{8}-\d{2})',
            r'101-25123867-24'  # Exact match
        ],
        'declaration_date': [
            r'DEC DATE[.:\s]*(\d{2}/\d{2}/\d{4})',
            r'تاريخ البيان.*?(\d{2}/\d{2}/\d{4})',
            r'(\d{2}/\d{2}/\d{4})',
            r'12/08/2024'  # Exact match
        ],
        'flight_number': [
            r'CARRIER\'S NAME.*?(\w+\d+)',
            r'7L5238',
            r'FLIGHT[.:\s]*(\w+\d+)'
        ],
        'packages': [
            r'NO\. OF PACKAGES.*?(\d+)\s*-\s*PACKAGES',
            r'(\d+)\s*-\s*PACKAGES',
            r'8 - PACKAGES',
            r'PKG\s*(\d+)'
        ],
        'consignee': [
            r'CONSIGNEE/EXPORTER.*?([A-Z\s]+(?:LLC|LTD|INC|TRADING))',
            r'MEREDEW TRADING LLC',
            r'AE-1008008 - ([A-Z\s]+(?:LLC|LTD|INC|TRADING))'
        ]
    }
    
    for field, pattern_list in patterns.items():
        print(f"\n{field}:")
        found = False
        for i, pattern in enumerate(pattern_list):
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                print(f"  ✅ Pattern {i+1}: '{pattern}'")
                print(f"     Found: {matches}")
                found = True
                break
        if not found:
            print(f"  ❌ No patterns matched")
    
    # Show lines containing key terms
    print("\n📝 Lines with key terms:")
    print("-" * 40)
    key_terms = ['DEC NO', 'DATE', 'FLIGHT', 'PACKAGES', 'MEREDEW', '101-25123867-24']
    for line in text.split('\n'):
        for term in key_terms:
            if term in line:
                print(f"  {line.strip()}")
                break

if __name__ == "__main__":
    # Update this path to your actual BOE.pdf location
    file_path = r"V:/Portresq/Compilance_Assistace_Bot/BOE.pdf"
    debug_boe_extraction(file_path)

    '''

# debug_boe_classification.py

import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
sys.path.insert(0, str(Path(__file__).parent))

from app.document.processor import DocumentProcessor
import pdfplumber

def debug_boe_classification():
    """See how BOE.pdf is being classified"""
    
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select BOE.pdf",
        filetypes=[("PDF files", "*.pdf")]
    )
    
    if not file_path:
        print("❌ No file selected")
        return
    
    print("=" * 60)
    print("🔍 BOE CLASSIFICATION DEBUG")
    print("=" * 60)
    print(f"📂 File: {file_path}")
    
    # Extract text
    processor = DocumentProcessor()
    with open(file_path, 'rb') as f:
        text = processor.extract_text_from_pdf(f)
    
    print(f"\n📝 First 500 chars of extracted text:")
    print("-" * 40)
    print(text[:500])
    print("-" * 40)
    
    # See what the classifier sees
    doc_type = processor.classifier.classify(text)
    print(f"\n🔎 Classifier result: '{doc_type}'")
    
    # Check what patterns are matching
    print("\n🔎 Testing classification patterns:")
    
    text_upper = text.upper()
    
    patterns = {
        'declaration': ['DEC NO', 'CUSTOMS DECLARATION', 'بيان جمركي', 'DECLARATION'],
        'invoice': ['INVOICE', 'COMMERCIAL INVOICE'],
        'coo': ['CERTIFICATE OF ORIGIN', 'ORIGINATE'],
        'mawb': ['BILL OF LADING', 'AIR WAYBILL', 'MAWB']
    }
    
    for doc_type_name, keywords in patterns.items():
        print(f"\n{doc_type_name.upper()}:")
        for keyword in keywords:
            found = keyword in text_upper
            print(f"  • '{keyword}': {'✅' if found else '❌'}")
    
    return doc_type

if __name__ == "__main__":
    debug_boe_classification()