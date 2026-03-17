# test_workflow_flow.py

"""
Test the complete workflow flow without UI
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.session.state_manager import SessionStateManager
from app.session.attempt_tracker import AttemptTracker
from app.workflow.state_machine import WorkflowState
from app.validation.engine import ValidationEngine
from datetime import datetime

def test_workflow():
    """Test the complete workflow flow"""
    
    print("=" * 60)
    print("TESTING WORKFLOW FLOW")
    print("=" * 60)
    
    # 1. Initialize
    print("\n1️⃣ Initializing session...")
    session = SessionStateManager()
    tracker = AttemptTracker(max_attempts=3)
    print("✅ Session initialized")
    
    # 2. Set declaration number
    print("\n2️⃣ Setting declaration number...")
    decl_number = "101-25123867-24"
    session.update_context(declaration_number=decl_number)
    print(f"✅ Declaration number: {decl_number}")
    
    # 3. Set declaration date
    print("\n3️⃣ Setting declaration date...")
    decl_date = datetime.now()
    session.update_context(declaration_date=decl_date)
    print(f"✅ Declaration date: {decl_date}")
    
    # 4. Test document order
    print("\n4️⃣ Document upload order:")
    document_order = [
        'declaration',
        'invoice',
        'packing_list',
        'bol_aws',
        'country_of_origin',
        'delivery_order'
    ]
    
    for i, doc_type in enumerate(document_order, 1):
        print(f"   {i}. {doc_type}")
    
    # 5. Test attempt tracking
    print("\n5️⃣ Testing attempt tracking...")
    doc_type = 'invoice'
    
    for attempt in range(1, 4):
        success, message = tracker.register_attempt(doc_type, success=False)
        print(f"   Attempt {attempt}: {message}")
        if not success:
            print(f"   ⚠️ Session aborted after {attempt} attempts!")
            break
    
    # Reset tracker
    tracker.reset()
    print("   ✅ Tracker reset")
    
    # 6. Test successful upload
    print("\n6️⃣ Testing successful upload...")
    success, message = tracker.register_attempt('invoice', success=True)
    print(f"   ✅ Success! {message}")
    
    print("\n" + "=" * 60)
    print("✅ WORKFLOW TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_workflow()