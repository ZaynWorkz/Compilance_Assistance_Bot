# test_cached_validation.py
from app.validation.engine import ValidationEngine, ValidationResult  
from app.validation.optimized_engine import OptimizedValidationEngine  
from app.utils.cache import CacheManager, cached
import time

def test_cached_validation():
    """Test the cached validation engine"""
    
    # Create test data
    declaration_number = "DEC-2024-123456"
    uploaded_documents = {
        "doc1": {
            "document_type": "declaration",
            "extracted_data": {"declaration_number": "DEC-2024-123456"}
        },
        "doc2": {
            "document_type": "invoice",
            "extracted_data": {
                "declaration_number": "DEC-2024-123456",
                "invoice_number": "INV-001",
                "total_amount": "1000"
            }
        },
        "doc3": {
            "document_type": "packing_list",
            "extracted_data": {
                "declaration_number": "DEC-2024-123456",
                "packing_list_number": "PL-001",
                "total_packages": "10",
                "total_value": "1000"
            }
        }
    }
    
    # Create engines
    standard_engine = ValidationEngine()
    optimized_engine = OptimizedValidationEngine()
    
    # First validation (should compute)
    print("First validation (standard)...")
    start = time.time()
    result1 = standard_engine.validate_all_documents(declaration_number, uploaded_documents)
    print(f"Time: {time.time() - start:.3f}s")
    print(f"Result: {result1.status}")
    
    # Second validation with optimized (should be cached)
    print("\nSecond validation (optimized - should be cached)...")
    start = time.time()
    result2 = optimized_engine.validate_all_documents(declaration_number, uploaded_documents)
    print(f"Time: {time.time() - start:.3f}s")
    print(f"Result: {result2.status}")
    
    # Third validation with different data (should compute new)
    print("\nThird validation (different data - should compute)...")
    uploaded_documents["doc4"] = {
        "document_type": "bol_aws",
        "extracted_data": {
            "declaration_number": "DEC-2024-123456",
            "bol_number": "BOL-001",
            "package_count": "10"
        }
    }
    start = time.time()
    result3 = optimized_engine.validate_all_documents(declaration_number, uploaded_documents)
    print(f"Time: {time.time() - start:.3f}s")
    print(f"Result: {result3.status}")

if __name__ == "__main__":
    test_cached_validation()