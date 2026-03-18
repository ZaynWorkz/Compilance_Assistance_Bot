# debug_coo_upload.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.document.processor import DocumentProcessor

# Path to your COO file
file_path = r"V:/Portresq/Compilance_Assistace_Bot/docs_/COO_GEN_.pdf"

processor = DocumentProcessor()
with open(file_path, 'rb') as f:
    result = processor.process_document(f)

print("\n" + "=" * 70)
print("📋 FINAL RESULT")
print("=" * 70)
print(f"Document Type: {result['document_type']}")
print(f"Validation: {result['validation']}")
print("\nExtracted Data:")
for key, value in result['extracted_data'].items():
    print(f"  {key}: {value}")