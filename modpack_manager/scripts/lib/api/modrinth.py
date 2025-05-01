#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modrinth API client for Minecraft Modpack Manager.
Handles interactions with the Modrinth API for mod search and downloads.
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

class ModrinthAPI:
    """
    Client for Modrinth API.
    """
    
    def __init__(self):
        """Initialize the API client."""
        self.api_key = config.MODRINTH_API_KEY
        self.base_url = config.MODRINTH_API
        self.user_agent = config.USER_AGENT
        self.last_request_time = 0
        self.request_cooldown = 1.0  # Minimum seconds between requests to avoid rate limiting
    
    def _make_request(self, endpoint, params=None):
        """
        Make a request to the Modrinth API with rate limiting and improved error handling.
        
        Args:
            endpoint (str): API endpoint
            params (dict, optional): Request parameters
            
        Returns:
            dict: Response JSON
        """
        # Don't include leading slash in endpoint
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
            
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "User-Agent": self.user_agent,
            "Authorization": self.api_key
        }
        
        logger.debug(f"Making API request to: {url}")
        
        # Implement simple rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.request_cooldown:
            sleep_time = self.request_cooldown - time_since_last_request
            time.sleep(sleep_time)
        
        # Add retry logic for transient errors
        max_retries = 3
        retry_delay = 2  # Start with 2 seconds delay
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, params=params)
                self.last_request_time = time.time()  # Update last request time
                
                # Handle common error cases
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    if attempt < max_retries - 1:
                        # Resource might truly not exist, but retry once in case of temporary issue
                        logger.warning(f"Resource not found at {endpoint}, retry {attempt+1}/{max_retries}")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    logger.error(f"HTTP Error: {response.status_code} - Not Found")
                    logger.error(f"Error details: {response.text}")
                    return None
                elif response.status_code == 403:
                    logger.error(f"HTTP Error: {response.status_code} - Forbidden (API key issues or rate limit)")
                    time.sleep(retry_delay * 2)  # Wait longer for rate limit errors
                    retry_delay *= 2
                    continue
                elif response.status_code == 429:
                    logger.warning(f"Rate limit exceeded, retrying after delay ({attempt+1}/{max_retries})")
                    # If response includes a Retry-After header, use that value
                    retry_after = int(response.headers.get('Retry-After', retry_delay))
                    time.sleep(retry_after)
                    retry_delay *= 2  # Exponential backoff
                    continue
                elif response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code}, retrying ({attempt+1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    logger.error(f"HTTP Error: {response.status_code} - {response.reason}")
                    logger.error(f"Error details: {response.text}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}")
                if attempt < max_retries - 1:
                    logger.warning(f"Retrying after error ({attempt+1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                return None
        
        logger.error(f"Failed after {max_retries} attempts for {endpoint}")
        return None
    
    def search_mods(self, query, game_version=None, loader=None, limit=10):
        """
        Search for mods.
        
        Args:
            query (str): Search query
            game_version (str, optional): Minecraft version
            loader (str, optional): Mod loader (fabric, forge)
            limit (int, optional): Maximum number of results
            
        Returns:
            list: List of mods matching the search criteria
        """
        params = {
            'query': query,
            'limit': limit,
            'facets': json.dumps([
                # Format facets as Modrinth API expects
                ["project_type:mod"]
            ])
        }
        
        # Add game version facet if provided
        if game_version:
            params['facets'] = json.dumps([
                ["project_type:mod"],
                [f"versions:{game_version}"]
            ])
            
        # Add loader facet if provided
        if loader:
            loader = loader.lower()
            loader_facet = f"categories:{loader}"
            
            # Update facets
            facets = json.loads(params['facets'])
            facets.append([loader_facet])
            params['facets'] = json.dumps(facets)
            
        result = self._make_request("search", params)
        return result.get('hits', []) if result else []
    
    def get_mod(self, mod_id):
        """
        Get details for a specific mod.
        
        Args:
            mod_id (str): Mod ID (slug or ID)
            
        Returns:
            dict: Mod details
        """
        return self._make_request(f"project/{mod_id}")
    
    def get_mod_versions(self, mod_id, minecraft_version=None, loader=None, featured=True):
        """
        Get versions for a specific mod.
        
        Args:
            mod_id (str): Mod ID (slug or ID)
            minecraft_version (str, optional): Minecraft version
            loader (str, optional): Mod loader (fabric, forge)
            featured (bool, optional): Only return featured versions
            
        Returns:
            list: List of mod versions
        """
        params = {}
        
        # Add game version filter if provided
        if minecraft_version:
            params['game_versions'] = f"[\"{minecraft_version}\"]"
            
        # Add loader filter if provided
        if loader:
            params['loaders'] = f"[\"{loader.lower()}\"]"
            
        if featured:
            params['featured'] = 'true'
            
        result = self._make_request(f"project/{mod_id}/version", params)
        
        # Sort by date (newest first)
        if result:
            result.sort(key=lambda v: v.get('date_published', ''), reverse=True)
            
            # Strictly filter mods by loader type
            if loader:
                # Filter to only include versions that are specific to our loader
                # and don't include other loaders like 'fabric' or 'neoforge'
                loader_lower = loader.lower()
                filtered_result = []
                
                for version in result:
                    version_loaders = version.get('loaders', [])
                    # Only include versions where:
                    # 1. Our exact loader is included
                    # 2. No other loader types are included (except for 'quilt' if loader is 'fabric')
                    if loader_lower in version_loaders:
                        # For forge, strictly only include forge versions
                        if loader_lower == 'forge':
                            if len(version_loaders) == 1 or (len(version_loaders) == 2 and 'neoforge' in version_loaders):
                                filtered_result.append(version)
                                continue
                        # Otherwise, include versions for our loader (less strict for fabric/quilt)
                        else:
                            filtered_result.append(version)
                
                # If we found filtered versions, use them instead
                if filtered_result:
                    print(f"Found {len(filtered_result)} versions specifically for {loader}")
                    return filtered_result
                else:
                    print(f"Warning: No strict {loader} versions found. Falling back to broader compatibility.")
            
        return result
    
    def get_version_download_url(self, version_id):
        """
        Get download URL for a specific version.
        
        Args:
            version_id (str): Version ID
            
        Returns:
            str: Download URL
        """
        endpoint = f'version/{version_id}'
        
        # First, get the version data
        version_data = self._make_request(endpoint)
        
        if not version_data:
            print(f"ERROR: Version {version_id} not found")
            return None
            
        # Check if there are files
        files = version_data.get('files', [])
        if not files:
            print(f"ERROR: No files found for version {version_id}")
            return None
            
        # Get the primary file
        primary_files = [f for f in files if f.get('primary', False)]
        if primary_files:
            download_url = primary_files[0].get('url')
            print(f"Found download URL: {download_url}")
            return download_url
        
        # If no primary file, use the first file
        if files:
            download_url = files[0].get('url')
            print(f"No primary file found, using first file: {download_url}")
            return download_url
            
        print(f"ERROR: Could not find download URL for version {version_id}")
        return None
    
    def get_mod_dependencies(self, mod_id, version_id):
        """
        Get dependencies for a specific mod version.
        
        Args:
            mod_id (str): Mod ID (slug or ID)
            version_id (str): Version ID
            
        Returns:
            list: List of dependencies
        """
        version = self._make_request(f"version/{version_id}")
        return version.get('dependencies', []) if version else []

def main():
    """Test Modrinth API functionality."""
    api = ModrinthAPI()
    
    print("Testing Modrinth API...")
    
    # Test search
    print("\nSearching for 'Create' mod:")
    results = api.search_mods('Create', game_version='1.20.1', loader='fabric', limit=5)
    for i, mod in enumerate(results):
        print(f"{i+1}. {mod.get('title')} - {mod.get('project_id')}")
    
    # Test get mod details
    if results:
        mod_id = results[0].get('project_id')
        print(f"\nGetting details for mod {mod_id}:")
        mod_details = api.get_mod(mod_id)
        print(f"Name: {mod_details.get('title')}")
        print(f"Description: {mod_details.get('description')}")
        
        # Test get versions
        print(f"\nGetting versions for mod {mod_id}:")
        versions = api.get_mod_versions(mod_id, game_version='1.20.1', loader='fabric')
        for i, version in enumerate(versions[:3]):  # Show first 3 versions
            print(f"{i+1}. {version.get('name')} - {version.get('version_number')}")
    
if __name__ == '__main__':
    main() 