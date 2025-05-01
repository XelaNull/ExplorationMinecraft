#!/bin/bash
# fix_imports.sh: Fix Python import paths for the ExplorationMinecraft modpack manager
# This ensures the core modules can be found in any Python environment

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODPACK_DIR="$ROOT_DIR/modpack_manager"
SCRIPTS_DIR="$MODPACK_DIR/scripts"
VENV_DIR="$MODPACK_DIR/.venv"

echo "Fixing Python import paths for ExplorationMinecraft..."

# Check if the virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Run ./run_server.sh first to create the virtual environment."
    exit 1
fi

# Find the Python version directory
PY_DIRS=$(find "$VENV_DIR/lib" -type d -name "python*" | sort)

if [ -z "$PY_DIRS" ]; then
    echo "Error: Could not find Python directory in $VENV_DIR/lib"
    echo "Try deleting the .venv directory and running ./run_server.sh again."
    exit 1
fi

for PY_DIR in $PY_DIRS; do
    SITE_PACKAGES="$PY_DIR/site-packages"
    if [ -d "$SITE_PACKAGES" ]; then
        echo "Creating .pth file in $SITE_PACKAGES..."
        echo "$SCRIPTS_DIR/lib" > "$SITE_PACKAGES/modpack_paths.pth"
        echo "$SCRIPTS_DIR" >> "$SITE_PACKAGES/modpack_paths.pth"
        echo "Created modpack_paths.pth in $SITE_PACKAGES"
        
        # Copy core module directly into site-packages (most reliable approach)
        echo "Copying core module to $SITE_PACKAGES..."
        CORE_DEST="$SITE_PACKAGES/core"
        mkdir -p "$CORE_DEST" 2>/dev/null || true
        
        # Copy all Python files
        cp -f "$SCRIPTS_DIR/lib/core"/*.py "$CORE_DEST/" 2>/dev/null || true
        
        # Create __init__.py if it doesn't exist
        if [ ! -f "$CORE_DEST/__init__.py" ]; then
            echo '"""Core module for the Minecraft modpack manager."""' > "$CORE_DEST/__init__.py"
        fi
        
        echo "Copied all core modules to $CORE_DEST"
    fi
done

# Print Python path to verify
echo -e "\nTesting Python path..."
export PYTHONPATH="$SCRIPTS_DIR/lib:$SCRIPTS_DIR:$PYTHONPATH"
echo "PYTHONPATH set to: $PYTHONPATH"

echo -e "\nVerifying import..."
if [ -f "$VENV_DIR/bin/python" ]; then
    VENV_PYTHON="$VENV_DIR/bin/python"
elif [ -f "$VENV_DIR/bin/python3" ]; then
    VENV_PYTHON="$VENV_DIR/bin/python3"
else
    VENV_PYTHON=$(find "$VENV_DIR/bin" -name "python*" | head -n 1)
fi

# Test if imports work
if [ ! -z "$VENV_PYTHON" ]; then
    echo "Using Python: $VENV_PYTHON"
    IMPORT_TEST=$($VENV_PYTHON -c "
import sys
print('Python path:')
for p in sys.path:
    print(f'  {p}')
print('\\nTrying import...')
try:
    from core.profile_manager import ProfileManager
    print('SUCCESS: Core modules can be imported!')
except ImportError as e:
    print(f'ERROR: {e}')
    sys.exit(1)
")
    echo "$IMPORT_TEST"
else
    echo "Warning: Could not find Python interpreter in virtual environment"
fi

echo -e "\nImport paths fixed. Please run ./run_server.sh to start the server."