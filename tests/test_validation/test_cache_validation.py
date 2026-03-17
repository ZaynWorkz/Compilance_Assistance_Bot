# tests/test_validation/test_cache_validation.py

"""
Test file for cached validation engine.
Run with: python -m pytest tests/test_validation/test_cache_validation.py -v
Or: python tests/test_validation/test_cache_validation.py
"""

import sys
import os
from pathlib import Path

# Add project root to Python path - THIS IS CRITICAL
current_file = Path(__file__).absolute()
project_root = current_file.parent.parent.parent  # Goes up 3 levels: file -> test_validation -> tests -> project_root
project_root = str(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"✅ Added project root to path: {project_root}")

# Now import your modules
try:
    from app.validation.engine import ValidationEngine, ValidationResult
    from app.validation.optimized_engine import OptimizedValidationEngine
    from app.utils.cache import CacheManager, cached
    print("✅ All imports successful!")
    print(f"   - ValidationEngine: {ValidationEngine}")
    print(f"   - OptimizedValidationEngine: {OptimizedValidationEngine}")
    print(f"   - CacheManager: {CacheManager}")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\n🔍 Troubleshooting:")
    print("   1. Check if app/validation/engine.py exists")
    print("   2. Check if app/utils/cache.py exists")
    print("   3. Run: python check_utils.py to debug")
    sys.exit(1)

import time

