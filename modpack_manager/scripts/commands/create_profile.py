#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Create a new modpack profile.
"""

import sys
import os
import argparse

# Add parent directory to path for module imports
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(lib_path)

from core.profile_manager import ProfileManager

def main():
    """Handle the create profile command."""
    parser = argparse.ArgumentParser(description='Create a new modpack profile.')
    parser.add_argument('name', help='Profile name')
    parser.add_argument('--minecraft', required=True, help='Minecraft version')
    parser.add_argument('--loader', required=True, choices=['fabric', 'forge'], help='Mod loader')
    parser.add_argument('--loader-version', required=True, help='Mod loader version')
    parser.add_argument('--description', help='Profile description')
    
    args = parser.parse_args()
    
    manager = ProfileManager()
    profile = manager.create_profile(
        args.name,
        args.minecraft,
        args.loader,
        args.loader_version,
        args.description
    )
    
    if profile:
        print(f"Profile '{args.name}' created successfully.")
    else:
        print(f"Failed to create profile '{args.name}'.")
        sys.exit(1)

if __name__ == '__main__':
    main() 