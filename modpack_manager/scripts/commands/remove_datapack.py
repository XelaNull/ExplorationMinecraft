#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Remove a data pack from a modpack profile.
"""

import sys
import os
import argparse

# Add parent directory to path for module imports
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(lib_path)

from core.profile_manager import ProfileManager

def main():
    """Handle removing a data pack from a profile."""
    parser = argparse.ArgumentParser(description='Remove a data pack from a profile.')
    parser.add_argument('datapack_id', help='Data pack ID or slug')
    parser.add_argument('--profile', required=True, help='Profile name')
    
    args = parser.parse_args()
    
    manager = ProfileManager()
    
    if manager.remove_datapack(args.profile, args.datapack_id):
        print(f"Data pack '{args.datapack_id}' removed from profile '{args.profile}'.")
    else:
        print(f"Failed to remove data pack '{args.datapack_id}' from profile '{args.profile}'.")
        sys.exit(1)

if __name__ == '__main__':
    main() 