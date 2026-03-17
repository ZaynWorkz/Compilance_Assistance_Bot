# run.py - Place this in your project root

import sys
import os
from pathlib import Path

# Print debug info
print("=" * 60)
print("DEBUG INFORMATION")
print("=" * 60)
print(f"Current working directory: {os.getcwd()}")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Virtual env: {sys.prefix != sys.base_prefix}")
print("\nPython path:")
for i, path in enumerate(sys.path):
    print(f"  {i}: {path}")
print("=" * 60)

# Add project root to path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    print(f"\n✅ Added project root to path: {project_root}")

# Now try to import
print("\n" + "=" * 60)
print("TESTING IMPORTS")
print("=" * 60)

try:
    from app.validation.engine import ValidationEngine
    print("✅ Successfully imported ValidationEngine")
except ImportError as e:
    print(f"❌ Failed to import ValidationEngine: {e}")

try:
    from app.utils.cache import CacheManager
    print("✅ Successfully imported CacheManager")
except ImportError as e:
    print(f"❌ Failed to import CacheManager: {e}")

print("\nChecking if app module exists:")
app_path = project_root / "app"
if app_path.exists():
    print(f"✅ app folder exists at: {app_path}")
    print(f"   Contents: {[d.name for d in app_path.iterdir() if d.is_dir()]}")
else:
    print(f"❌ app folder NOT found at: {app_path}")

print("\n" + "=" * 60)