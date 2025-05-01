#!/bin/bash
# Script to set up the PYTHONPATH for modpack manager scripts

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Add lib directory to PYTHONPATH
if [ -z "$PYTHONPATH" ]; then
    export PYTHONPATH="$SCRIPT_DIR/lib"
else
    export PYTHONPATH="$SCRIPT_DIR/lib:$PYTHONPATH"
fi

# If we're in a virtual environment, also add the site-packages
if [ ! -z "$VIRTUAL_ENV" ]; then
    # Get Python version
    PY_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    SITE_PACKAGES="$VIRTUAL_ENV/lib/python$PY_VERSION/site-packages"
    
    if [ -d "$SITE_PACKAGES" ]; then
        export PYTHONPATH="$SITE_PACKAGES:$PYTHONPATH"
    fi
fi

echo "PYTHONPATH set to: $PYTHONPATH"