def test_cache_validation():
    """Test the cached validation engine"""
    
    print("\n" + "="*70)
    print("🧪 TESTING CACHED VALIDATION ENGINE")
    print("="*70)
    
    # Create test data
    declaration_number = "DEC-2024-123456"
    uploaded_documents = {
        "doc1": {
            "document_type": "declaration",
            "extracted_data": {
                "declaration_number": "DEC-2024-123456",
                "consignee": "Test Importer Inc",
                "exporter": "Test Exporter Ltd"
            }
        },
        "doc2": {
            "document_type": "invoice",
            "extracted_data": {
                "declaration_number": "DEC-2024-123456",
                "invoice_number": "INV-001",
                "total_amount": "1000",
                "currency": "USD"
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
    
    print(f"\n📄 Declaration Number: {declaration_number}")
    print(f"📦 Documents to validate: {len(uploaded_documents)}")
    print(f"   - {list(uploaded_documents.keys())}")
    
    # Create engines
    print("\n🔧 Creating validation engines...")
    standard_engine = ValidationEngine()
    optimized_engine = OptimizedValidationEngine()
    
    # TEST 1: Standard validation (should compute)
    print("\n" + "-"*70)
    print("🔷 TEST 1: Standard Validation (should compute)")
    print("-"*70)
    
    start = time.perf_counter()
    result1 = standard_engine.validate_all_documents(declaration_number, uploaded_documents)
    time1 = time.perf_counter() - start
    
    print(f"   ⏱️  Execution time: {time1*1000:.3f}ms")
    print(f"   📊 Status: {result1.status}")
    print(f"   📋 Missing documents: {result1.missing_documents}")
    print(f"   🔍 Mismatches found: {len(result1.mismatches)}")
    
    if result1.mismatches:
        for i, mismatch in enumerate(result1.mismatches[:3]):  # Show first 3 mismatches
            print(f"      {i+1}. {mismatch.get('document_type')}: {mismatch.get('field')}")
    
    # TEST 2: Cached validation (should be faster)
    print("\n" + "-"*70)
    print("🔶 TEST 2: Cached Validation (should retrieve from cache)")
    print("-"*70)
    
    start = time.perf_counter()
    result2 = optimized_engine.validate_all_documents(declaration_number, uploaded_documents)
    time2 = time.perf_counter() - start
    
    print(f"   ⏱️  Execution time: {time2*1000:.3f}ms")
    print(f"   📊 Status: {result2.status}")
    print(f"   📋 Missing documents: {result2.missing_documents}")
    
    # TEST 3: Add BOL document and validate again (should compute new)
    print("\n" + "-"*70)
    print("🔷 TEST 3: Add BOL Document (should compute new)")
    print("-"*70)
    
    uploaded_documents["doc4"] = {
        "document_type": "bol_aws",
        "extracted_data": {
            "declaration_number": "DEC-2024-123456",
            "bol_number": "BOL-001",
            "vessel_name": "MV Test Voyager",
            "package_count": "10"
        }
    }
    
    print(f"   📦 Added document: bol_aws")
    print(f"   📦 Total documents now: {len(uploaded_documents)}")
    
    start = time.perf_counter()
    result3 = optimized_engine.validate_all_documents(declaration_number, uploaded_documents)
    time3 = time.perf_counter() - start
    
    print(f"   ⏱️  Execution time: {time3*1000:.3f}ms")
    print(f"   📊 Status: {result3.status}")
    
    # TEST 4: Add Country of Origin (should compute new)
    print("\n" + "-"*70)
    print("🔷 TEST 4: Add Country of Origin (should compute new)")
    print("-"*70)
    
    uploaded_documents["doc5"] = {
        "document_type": "country_of_origin",
        "extracted_data": {
            "declaration_number": "DEC-2024-123456",
            "certificate_number": "COO-001",
            "country": "China"
        }
    }
    
    print(f"   📦 Added document: country_of_origin")
    print(f"   📦 Total documents now: {len(uploaded_documents)}")
    
    start = time.perf_counter()
    result4 = optimized_engine.validate_all_documents(declaration_number, uploaded_documents)
    time4 = time.perf_counter() - start
    
    print(f"   ⏱️  Execution time: {time4*1000:.3f}ms")
    print(f"   📊 Status: {result4.status}")
    
    # TEST 5: Same data again (should be cached)
    print("\n" + "-"*70)
    print("🔶 TEST 5: Same Data Again (should be cached)")
    print("-"*70)
    
    start = time.perf_counter()
    result5 = optimized_engine.validate_all_documents(declaration_number, uploaded_documents)
    time5 = time.perf_counter() - start
    
    print(f"   ⏱️  Execution time: {time5*1000:.3f}ms")
    print(f"   📊 Status: {result5.status}")
    
    # PERFORMANCE SUMMARY
    print("\n" + "="*70)
    print("📊 PERFORMANCE SUMMARY")
    print("="*70)
    
    print(f"\n📈 Standard validation (Test 1):      {time1*1000:8.3f}ms")
    print(f"📉 Cached validation (Test 2):        {time2*1000:8.3f}ms")
    print(f"📊 New computation - BOL (Test 3):    {time3*1000:8.3f}ms")
    print(f"📊 New computation - COO (Test 4):    {time4*1000:8.3f}ms")
    print(f"📉 Cached again (Test 5):             {time5*1000:8.3f}ms")
    
    # Calculate speedups
    if time2 < time1:
        speedup1 = time1 / time2
        print(f"\n✅ Cache speedup (Test 1 vs 2): {speedup1:.1f}x faster")
    else:
        print(f"\n⚠️  Cache not showing speedup in Test 2")
    
    if time5 < time3:
        speedup2 = time3 / time5
        print(f"✅ Cache speedup (Test 3 vs 5): {speedup2:.1f}x faster")
    
    # Verify results are consistent
    print("\n" + "-"*70)
    print("🔍 CONSISTENCY CHECK")
    print("-"*70)
    
    assert result1.status == result2.status, "Test 1 and 2 results should match"
    assert result4.status == result5.status, "Test 4 and 5 results should match"
    
    print("✅ All results are consistent!")
    
    # Show final validation status
    print("\n" + "-"*70)
    print("📋 FINAL VALIDATION STATUS")
    print("-"*70)
    
    if result5.status == "success":
        print("✅ All documents validated successfully!")
    else:
        print("❌ Validation failed. Issues found:")
        if result5.missing_documents:
            print(f"   Missing: {result5.missing_documents}")
        if result5.mismatches:
            print(f"   Mismatches: {len(result5.mismatches)}")
        if result5.document_specific_errors:
            print(f"   Document errors: {result5.document_specific_errors}")
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETED SUCCESSFULLY")
    print("="*70)
    
    return {
        "times": {
            "standard": time1,
            "cached": time2,
            "new_bol": time3,
            "new_coo": time4,
            "cached_again": time5
        },
        "results": {
            "test1": result1.status,
            "test2": result2.status,
            "test3": result3.status,
            "test4": result4.status,
            "test5": result5.status
        }
    }

def test_with_missing_documents():
    """Test validation with missing documents"""
    print("\n" + "="*70)
    print("🧪 TESTING WITH MISSING DOCUMENTS")
    print("="*70)
    
    engine = ValidationEngine()
    
    # Create test data with missing documents
    declaration_number = "DEC-2024-123456"
    uploaded_documents = {
        "doc1": {
            "document_type": "declaration",
            "extracted_data": {"declaration_number": "DEC-2024-123456"}
        }
        # Missing invoice, packing_list, etc.
    }
    
    print(f"\n📄 Declaration Number: {declaration_number}")
    print(f"📦 Documents uploaded: {len(uploaded_documents)}")
    
    result = engine.validate_all_documents(declaration_number, uploaded_documents)
    
    print(f"\n📊 Validation Status: {result.status}")
    print(f"📋 Missing documents: {result.missing_documents}")
    
    assert result.status == "error"
    assert len(result.missing_documents) > 0
    print("\n✅ Missing documents detection works!")

def test_with_mismatched_data():
    """Test validation with mismatched data"""
    print("\n" + "="*70)
    print("🧪 TESTING WITH MISMATCHED DATA")
    print("="*70)
    
    engine = ValidationEngine()
    
    # Create test data with mismatched declaration numbers
    declaration_number = "DEC-2024-123456"
    uploaded_documents = {
        "doc1": {
            "document_type": "declaration",
            "extracted_data": {"declaration_number": "DEC-2024-123456"}
        },
        "doc2": {
            "document_type": "invoice",
            "extracted_data": {
                "declaration_number": "DEC-2024-999999",  # Mismatch!
                "invoice_number": "INV-001",
                "total_amount": "1000"
            }
        }
    }
    
    print(f"\n📄 Declaration Number: {declaration_number}")
    print(f"📦 Documents with mismatch")
    
    result = engine.validate_all_documents(declaration_number, uploaded_documents)
    
    print(f"\n📊 Validation Status: {result.status}")
    print(f"🔍 Mismatches found: {len(result.mismatches)}")
    
    for mismatch in result.mismatches:
        print(f"   - {mismatch.get('document_type')}: {mismatch.get('field')}")
        print(f"     Expected: {mismatch.get('expected')}, Found: {mismatch.get('found')}")
    
    assert result.status == "error"
    assert len(result.mismatches) > 0
    print("\n✅ Mismatch detection works!")

def test_cache_manager_directly():
    """Test the CacheManager directly"""
    print("\n" + "="*70)
    print("🧪 TESTING CACHE MANAGER DIRECTLY")
    print("="*70)
    
    cache = CacheManager()
    
    # Test set and get
    cache.set("test_key", "test_value", ttl=5)
    value = cache.get("test_key")
    print(f"\n✅ Set/Get: {value}")
    
    # Test cache key generation
    key = cache.get_cache_key("function_name", "arg1", "arg2", kwarg1="value1")
    print(f"✅ Cache key generation: {key}")
    
    # Test stats
    cache.get("missing_key")
    stats = cache.get_stats()
    print(f"✅ Cache stats: {stats}")
    
    # Test clear
    cache.clear()
    print("✅ Cache cleared")
    
    print("\n✅ CacheManager tests passed!")

if __name__ == "__main__":
    """Run all tests"""
    
    print("\n" + "🚀"*35)
    print("🚀 RUNNING ALL CACHE VALIDATION TESTS")
    print("🚀"*35)
    
    # Run cache manager test
    test_cache_manager_directly()
    
    # Run main validation test
    results = test_cache_validation()
    
    # Run missing documents test
    test_with_missing_documents()
    
    # Run mismatched data test
    test_with_mismatched_data()
    
    print("\n" + "✨"*35)
    print("✨ ALL TESTS COMPLETED SUCCESSFULLY")
    print("✨"*35)
    
    # Print final summary
    print("\n📊 FINAL SUMMARY:")
    print(f"   - Standard validation time: {results['times']['standard']*1000:.2f}ms")
    print(f"   - Cached validation time: {results['times']['cached']*1000:.2f}ms")
    print(f"   - Speedup: {results['times']['standard']/results['times']['cached']:.1f}x")