# V:\Portresq\Compilance_Assistace_Bot\run.py

"""
Compliance Assistant - Main Entry Point
Run this file to start the application
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

print("=" * 60)
print("🚀 COMPLIANCE ASSISTANT BOT")
print("=" * 60)
print(f"📂 Project Root: {project_root}")
print(f"🐍 Python: {sys.executable}")
print("=" * 60)

try:
    # Import the main app
    from app.main import main
    
    # Run it
    print("✅ Imports successful! Starting application...\n")
    main()
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("\n🔍 Troubleshooting:")
    print("1. Check if all __init__.py files exist")
    print("2. Check for circular imports")
    print("3. Run: python test_all_imports.py")
    
except Exception as e:
    print(f"❌ Runtime Error: {e}")
    import traceback
    traceback.print_exc()