#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Add a data pack to a modpack profile.
"""

import sys
import os
import argparse

# Add parent directory to path for module imports
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(lib_path)

from lib.core.profile_manager import ProfileManager

def main():
    """Handle adding a data pack to a profile."""
    parser = argparse.ArgumentParser(description='Add a data pack to a profile.')
    parser.add_argument('datapack_id', help='Data pack ID or slug')
    parser.add_argument('--profile', required=True, help='Profile name')
    parser.add_argument('--source', required=True, choices=['modrinth', 'curseforge', 'both'], help='Data pack source')
    
    args = parser.parse_args()
    
    manager = ProfileManager()
    
    if manager.add_datapack(args.profile, args.datapack_id, args.source):
        print(f"Data pack '{args.datapack_id}' added to profile '{args.profile}'.")
    else:
        print(f"Failed to add data pack '{args.datapack_id}' to profile '{args.profile}'.")
        sys.exit(1)

if __name__ == '__main__':
    main() 