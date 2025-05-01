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

# Try direct access to core module folder
core_path = os.path.join(lib_path, 'core')
if os.path.exists(core_path) and core_path not in sys.path:
    sys.path.insert(0, core_path)

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
        try:
            # Try direct import using absolute imports
            sys.path.insert(0, os.path.dirname(core_path))
            from core.profile_manager import ProfileManager
            from core.dependency_resolver import DependencyResolver
        except ImportError:
            # Try a last-resort approach by directly importing from path
            try:
                import importlib.util
                profile_manager_path = os.path.join(core_path, 'profile_manager.py')
                resolver_path = os.path.join(core_path, 'dependency_resolver.py')
                
                if os.path.exists(profile_manager_path) and os.path.exists(resolver_path):
                    spec1 = importlib.util.spec_from_file_location("profile_manager", profile_manager_path)
                    profile_manager = importlib.util.module_from_spec(spec1)
                    spec1.loader.exec_module(profile_manager)
                    
                    spec2 = importlib.util.spec_from_file_location("dependency_resolver", resolver_path)
                    dependency_resolver = importlib.util.module_from_spec(spec2)
                    spec2.loader.exec_module(dependency_resolver)
                    
                    ProfileManager = profile_manager.ProfileManager
                    DependencyResolver = dependency_resolver.DependencyResolver
                else:
                    raise ImportError("Could not find module files")
            except Exception as e2:
                # Print detailed error information for debugging
                print(f"Error: Failed to import required modules.")
                print(f"Python path: {sys.path}")
                print(f"Script directory: {script_dir}")
                print(f"Lib path: {lib_path}")
                print(f"Core path: {core_path}")
                print(f"Original error: {e}")
                print(f"Last resort error: {e2}")
                print(f"Core module exists: {os.path.exists(core_path)}")
                print(f"Profile manager exists: {os.path.exists(os.path.join(core_path, 'profile_manager.py'))}")
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