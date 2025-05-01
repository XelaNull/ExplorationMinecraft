#!/bin/bash
# Run server script for ExplorationMinecraft
# This script will download all mods, build a Docker image, and start the server

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

# Source the PYTHONPATH setup script
source "$SCRIPTS_DIR/export_pythonpath.sh" > /dev/null

# Create a symlink to the lib directory in the virtual environment to ensure imports work
VENV_DIR="$MODPACK_DIR/.venv"
if [ -d "$VENV_DIR" ]; then
    # Get Python version
    if [ -d "$VENV_DIR/lib/python3.9" ]; then
        PY_VERSION="3.9"
    elif [ -d "$VENV_DIR/lib/python3.8" ]; then
        PY_VERSION="3.8"
    elif [ -d "$VENV_DIR/lib/python3.7" ]; then
        PY_VERSION="3.7"
    elif [ -d "$VENV_DIR/lib/python3.10" ]; then
        PY_VERSION="3.10"
    elif [ -d "$VENV_DIR/lib/python3.11" ]; then
        PY_VERSION="3.11"
    else
        # Find any Python directory
        PY_VERSION=$(ls -1 "$VENV_DIR/lib" | grep "python3" | head -n 1)
    fi
    
    if [ ! -z "$PY_VERSION" ]; then
        SITE_PACKAGES="$VENV_DIR/lib/$PY_VERSION/site-packages"
        if [ -d "$SITE_PACKAGES" ]; then
            # Create .pth file to add lib directory to Python path
            echo "$SCRIPTS_DIR/lib" > "$SITE_PACKAGES/modpack_paths.pth"
            echo "$SCRIPTS_DIR" >> "$SITE_PACKAGES/modpack_paths.pth"
        fi
    fi
fi

# Step 1: Create required directories if they don't exist
echo -e "\n[1/6] Creating required directories..."
mkdir -p "$MODPACK_DIR/modpack_cache"
mkdir -p "$MODPACK_DIR/client_packs"
mkdir -p "$MODPACK_DIR/backups"
mkdir -p "$MODPACK_DIR/server_pack/mods"
mkdir -p "$MODPACK_DIR/server_pack/config"
mkdir -p "$MODPACK_DIR/server_pack/datapacks"

# Step 2: Resolve mod dependencies from the profile
echo -e "\n[2/6] Resolving mod dependencies..."
PYTHONPATH="$SCRIPTS_DIR/lib:$SCRIPTS_DIR:$PYTHONPATH" $SCRIPTS_DIR/modpack_manager.sh resolve-dependencies --profile $PROFILE_NAME

# Step 3: Download all mods
echo -e "\n[3/6] Downloading all mods..."
$SCRIPTS_DIR/modpack_manager.sh download --profile $PROFILE_NAME

# Step 4: Create server pack
echo -e "\n[4/6] Creating server pack..."
$SCRIPTS_DIR/modpack_manager.sh create-server-pack --profile $PROFILE_NAME --force

# Step 5: Build Docker image
echo -e "\n[5/6] Building Docker image..."
$SCRIPTS_DIR/docker_image_manager.sh build $PROFILE_NAME

# Step 6: Start the server
echo -e "\n[6/6] Starting Minecraft server..."
$SCRIPTS_DIR/docker_image_manager.sh start $PROFILE_NAME

echo -e "\n===== Server Started ====="
echo "The server is now starting. This may take a few minutes, especially on first run."
echo "You can check the logs with: ./modpack_manager/scripts/docker_image_manager.sh logs $PROFILE_NAME"
echo "To stop the server: ./modpack_manager/scripts/docker_image_manager.sh stop $PROFILE_NAME"

# Display logs to monitor startup
echo -e "\nShowing server logs (press Ctrl+C to exit logs but keep server running):"
sleep 3
$SCRIPTS_DIR/docker_image_manager.sh logs $PROFILE_NAME