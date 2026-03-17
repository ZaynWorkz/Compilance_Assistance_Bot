# test_imports_fixed.py

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

print("=" * 60)
print("TESTING IMPORTS WITH FIXED PATHS")
print("=" * 60)

# Test each import
imports_to_test = [
    ("app.utils.exceptions", ["WorkflowError", "ValidationError"]),
    ("app.utils.logger", ["setup_logging"]),
    ("app.utils.error_handler", ["ErrorHandler"]),
    ("app.utils.security", ["SecurityMiddleware", "RateLimiter"]),
    ("app.utils.cache", ["CacheManager", "cached"]),
    ("app.utils.context", ["WorkflowContext"]),
    ("app.session.state_manager", ["SessionStateManager"]),
    ("app.session.attempt_tracker", ["AttemptTracker"]),
    ("app.workflow.state_machine", ["StateMachine", "WorkflowState"]),
]

for module_name, classes in imports_to_test:
    try:
        module = __import__(module_name, fromlist=classes)
        print(f"✅ {module_name}")
        for class_name in classes:
            if hasattr(module, class_name):
                print(f"   └─ {class_name} ✓")
            else:
                print(f"   └─ {class_name} ✗ MISSING")
    except Exception as e:
        print(f"❌ {module_name}: {e}")

print("=" * 60)