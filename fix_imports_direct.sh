#!/bin/bash
# Script to directly fix import issues in Python scripts

COMMANDS_DIR="modpack_manager/scripts/commands"

# Check if the commands directory exists
if [ ! -d "$COMMANDS_DIR" ]; then
    echo "Error: Commands directory not found at $COMMANDS_DIR"
    exit 1
fi

echo "Updating all Python scripts with direct core imports..."

# Loop through all Python files in the commands directory
for file in "$COMMANDS_DIR"/*.py; do
    if [ -f "$file" ]; then
        echo "Processing $file"
        
        # Replace the path setup and imports
        sed -i.bak '
        # Find the import block
        /# Add parent directory to path for module imports/,/from lib\.core/ {
            # Replace the whole block
            /# Add parent directory to path for module imports/ {
                c\
# Add parent directory to path for module imports\
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # scripts directory\
sys.path.append(lib_path)\
\
# This ensures both direct imports and lib.X imports work\
from core.profile_manager import ProfileManager
                N
                d
            }
            # Delete all other lines in the block
            d
        }
        
        # Just convert any other imports from lib.core to core
        s/from lib\.core\./from core./g
        ' "$file"
        
        # Remove backup files
        rm -f "$file.bak"
    fi
done

echo "Import fixing complete. All scripts now use direct 'from core.X import Y' imports."
echo "Be sure to run the scripts with PYTHONPATH including the scripts directory."