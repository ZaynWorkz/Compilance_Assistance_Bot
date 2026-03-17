# check_utils.py

import sys
import os
from pathlib import Path

print("=" * 60)
print("UTILS PACKAGE DEBUGGER")
print("=" * 60)

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
print(f"Project root: {project_root}")

# Check if utils directory exists
utils_path = project_root / "app" / "utils"
print(f"\nUtils path: {utils_path}")
print(f"Utils exists: {utils_path.exists()}")

if utils_path.exists():
    # List all files in utils
    print("\nFiles in utils:")
    for file in utils_path.glob("*.py"):
        size = file.stat().st_size
        print(f"  - {file.name} ({size} bytes)")
        
        # Check for syntax errors in each file
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            compile(content, str(file), 'exec')
            print(f"    ✅ Syntax OK")
        except SyntaxError as e:
            print(f"    ❌ Syntax Error: {e}")
        except Exception as e:
            print(f"    ❌ Error: {e}")

# Try to import cache module
print("\n" + "=" * 60)
print("TESTING IMPORTS")
print("=" * 60)

try:
    from app.utils.cache import CacheManager
    print("✅ Successfully imported CacheManager from app.utils.cache")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    
    # Try to see what's in the module
    try:
        import app.utils.cache
        print(f"\nContents of app.utils.cache:")
        print(dir(app.utils.cache))
    except Exception as e2:
        print(f"Can't inspect module: {e2}")

try:
    from app.validation.engine import ValidationEngine
    print("✅ Successfully imported ValidationEngine from app.validation.engine")
except ImportError as e:
    print(f"❌ Import failed: {e}")

print("\n" + "=" * 60)