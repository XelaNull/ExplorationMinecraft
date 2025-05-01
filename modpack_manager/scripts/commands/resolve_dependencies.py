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
lib_path = os.path.abspath(os.path.join(script_dir, '..', 'lib'))
scripts_path = os.path.abspath(os.path.join(script_dir, '..'))

# Add paths to Python path if they're not already there
for path in [lib_path, scripts_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Try each possible import path in sequence
try:
    # Try direct core import first (if PYTHONPATH is set correctly)
    from core.profile_manager import ProfileManager
    from core.dependency_resolver import DependencyResolver
except ImportError as e:
    try:
        # Try relative import from lib
        from lib.core.profile_manager import ProfileManager
        from lib.core.dependency_resolver import DependencyResolver
    except ImportError:
        # Print detailed error information for debugging
        print(f"Error: Failed to import required modules.")
        print(f"Python path: {sys.path}")
        print(f"Script directory: {script_dir}")
        print(f"Lib path: {lib_path}")
        print(f"Original error: {e}")
        sys.exit(1)

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