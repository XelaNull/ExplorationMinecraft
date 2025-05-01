#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mod search module for Minecraft Modpack Manager.
Handles searching for mods across multiple sources.
Compatible with Python 2.7 and 3+.
"""

from __future__ import print_function, division, unicode_literals
import os
import sys
import json
import time

# Add parent directory to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import config
from api.modrinth import ModrinthAPI
from api.curseforge import CurseForgeAPI

# Python 2/3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    from io import open

class ModSearch:
    """
    Handles searching for mods across multiple sources.
    """
    
    def __init__(self):
        """Initialize API clients."""
        self.modrinth_api = ModrinthAPI()
        self.curseforge_api = CurseForgeAPI()
    
    def search_modrinth(self, query, game_version=None, loader=None, limit=10):
        """
        Search for mods on Modrinth.
        
        Args:
            query (str): Search query
            game_version (str, optional): Minecraft version filter
            loader (str, optional): Mod loader filter (fabric, forge)
            limit (int, optional): Maximum number of results
            
        Returns:
            list: List of standardized mod data dictionaries
        """
        print(f"Searching Modrinth for '{query}'...")
        
        # Search Modrinth
        results = self.modrinth_api.search_mods(query, game_version, loader, limit)
        
        # Standardize results
        standardized = []
        for result in results:
            mod = {
                "name": result.get('title'),
                "id": result.get('project_id'),
                "description": result.get('description'),
                "author": result.get('author'),
                "downloads": result.get('downloads'),
                "created": result.get('date_created'),
                "updated": result.get('date_modified'),
                "source": "modrinth"
            }
            standardized.append(mod)
        
        return standardized
    
    def search_curseforge(self, query, game_version=None, loader=None, limit=10):
        """
        Search for mods on CurseForge.
        
        Args:
            query (str): Search query
            game_version (str, optional): Minecraft version filter
            loader (str, optional): Mod loader filter (fabric, forge)
            limit (int, optional): Maximum number of results
            
        Returns:
            list: List of standardized mod data dictionaries
        """
        print(f"Searching CurseForge for '{query}'...")
        
        # Search CurseForge
        results = self.curseforge_api.search_mods(query, game_version, loader, limit)
        
        # Standardize results
        standardized = []
        
        # Check if results is a valid list
        if not isinstance(results, list):
            print("Error: Invalid response format from CurseForge API")
            return []
            
        try:
            for result in results:
                if not isinstance(result, dict):
                    continue  # Skip non-dictionary results
                    
                # Extract safe data with fallbacks
                mod = {
                    "name": result.get('name', 'Unknown Mod'),
                    "id": result.get('id', 0),
                    "description": result.get('summary', 'No description available'),
                    "slug": result.get('slug', ''),
                    "downloads": result.get('downloadCount', 0),
                    "source": "curseforge"
                }
                
                # Safely extract author
                authors = result.get('authors', [])
                if authors and isinstance(authors, list) and len(authors) > 0:
                    mod["author"] = authors[0].get('name', 'Unknown') if isinstance(authors[0], dict) else 'Unknown'
                else:
                    mod["author"] = 'Unknown'
                    
                # Dates
                mod["created"] = result.get('dateCreated', '')
                mod["updated"] = result.get('dateModified', '')
                
                # Add loaders information
                mod["loaders"] = []
                if 'latestFilesIndexes' in result:
                    for file_index in result.get('latestFilesIndexes', []):
                        modloader_type = file_index.get('modLoader', 0)
                        if modloader_type == 1:
                            mod["loaders"].append('forge')
                        elif modloader_type == 4:
                            mod["loaders"].append('fabric')
                        elif modloader_type == 5:
                            mod["loaders"].append('neoforge')
                
                standardized.append(mod)
        except Exception as e:
            print(f"Error processing CurseForge results: {e}")
            
        return standardized
    
    def search(self, query, game_version=None, loader=None, limit=10, source="both"):
        """
        Search for mods across all sources.
        
        Args:
            query (str): Search query
            game_version (str, optional): Minecraft version filter
            loader (str, optional): Mod loader filter (fabric, forge)
            limit (int, optional): Maximum number of results per source
            source (str, optional): Source to search ('modrinth', 'curseforge', or 'both')
            
        Returns:
            list: List of standardized mod data dictionaries
        """
        results = []
        
        if source.lower() in ["modrinth", "both"]:
            modrinth_results = self.search_modrinth(query, game_version, loader, limit)
            results.extend(modrinth_results)
        
        if source.lower() in ["curseforge", "both"]:
            curseforge_results = self.search_curseforge(query, game_version, loader, limit)
            results.extend(curseforge_results)
        
        # Sort by downloads (popularity)
        results.sort(key=lambda x: x.get('downloads', 0), reverse=True)
        
        return results
    
    def get_mod_details(self, mod_id, source):
        """
        Get detailed information about a mod.
        
        Args:
            mod_id (str or int): Mod ID or slug
            source (str): Source ('modrinth' or 'curseforge')
            
        Returns:
            dict: Detailed mod data
        """
        if source.lower() == "modrinth":
            mod = self.modrinth_api.get_mod(mod_id)
            
            # Format the data
            return {
                "name": mod.get('title'),
                "id": mod.get('id'),
                "description": mod.get('description'),
                "body": mod.get('body'),
                "author": mod.get('author'),
                "downloads": mod.get('downloads'),
                "created": mod.get('published'),
                "updated": mod.get('updated'),
                "categories": mod.get('categories', []),
                "source": "modrinth"
            }
            
        elif source.lower() == "curseforge":
            # Convert string ID to integer if needed
            if isinstance(mod_id, str) and mod_id.isdigit():
                mod_id = int(mod_id)
                
            mod = self.curseforge_api.get_mod(mod_id)
            
            # Format the data
            return {
                "name": mod.get('name'),
                "id": mod.get('id'),
                "description": mod.get('summary'),
                "body": mod.get('description'),
                "author": mod.get('authors')[0].get('name') if mod.get('authors') else "Unknown",
                "downloads": mod.get('downloadCount'),
                "created": mod.get('dateCreated'),
                "updated": mod.get('dateModified'),
                "categories": [cat.get('name') for cat in mod.get('categories', [])],
                "source": "curseforge"
            }
        
        else:
            print(f"Error: Unsupported source {source}")
            return None
    
    def get_mod_versions(self, mod_id, source, game_version=None, loader=None):
        """
        Get available versions for a mod.
        
        Args:
            mod_id (str or int): Mod ID or slug
            source (str): Source ('modrinth' or 'curseforge')
            game_version (str, optional): Minecraft version filter
            loader (str, optional): Mod loader filter (fabric, forge)
            
        Returns:
            list: List of version data
        """
        if source.lower() == "modrinth":
            versions = self.modrinth_api.get_mod_versions(mod_id, game_version, loader)
            
            # Format the data
            return [{
                "id": version.get('id'),
                "name": version.get('name'),
                "version_number": version.get('version_number'),
                "game_versions": version.get('game_versions', []),
                "loaders": version.get('loaders', []),
                "downloads": version.get('downloads'),
                "date_published": version.get('date_published')
            } for version in versions]
            
        elif source.lower() == "curseforge":
            # Convert string ID to integer if needed
            if isinstance(mod_id, str) and mod_id.isdigit():
                mod_id = int(mod_id)
                
            files = self.curseforge_api.get_mod_files(mod_id, game_version, loader)
            
            # Format the data
            return [{
                "id": file.get('id'),
                "name": file.get('displayName'),
                "file_name": file.get('fileName'),
                "game_versions": file.get('gameVersions', []),
                "downloads": file.get('downloadCount'),
                "date_published": file.get('fileDate')
            } for file in files]
        
        else:
            print(f"Error: Unsupported source {source}")
            return []

def main():
    """Test mod search functionality."""
    searcher = ModSearch()
    
    print("==== Mod Search Test ====")
    
    # Test search
    query = "Create"
    minecraft_version = "1.20.1"
    results = searcher.search(query, minecraft_version, source="both", limit=5)
    
    print(f"\nSearch results for '{query}' (Minecraft {minecraft_version}):")
    for i, result in enumerate(results):
        print(f"{i+1}. {result['name']} ({result['source']})")
        print(f"   ID: {result['id']}")
        print(f"   Author: {result['author']}")
        print(f"   Downloads: {result['downloads']}")
        print(f"   Description: {result['description'][:100]}...")
    
    # Test get mod details
    if results:
        result = results[0]
        mod_id = result['id']
        source = result['source']
        
        print(f"\nGetting details for {result['name']} ({source}):")
        details = searcher.get_mod_details(mod_id, source)
        print(f"Name: {details['name']}")
        print(f"Author: {details['author']}")
        print(f"Downloads: {details['downloads']}")
        print(f"Categories: {', '.join(details['categories'])}")
        
        # Test get mod versions
        print(f"\nGetting versions for {result['name']} ({source}):")
        versions = searcher.get_mod_versions(mod_id, source, minecraft_version)
        for i, version in enumerate(versions[:3]):  # Show first 3 versions
            print(f"{i+1}. {version['name']} - Game versions: {', '.join(version['game_versions'][:3])}")
    
if __name__ == '__main__':
    main() 