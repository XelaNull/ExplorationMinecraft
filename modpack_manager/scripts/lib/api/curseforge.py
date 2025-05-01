#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CurseForge API client for Minecraft Modpack Manager.
Handles interactions with the CurseForge API for mod search and downloads.
Compatible with Python 2.7 and 3+.
"""

from __future__ import print_function, division, unicode_literals
import os
import sys
import json
import time
import requests
import logging

# Add parent directory to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import config

# Python 2/3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    from io import open
    from urllib2 import Request, urlopen, URLError, HTTPError
    from urllib import urlencode
else:
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError
    from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class CurseForgeAPI:
    """
    Client for CurseForge API.
    """
    
    def __init__(self):
        """Initialize the API client."""
        self.api_key = config.CURSEFORGE_API_KEY
        self.base_url = config.CURSEFORGE_API
        self.user_agent = config.USER_AGENT
        self.minecraft_game_id = config.MINECRAFT_GAME_ID
        self.mc_mods_class_id = config.MC_MODS_CLASS_ID
        self.last_request_time = 0
        self.request_cooldown = 1.5  # Minimum seconds between requests to avoid rate limiting
    
    def _make_request(self, endpoint, params=None):
        """
        Make a request to the CurseForge API with rate limiting and improved error handling.
        
        Args:
            endpoint (str): API endpoint
            params (dict, optional): Request parameters
            
        Returns:
            dict: Response JSON
        """
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "User-Agent": self.user_agent,
            "x-api-key": self.api_key
        }
        
        print(f"DEBUG: Making request to {url}")
        print(f"DEBUG: Headers: {headers}")
        print(f"DEBUG: Params: {params}")
        
        # Implement simple rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.request_cooldown:
            sleep_time = self.request_cooldown - time_since_last_request
            time.sleep(sleep_time)
        
        # Add retry logic for transient errors
        max_retries = 3
        retry_delay = 3  # Start with 3 seconds delay for CurseForge
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, params=params)
                self.last_request_time = time.time()  # Update last request time
                
                print(f"DEBUG: Response status code: {response.status_code}")
                
                # Handle common error cases
                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(f"DEBUG: Response JSON: {result}")
                        # Return the whole response, let the specific methods handle the structure
                        return result
                    except Exception as e:
                        print(f"DEBUG: Error parsing JSON: {e}")
                        print(f"DEBUG: Response text: {response.text[:200]}")  # First 200 chars
                        return None
                elif response.status_code == 404:
                    if attempt < max_retries - 1:
                        # Resource might truly not exist, but retry once in case of temporary issue
                        print(f"WARNING: Resource not found at {endpoint}, retry {attempt+1}/{max_retries}")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    print(f"ERROR: HTTP Error: {response.status_code} - Not Found")
                    print(f"ERROR: Error details: {response.text}")
                    return None
                elif response.status_code == 403:
                    print(f"ERROR: HTTP Error: {response.status_code} - Forbidden (API key issues or rate limit)")
                    print(f"ERROR: Error details: {response.text}")
                    time.sleep(retry_delay * 2)  # Wait longer for rate limit errors
                    retry_delay *= 2
                    continue
                elif response.status_code == 429:
                    print(f"WARNING: Rate limit exceeded, retrying after delay ({attempt+1}/{max_retries})")
                    # If response includes a Retry-After header, use that value
                    retry_after = int(response.headers.get('Retry-After', retry_delay))
                    time.sleep(retry_after)
                    retry_delay *= 2  # Exponential backoff
                    continue
                elif response.status_code >= 500:
                    print(f"WARNING: Server error {response.status_code}, retrying ({attempt+1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    print(f"ERROR: HTTP Error: {response.status_code} - {response.reason}")
                    print(f"ERROR: Error details: {response.text}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                print(f"ERROR: Request error: {e}")
                if attempt < max_retries - 1:
                    print(f"WARNING: Retrying after error ({attempt+1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                return None
        
        print(f"ERROR: Failed after {max_retries} attempts for {endpoint}")
        return None
    
    def search_mods(self, query, game_version=None, loader=None, limit=10):
        """
        Search for mods on CurseForge.
        
        Args:
            query (str): Search query
            game_version (str, optional): Minecraft version filter
            loader (str, optional): Mod loader filter (fabric, forge)
            limit (int, optional): Maximum number of results
            
        Returns:
            list: List of mod data dictionaries
        """
        endpoint = '/v1/mods/search'
        
        # Determine modLoaderType ID
        mod_loader_type = None
        if loader:
            if loader.lower() == 'forge':
                mod_loader_type = 1
            elif loader.lower() == 'fabric':
                mod_loader_type = 4
            elif loader.lower() == 'neoforge':
                mod_loader_type = 5
        
        params = {
            'gameId': self.minecraft_game_id,
            'classId': self.mc_mods_class_id,
            'searchFilter': query,
            'sortField': 2,  # Popularity
            'sortOrder': 'desc',
            'pageSize': limit
        }
        
        if game_version:
            params['gameVersion'] = game_version
        if mod_loader_type:
            params['modLoaderType'] = mod_loader_type
        
        try:
            response = self._make_request(endpoint, params=params)
            if not response:
                print(f"No results or invalid response from CurseForge API")
                return []
            
            if isinstance(response, list):  # Sometimes response is a list
                return response
            
            return response
        except Exception as e:
            print(f"Error searching mods: {e}")
            return []
    
    def get_mod(self, mod_id):
        """
        Get mod details from CurseForge.
        
        Args:
            mod_id (int): Mod ID
            
        Returns:
            dict: Mod data
        """
        endpoint = f'/v1/mods/{mod_id}'
        
        try:
            response = self._make_request(endpoint)
            print(f"DEBUG: Raw response from CurseForge API for mod {mod_id}: {response}")
            
            # More robust response handling
            if not response:
                print(f"Error: No response data for mod {mod_id}")
                return {}
                
            if isinstance(response, dict):
                data = response.get('data')
                if data:
                    return data
                print(f"Error: Response has no 'data' field: {response}")
                return {}
            else:
                print(f"Error: Unexpected response type: {type(response)}")
                return {}
        except Exception as e:
            print(f"Error getting mod details: {e}")
            return {}
    
    def get_mod_files(self, mod_id, game_version=None, loader=None):
        """
        Get available files for a mod.
        
        Args:
            mod_id (int): Mod ID
            game_version (str, optional): Minecraft version filter
            loader (str, optional): Mod loader filter (fabric, forge)
            
        Returns:
            list: List of file data dictionaries
        """
        endpoint = f'/v1/mods/{mod_id}/files'
        
        # Determine modLoaderType ID
        mod_loader_type = None
        if loader:
            if loader.lower() == 'forge':
                mod_loader_type = 1
            elif loader.lower() == 'fabric':
                mod_loader_type = 4
            elif loader.lower() == 'neoforge':
                mod_loader_type = 5
        
        params = {}
        if game_version:
            params['gameVersion'] = game_version
        if mod_loader_type:
            params['modLoaderType'] = mod_loader_type
        
        try:
            response = self._make_request(endpoint, params=params)
            
            # Handle various response formats
            if not response:
                return []
                
            if isinstance(response, dict):
                # Extract data from dictionary response
                data = response.get('data', [])
                if isinstance(data, list):
                    if len(data) > 0:
                        # Log what we found
                        print(f"Found {len(data)} files in CurseForge API response")
                        # Filter files by forge if loader is forge
                        if loader and loader.lower() == 'forge':
                            forge_files = []
                            for file in data:
                                # Check if this is explicitly a Forge file
                                game_versions = file.get('gameVersions', [])
                                if 'Forge' in game_versions:
                                    forge_files.append(file)
                            
                            if forge_files:
                                print(f"Filtered to {len(forge_files)} Forge-specific files")
                                return forge_files
                            # If no Forge-specific files, fall back to all files
                            print("No Forge-specific files found, using all files")
                    return data
                return []
            elif isinstance(response, list):
                # Response is already a list
                if len(response) > 0:
                    print(f"Found {len(response)} files in CurseForge API list response")
                    # Filter files by forge if loader is forge
                    if loader and loader.lower() == 'forge':
                        forge_files = []
                        for file in response:
                            # Check if this is explicitly a Forge file
                            game_versions = file.get('gameVersions', [])
                            if 'Forge' in game_versions:
                                forge_files.append(file)
                        
                        if forge_files:
                            print(f"Filtered to {len(forge_files)} Forge-specific files")
                            return forge_files
                        # If no Forge-specific files, fall back to all files
                        print("No Forge-specific files found, using all files")
                return response
            else:
                print(f"Unexpected response format: {type(response)}")
                return []
                
        except Exception as e:
            print(f"Error getting mod files: {e}")
            return []
    
    def get_download_url(self, mod_id, file_id):
        """
        Get download URL for a specific file.
        
        Args:
            mod_id (int): Mod ID
            file_id (int): File ID
            
        Returns:
            str: Download URL
        """
        # Direct URL construction for CurseForge files (bypassing the API)
        # This works for most CurseForge downloads without requiring the API key
        direct_url = f"https://edge.forgecdn.net/files/{str(file_id)[0:4]}/{str(file_id)[4:]}/file"
        print(f"Using direct file URL: {direct_url}")
        return direct_url
        
        # The API endpoint method below often doesn't work without proper authorization
        # Keeping it as fallback
        endpoint = f'/v1/mods/{mod_id}/files/{file_id}/download-url'
        
        try:
            response = self._make_request(endpoint)
            api_url = response.get('data', '')
            if api_url:
                print(f"API provided URL: {api_url}")
                return api_url
            else:
                print(f"API didn't provide URL, using direct URL")
                return direct_url
        except Exception as e:
            print(f"Error getting download URL from API: {e}")
            print(f"Falling back to direct URL")
            return direct_url
    
    def get_mod_dependencies(self, mod_id, file_id):
        """
        Get dependencies for a mod file.
        
        Args:
            mod_id (int): Mod ID
            file_id (int): File ID
            
        Returns:
            list: List of dependency dictionaries
        """
        endpoint = f'/v1/mods/{mod_id}/files/{file_id}'
        
        try:
            response = self._make_request(endpoint)
            file_data = response.get('data', {})
            return file_data.get('dependencies', [])
        except Exception as e:
            print(f"Error getting mod dependencies: {e}")
            return []

def main():
    """Test CurseForge API functionality."""
    api = CurseForgeAPI()
    
    print("Testing CurseForge API...")
    
    # Test search
    print("\nSearching for 'Create' mod:")
    results = api.search_mods('Create', game_version='1.20.1', loader='forge', limit=5)
    for i, mod in enumerate(results):
        print(f"{i+1}. {mod.get('name')} - {mod.get('id')}")
    
    # Test get mod details
    if results:
        mod_id = results[0].get('id')
        print(f"\nGetting details for mod {mod_id}:")
        mod_details = api.get_mod(mod_id)
        print(f"Name: {mod_details.get('name')}")
        print(f"Summary: {mod_details.get('summary')}")
        
        # Test get files
        print(f"\nGetting files for mod {mod_id}:")
        files = api.get_mod_files(mod_id, game_version='1.20.1', loader='forge')
        for i, file in enumerate(files[:3]):  # Show first 3 files
            print(f"{i+1}. {file.get('displayName')} - {file.get('fileName')}")
    
if __name__ == '__main__':
    main() 