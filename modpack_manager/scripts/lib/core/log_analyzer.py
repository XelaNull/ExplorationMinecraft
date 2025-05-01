#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Log Analyzer Module for Minecraft Modpack Manager

Analyzes Minecraft server logs to detect milestones, errors, warnings,
mod loading times, and datapack loading information.
"""

import re
import json
import logging
import time
from datetime import datetime
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('log_analyzer')

class LogAnalyzer:
    """
    Analyzes Minecraft server logs to extract useful information
    about the server startup process and health.
    """
    
    def __init__(self):
        """Initialize the LogAnalyzer."""
        # Patterns for detecting various log events
        self.patterns = {
            # Server start and completion patterns
            "forge_start": re.compile(r"Forge mod loading, version (.+), for MC (.+) with MCP"),
            "server_started": re.compile(r"Done \(\d+\.\d+s\)! For help, type \"help\""),
            
            # Error patterns
            "generic_error": re.compile(r"\[ERROR\]|\[FATAL\]"),
            "mod_crash": re.compile(r"(Exception (?:while|caused by|in) (?:loading|initializing) mod)"),
            "missing_dependency": re.compile(r"(Missing(?:\s+required)?\s+dependency):?\s+([^\n]+)"),
            "class_loading_error": re.compile(r"java\.lang\.ClassNotFoundException: ([^\n]+)"),
            
            # Mod loading patterns
            "mod_loading": re.compile(r"Loading mod: ([^\n]+)"),
            "mod_loaded": re.compile(r"Mod ([^\n]+) loaded"),
            "mod_loading_time": re.compile(r"Mod ([^\n]+) loaded in (\d+(?:\.\d+)?) (?:s|ms)"),
        }
    
    def analyze_server_logs(self, profile_name, timeout=300):
        """
        Analyze server logs for a given profile.
        
        Args:
            profile_name (str): The name of the profile to analyze logs for
            timeout (int): Maximum time to wait for server startup (seconds)
            
        Returns:
            dict: Analysis results
        """
        # Import here to avoid circular imports
        from core.server_manager import ServerManager
        
        server_manager = ServerManager()
        
        # Check if the server is running
        if not server_manager.is_running(profile_name):
            logger.error(f"Server for profile '{profile_name}' is not running")
            return {
                "success": False,
                "server_started": False,
                "errors": ["Server is not running"]
            }
        
        start_time = time.time()
        end_time = start_time + timeout
        
        # Initialize results
        results = {
            "success": False,
            "server_started": False,
            "errors": [],
            "warnings": [],
            "mod_count": 0,
            "loaded_mod_count": 0,
            "mod_loading_times": {},
            "forge_version": "unknown",
            "minecraft_version": "unknown",
            "slow_mods": []
        }
        
        # Track mods being loaded
        mods_being_loaded = set()
        mods_loaded = set()
        
        while time.time() < end_time:
            # Get logs
            logs = server_manager.get_logs(profile_name)
            
            if not logs:
                logger.warning("No logs available yet, waiting...")
                time.sleep(5)
                continue
            
            # Check for Forge startup
            forge_match = self.patterns["forge_start"].search(logs)
            if forge_match:
                results["forge_version"] = forge_match.group(1)
                results["minecraft_version"] = forge_match.group(2)
            
            # Check for server started
            if self.patterns["server_started"].search(logs):
                results["server_started"] = True
                results["success"] = True
                break
            
            # Parse errors
            for error_match in self.patterns["generic_error"].finditer(logs):
                error_line = logs[error_match.start():logs.find('\n', error_match.start())].strip()
                if error_line not in results["errors"]:
                    results["errors"].append(error_line)
            
            # Parse mod crashes
            for crash_match in self.patterns["mod_crash"].finditer(logs):
                crash_line = logs[crash_match.start():logs.find('\n', crash_match.start()) + 100].strip()
                if crash_line not in results["errors"]:
                    results["errors"].append(crash_line)
            
            # Parse missing dependencies
            for dep_match in self.patterns["missing_dependency"].finditer(logs):
                dependency = dep_match.group(2).strip()
                if dependency not in results.get("missing_dependencies", []):
                    if "missing_dependencies" not in results:
                        results["missing_dependencies"] = []
                    results["missing_dependencies"].append(dependency)
            
            # Parse class loading errors
            for class_error_match in self.patterns["class_loading_error"].finditer(logs):
                class_name = class_error_match.group(1).strip()
                if class_name not in results.get("class_loading_issues", []):
                    if "class_loading_issues" not in results:
                        results["class_loading_issues"] = []
                    results["class_loading_issues"].append(class_name)
            
            # Track mod loading
            for mod_loading_match in self.patterns["mod_loading"].finditer(logs):
                mod_name = mod_loading_match.group(1).strip()
                mods_being_loaded.add(mod_name)
            
            # Track mods loaded
            for mod_loaded_match in self.patterns["mod_loaded"].finditer(logs):
                mod_name = mod_loaded_match.group(1).strip()
                mods_loaded.add(mod_name)
            
            # Track mod loading times
            for mod_time_match in self.patterns["mod_loading_time"].finditer(logs):
                mod_name = mod_time_match.group(1).strip()
                load_time = float(mod_time_match.group(2))
                
                # Convert to milliseconds if in seconds
                if "ms" not in mod_time_match.group(0):
                    load_time *= 1000
                
                results["mod_loading_times"][mod_name] = load_time
            
            # Update counts
            results["mod_count"] = len(mods_being_loaded)
            results["loaded_mod_count"] = len(mods_loaded)
            
            # Sleep a bit before checking again
            time.sleep(5)
        
        # Calculate slow mods
        if results["mod_loading_times"]:
            # Sort mods by loading time (slowest first)
            sorted_mods = sorted(
                results["mod_loading_times"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            results["slow_mods"] = [
                {"name": name, "time": time_ms} 
                for name, time_ms in sorted_mods[:10]
            ]
        
        # If we timed out and the server didn't start
        if not results["server_started"]:
            logger.warning(f"Server did not start within {timeout} seconds")
            if "Server timed out" not in results["errors"]:
                results["errors"].append(f"Server did not start within {timeout} seconds")
        
        return results
    
    def parse_line(self, line):
        """
        Parse a single log line to extract useful information.
        
        Args:
            line (str): The log line to parse
            
        Returns:
            tuple: (log_type, component, message)
        """
        # Default values
        log_type = "INFO"
        component = "unknown"
        message = line.strip()
        
        # Try to match against common log patterns
        # Example line: [12:34:56] [Server thread/INFO] [minecraft/Server]: Done (10.5s)! For help, type "help"
        match = re.match(r'\[\d+:\d+:\d+\] \[([^/]+)/([A-Z]+)\] \[([^:]+)\]: (.*)', line)
        if match:
            thread, log_type, component, message = match.groups()
        
        return log_type, component, message

def main():
    """Run a test of the LogAnalyzer with a sample log file."""
    import sys
    
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <log_file>")
        return 1
    
    log_file = sys.argv[1]
    
    # Create a sample profile
    profile = {
        'minecraft_version': '1.20.1',
        'loader_type': 'forge',
        'loader_version': '47.3.0'
    }
    
    # Initialize log analyzer
    analyzer = LogAnalyzer()
    
    # Read logs
    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
        logs = f.read()
    
    # Analyze logs
    results = analyzer.analyze_server_logs(log_file)
    
    # Print results
    print(json.dumps(results, indent=2, default=str))
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main()) 