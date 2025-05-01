#!/bin/bash
# Quick fix script for resolve_dependencies.py

# Directory setup
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/modpack_manager/scripts"
FILE_PATH="$SCRIPTS_DIR/commands/resolve_dependencies.py"

echo "Fixing resolve_dependencies.py..."

# Check if file exists
if [ ! -f "$FILE_PATH" ]; then
    echo "Error: File not found at $FILE_PATH"
    exit 1
fi

# Create a backup
cp "$FILE_PATH" "${FILE_PATH}.bak"

# Replace the import section with direct importing
sed -i 's/from lib\.core\.profile_manager/from core.profile_manager/g' "$FILE_PATH"
sed -i 's/from lib\.core\.dependency_resolver/from core.dependency_resolver/g' "$FILE_PATH"

# Fix the path setup
cat > "$FILE_PATH.tmp" << EOF
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Resolve dependencies for a modpack profile.
"""

import sys
import os
import argparse

# Add parent directory to path for module imports
script_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.join(os.path.dirname(script_dir), 'lib')
sys.path.insert(0, lib_dir)

# Import modules
from core.profile_manager import ProfileManager
from core.dependency_resolver import DependencyResolver

def main():
    """Handle resolving dependencies for a profile."""
    parser = argparse.ArgumentParser(description='Resolve dependencies for a profile.')
    parser.add_argument('--profile', required=True, help='Profile name')
    parser.add_argument('--datapack-only', action='store_true', help='Only resolve datapack dependencies')
    
    args = parser.parse_args()
    
    manager = ProfileManager()
    resolver = DependencyResolver()
    
    profile = manager.load_profile(args.profile)
    if not profile:
        print(f"Profile '{args.profile}' not found.")
        sys.exit(1)
    
    print(f"Resolving dependencies for profile '{args.profile}'...")
    
    # Resolve dependencies
    updated_profile = resolver.resolve_dependencies(profile)
    
    if updated_profile != profile:
        manager.save_profile(updated_profile)
        print("Profile updated with new dependencies and datapacks.")
    else:
        print("No new dependencies or datapacks found.")

if __name__ == '__main__':
    main()
EOF

# Replace the original file with the fixed version
mv "$FILE_PATH.tmp" "$FILE_PATH"
chmod +x "$FILE_PATH"

echo "Fix complete for resolve_dependencies.py"
echo "The script should now directly import from 'core' module."