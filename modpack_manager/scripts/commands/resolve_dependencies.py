#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Resolve dependencies for a modpack profile.
"""

import sys
import os
import argparse

# Add parent directory to path for module imports
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(lib_path)

# Fix path for direct imports
sys.path.append(os.path.dirname(lib_path))

# Import modules from the proper paths
try:
    # First try the relative import approach
    from core.profile_manager import ProfileManager
    from core.dependency_resolver import DependencyResolver
except ImportError:
    # Fall back to direct import if needed
    from lib.core.profile_manager import ProfileManager
    from lib.core.dependency_resolver import DependencyResolver

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