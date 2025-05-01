#!/bin/bash
# Script to robustly fix import issues in Python scripts

COMMANDS_DIR="modpack_manager/scripts/commands"

# Check if the commands directory exists
if [ ! -d "$COMMANDS_DIR" ]; then
    echo "Error: Commands directory not found at $COMMANDS_DIR"
    exit 1
fi

echo "Fixing import statements in Python scripts with a more robust approach..."

# Create a template for the import fix
IMPORT_FIX='# Add parent directory to path for module imports
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), \"..\", \"lib\"))
sys.path.append(lib_path)

# Fix path for direct imports
sys.path.append(os.path.dirname(lib_path))

# Import modules from the proper paths
try:
    # First try the relative import approach'

# Loop through all Python files in the commands directory
for file in "$COMMANDS_DIR"/*.py; do
    if [ -f "$file" ]; then
        echo "Processing $file"
        
        # Create a temporary file
        temp_file="${file}.tmp"
        
        # Process the file
        awk -v import_fix="$IMPORT_FIX" '
        BEGIN { in_import_section = 0; processed = 0; }
        
        # Find import statements
        /^from core\./ { 
            if (!in_import_section && !processed) {
                # If we have not processed yet and we find a core import
                printf "%s\n", import_fix;
                in_import_section = 1;
                processed = 1;
            }
            
            # Store the original import for the except block
            if (in_import_section) {
                original = $0;
                # Change core to lib.core
                sub(/from core\./, "from lib.core.");
                lib_version = $0;
                
                # Output in try-except format
                print "    " original;
                imports_to_fix[imports_count++] = original "," lib_version;
            } else {
                print;
            }
            next;
        }
        
        # When we detect the first non-import, close the try-except block
        !/^(import|from)/ && in_import_section {
            print "except ImportError:";
            print "    # Fall back to direct import if needed";
            for (i = 0; i < imports_count; i++) {
                split(imports_to_fix[i], parts, ",");
                print "    " parts[2];
            }
            print "";
            in_import_section = 0;
        }
        
        # Default action is to print the line
        { print; }
        
        ' "$file" > "$temp_file"
        
        # Replace the original file
        mv "$temp_file" "$file"
    fi
done

echo "Import fixing complete with robust try-except approach."
echo "This should handle both import scenarios correctly."