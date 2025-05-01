#!/bin/bash
# Run server script for ExplorationMinecraft
# This version uses a more direct approach to avoid Python import issues

# Enable strict error handling
set -e

# Error handling function
function handle_error {
    echo "ERROR: An error occurred on line $1"
    echo "Please check the output above for specific error messages"
    exit 1
}

# Set up error trap
trap 'handle_error $LINENO' ERR

# Directory setup
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODPACK_DIR="$ROOT_DIR/modpack_manager"
SCRIPTS_DIR="$MODPACK_DIR/scripts"
PROFILE_NAME="exploration_modpack"

echo "===== ExplorationMinecraft Server Setup ====="
echo "This script will set up and run the Minecraft server with all required mods."
echo "Starting from directory: $ROOT_DIR"

# Step 1: Create required directories if they don't exist
echo -e "\n[1/6] Creating required directories..."
mkdir -p "$MODPACK_DIR/modpack_cache"
mkdir -p "$MODPACK_DIR/client_packs"
mkdir -p "$MODPACK_DIR/backups"
mkdir -p "$MODPACK_DIR/server_pack/mods"
mkdir -p "$MODPACK_DIR/server_pack/config"
mkdir -p "$MODPACK_DIR/server_pack/datapacks"

# Determine Python version and command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found"
    exit 1
fi
echo "Using Python command: $PYTHON_CMD"

# Set up Python virtual environment
VENV_DIR="$MODPACK_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR" 2>/dev/null || $PYTHON_CMD -m virtualenv "$VENV_DIR"
fi

# Activate the virtual environment
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    PYTHON_CMD="$VENV_DIR/bin/python"
elif [ -f "$VENV_DIR/Scripts/activate" ]; then
    # Windows support
    source "$VENV_DIR/Scripts/activate"
    PYTHON_CMD="$VENV_DIR/Scripts/python"
else
    echo "Warning: Could not activate virtual environment. Using system Python."
fi

# Install required packages
echo "Installing required packages..."
$PYTHON_CMD -m pip install -r "$SCRIPTS_DIR/requirements.txt"

# Step 2: Resolve mod dependencies from the profile (direct Python call to avoid import issues)
echo -e "\n[2/6] Resolving mod dependencies..."
$PYTHON_CMD - << EOF
import sys
import os

# Add scripts directory to Python path
scripts_dir = "$SCRIPTS_DIR"
sys.path.insert(0, scripts_dir)

# Import commands module
try:
    from commands.resolve_dependencies import main
    sys.argv = ['resolve_dependencies.py', '--profile', '$PROFILE_NAME']
    main()
except Exception as e:
    print(f"Error resolving dependencies: {e}")
    sys.exit(1)
EOF

# Step 3: Download all mods
echo -e "\n[3/6] Downloading all mods..."
$PYTHON_CMD - << EOF
import sys
import os

# Add scripts directory to Python path
scripts_dir = "$SCRIPTS_DIR"
sys.path.insert(0, scripts_dir)

# Import commands module
try:
    from commands.download_mods import main
    sys.argv = ['download_mods.py', '--profile', '$PROFILE_NAME']
    main()
except Exception as e:
    print(f"Error downloading mods: {e}")
    sys.exit(1)
EOF

# Step 4: Create server pack
echo -e "\n[4/6] Creating server pack..."
$PYTHON_CMD - << EOF
import sys
import os

# Add scripts directory to Python path
scripts_dir = "$SCRIPTS_DIR"
sys.path.insert(0, scripts_dir)

# Import commands module
try:
    from commands.create_server_pack import main
    sys.argv = ['create_server_pack.py', '--profile', '$PROFILE_NAME', '--force']
    main()
except Exception as e:
    print(f"Error creating server pack: {e}")
    sys.exit(1)
EOF

# Step 5: Build Docker image
echo -e "\n[5/6] Building Docker image..."
"$SCRIPTS_DIR/docker_image_manager.sh" build $PROFILE_NAME

# Step 6: Start the server
echo -e "\n[6/6] Starting Minecraft server..."
"$SCRIPTS_DIR/docker_image_manager.sh" start $PROFILE_NAME

echo -e "\n===== Server Started ====="
echo "The server is now starting. This may take a few minutes, especially on first run."
echo "You can check the logs with: ./modpack_manager/scripts/docker_image_manager.sh logs $PROFILE_NAME"
echo "To stop the server: ./modpack_manager/scripts/docker_image_manager.sh stop $PROFILE_NAME"

# Display logs to monitor startup
echo -e "\nShowing server logs (press Ctrl+C to exit logs but keep server running):"
sleep 3
"$SCRIPTS_DIR/docker_image_manager.sh" logs $PROFILE_NAME