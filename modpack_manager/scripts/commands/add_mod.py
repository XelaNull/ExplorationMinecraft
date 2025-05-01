#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Add a mod to a modpack profile.
"""

import sys
import os
import argparse

# Add parent directory to path for module imports
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(lib_path)

from core.profile_manager import ProfileManager

def main():
    """Handle adding a mod to a profile."""
    parser = argparse.ArgumentParser(description='Add a mod to a profile.')
    parser.add_argument('mod_id', help='Mod ID or slug')
    parser.add_argument('--profile', required=True, help='Profile name')
    parser.add_argument('--source', required=True, choices=['modrinth', 'curseforge'], help='Mod source')
    parser.add_argument('--side', choices=['client', 'server', 'both'], default='both', 
                       help='Whether the mod is client-only, server-only, or both (default: both)')
    
    args = parser.parse_args()
    
    manager = ProfileManager()
    
    if manager.add_mod(args.profile, args.mod_id, args.source, args.side):
        print(f"Mod '{args.mod_id}' added to profile '{args.profile}'.")
    else:
        print(f"Failed to add mod '{args.mod_id}' to profile '{args.profile}'.")
        sys.exit(1)

if __name__ == '__main__':
    main() 