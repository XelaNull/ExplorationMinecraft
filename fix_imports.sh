#!/bin/bash
# Script to fix import issues in Python scripts

COMMANDS_DIR="modpack_manager/scripts/commands"

# Check if the commands directory exists
if [ ! -d "$COMMANDS_DIR" ]; then
    echo "Error: Commands directory not found at $COMMANDS_DIR"
    exit 1
fi

echo "Fixing import statements in Python scripts..."

# Loop through all Python files in the commands directory
for file in "$COMMANDS_DIR"/*.py; do
    if [ -f "$file" ]; then
        echo "Processing $file"
        
        # Use sed to replace 'from core.' with 'from lib.core.'
        sed -i.bak 's/from core\./from lib.core./g' "$file"
        
        # Remove backup files
        rm -f "$file.bak"
    fi
done

echo "Import fixing complete."
echo "Remember to also run the scripts with PYTHONPATH set to include the lib directory."