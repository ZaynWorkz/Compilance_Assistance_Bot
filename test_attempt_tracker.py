# test_attempts.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.session.attempt_tracker import AttemptTracker

def test_attempt_tracker():
    """Test the attempt tracker functionality"""
    
    print("=" * 60)
    print("TESTING ATTEMPT TRACKER")
    print("=" * 60)
    
    tracker = AttemptTracker(max_attempts=3)
    
    # Test 1: Get attempts for new document
    print("\n1️⃣ Getting attempts for new document...")
    attempts = tracker.get_attempts('invoice')
    print(f"   Total: {attempts['total']}")
    print(f"   Failed: {attempts['failed']}")
    print(f"   Remaining: {attempts['remaining']}")
    assert attempts['total'] == 0
    assert attempts['failed'] == 0
    assert attempts['remaining'] == 3
    print("   ✅ Correct!")
    
    # Test 2: Register a failed attempt
    print("\n2️⃣ Registering failed attempt...")
    can_proceed, message = tracker.register_attempt('invoice', success=False)
    print(f"   Message: {message}")
    
    attempts = tracker.get_attempts('invoice')
    print(f"   Failed: {attempts['failed']}")
    print(f"   Remaining: {attempts['remaining']}")
    assert attempts['failed'] == 1
    assert attempts['remaining'] == 2
    print("   ✅ Correct!")
    
    # Test 3: Register two more failures
    print("\n3️⃣ Registering two more failures...")
    tracker.register_attempt('invoice', success=False)
    tracker.register_attempt('invoice', success=False)
    
    attempts = tracker.get_attempts('invoice')
    print(f"   Failed: {attempts['failed']}")
    print(f"   Remaining: {attempts['remaining']}")
    print(f"   Session aborted: {tracker.session_aborted}")
    assert attempts['failed'] == 3
    assert attempts['remaining'] == 0
    assert tracker.session_aborted == True
    print("   ✅ Correct - Session aborted after 3 failures!")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)

if __name__ == "__main__":
    test_attempt_tracker()