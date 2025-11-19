# Configuration file for pytest
import sys
from pathlib import Path

# Add the app directory to the path so we can import modules
# Get the project root (backend directory)
backend_path = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_path))

# Ensure app module can be imported
app_path = backend_path / "app"
if str(app_path) not in sys.path:
    sys.path.insert(0, str(app_path))