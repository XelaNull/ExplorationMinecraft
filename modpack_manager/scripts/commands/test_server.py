#!/usr/bin/env python
"""
Test Server Script

This script deploys a Minecraft server for testing, monitors its logs,
and provides a detailed report on startup performance and any issues detected.
"""

import os
import sys
import json
import time
import logging
import argparse
import datetime
import tempfile
import subprocess
from pathlib import Path

# Add the parent directory to sys.path to be able to import from lib
script_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.join(os.path.dirname(script_dir), 'lib')
sys.path.insert(0, lib_dir)

from lib.core.profile_manager import ProfileManager
from lib.core.server_manager import ServerManager
from lib.core.log_analyzer import LogAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_server")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test a Minecraft server deployment")
    parser.add_argument("--profile", required=True, help="Name of the modpack profile to test")
    parser.add_argument("--timeout", type=int, default=300, help="Server startup timeout in seconds (default: 300)")
    parser.add_argument("--full-report", action="store_true", help="Generate a detailed report including all mods")
    parser.add_argument("--output", help="Path to save the report as JSON")
    
    return parser.parse_args()

def deploy_server(profile_name):
    """
    Deploy the server for testing.
    
    Args:
        profile_name (str): The name of the profile to deploy
        
    Returns:
        bool: True if deployment was successful, False otherwise
    """
    logger.info(f"Deploying server for profile '{profile_name}'")
    
    try:
        server_manager = ServerManager()
        
        # Stop any existing instance
        if server_manager.is_running(profile_name):
            logger.info(f"Stopping existing server for '{profile_name}'")
            server_manager.stop_server(profile_name)
            time.sleep(5)  # Give it time to stop
        
        # Deploy the server
        success = server_manager.deploy_server(profile_name)
        if not success:
            logger.error(f"Failed to deploy server for profile '{profile_name}'")
            return False
        
        logger.info(f"Server for profile '{profile_name}' deployed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error deploying server: {str(e)}")
        return False

def test_server(profile_name, timeout=300):
    """
    Test the server by starting it and analyzing logs.
    
    Args:
        profile_name (str): The name of the profile to test
        timeout (int): Maximum time to wait for server startup (seconds)
        
    Returns:
        dict: Analysis results
    """
    logger.info(f"Testing server for profile '{profile_name}' with timeout {timeout}s")
    
    try:
        server_manager = ServerManager()
        
        # Start the server
        success = server_manager.start_server(profile_name)
        if not success:
            logger.error(f"Failed to start server for profile '{profile_name}'")
            return {
                "success": False,
                "server_started": False,
                "errors": ["Failed to start server"]
            }
        
        logger.info(f"Server for profile '{profile_name}' started, analyzing logs...")
        
        # Analyze logs
        analyzer = LogAnalyzer()
        results = analyzer.analyze_server_logs(profile_name, timeout)
        
        # Stop the server
        server_manager.stop_server(profile_name)
        
        return results
    
    except Exception as e:
        logger.error(f"Error testing server: {str(e)}")
        # Ensure server is stopped even if an exception occurs
        try:
            server_manager = ServerManager()
            server_manager.stop_server(profile_name)
        except:
            pass
        
        return {
            "success": False,
            "server_started": False,
            "errors": [f"Error during testing: {str(e)}"]
        }

def generate_report(profile_name, results, full_report=False):
    """
    Generate a detailed report from the test results.
    
    Args:
        profile_name (str): The name of the profile tested
        results (dict): The raw test results
        full_report (bool): Whether to include full details
        
    Returns:
        dict: The formatted report
    """
    # Get profile details
    profile_manager = ProfileManager()
    profile = profile_manager.get_profile(profile_name)
    
    # Basic report structure
    report = {
        "profile_name": profile_name,
        "game_version": profile.get("minecraft_version", "unknown"),
        "mod_loader": profile.get("mod_loader", "unknown"),
        "test_timestamp": datetime.datetime.now().isoformat(),
        "success": results.get("success", False),
        "server_started": results.get("server_started", False),
        "error_count": len(results.get("errors", [])),
        "warning_count": len(results.get("warnings", [])),
        "mod_count": results.get("mod_count", 0),
        "loaded_mod_count": results.get("loaded_mod_count", 0),
        "mods_with_issues": len(set(results.get("errors", [])) - set(results.get("loaded_mod_count", 0))),
    }
    
    # Add error and warning details
    if results.get("errors"):
        report["errors"] = results["errors"]
    
    if results.get("warnings"):
        report["warnings"] = results["warnings"]
    
    # Add missing dependencies if any
    if results.get("missing_dependencies"):
        report["missing_dependencies"] = results["missing_dependencies"]
    
    # Add slow mods
    if results.get("slow_mods"):
        report["slow_mods"] = results["slow_mods"]
    
    # Add detailed mod information if requested
    if full_report and profile.get("mods"):
        # Combine profile mod info with test results
        report["mods"] = []
        for mod_id, mod_info in profile.get("mods", {}).items():
            mod_report = {
                "id": mod_id,
                "name": mod_info.get("name", mod_id),
                "version": mod_info.get("version", "unknown"),
                "source": mod_info.get("source", "unknown"),
            }
            
            # Add loading time if available
            if mod_info.get("name") in results.get("mod_loading_times", {}):
                mod_report["loading_time_ms"] = results["mod_loading_times"][mod_info["name"]]
            
            report["mods"].append(mod_report)
        
        # Sort mods by loading time if available
        if any("loading_time_ms" in mod for mod in report["mods"]):
            report["mods"].sort(
                key=lambda mod: mod.get("loading_time_ms", 0),
                reverse=True
            )
    
    return report

def print_report(report):
    """
    Print the report in a user-friendly format.
    
    Args:
        report (dict): The generated report
    """
    print("\n" + "="*80)
    print(f"SERVER TEST REPORT: {report['profile_name']}")
    print("="*80)
    
    print(f"\nGame Version: {report['game_version']}")
    print(f"Mod Loader: {report['mod_loader']}")
    print(f"Test Date: {report['test_timestamp']}")
    print(f"Server Started: {'✅ Yes' if report['server_started'] else '❌ No'}")
    print(f"Total Mods: {report['mod_count']}")
    print(f"Loaded Mods: {report['loaded_mod_count']}")
    
    # Print errors if any
    if report.get("errors"):
        print("\n" + "-"*80)
        print(f"ERRORS ({len(report['errors'])})")
        print("-"*80)
        for i, error in enumerate(report['errors'], 1):
            print(f"{i}. {error}")
    
    # Print warnings if any
    if report.get("warnings"):
        print("\n" + "-"*80)
        print(f"WARNINGS ({len(report['warnings'])})")
        print("-"*80)
        for i, warning in enumerate(report['warnings'], 1):
            print(f"{i}. {warning}")
    
    # Print missing dependencies if any
    if report.get("missing_dependencies"):
        print("\n" + "-"*80)
        print(f"MISSING DEPENDENCIES ({len(report['missing_dependencies'])})")
        print("-"*80)
        for i, dep in enumerate(report['missing_dependencies'], 1):
            print(f"{i}. {dep}")
    
    # Print slow mods if any
    if report.get("slow_mods"):
        print("\n" + "-"*80)
        print("SLOW MODS")
        print("-"*80)
        for i, mod in enumerate(report['slow_mods'], 1):
            print(f"{i}. {mod['name']} - {mod['time']:.2f} ms")
    
    print("\n" + "="*80)
    if report['success']:
        print("✅ SERVER TEST PASSED - Server started successfully")
    else:
        print("❌ SERVER TEST FAILED - See errors above")
    print("="*80 + "\n")

def main():
    """Main function to run the server test."""
    args = parse_args()
    
    # Check if profile exists
    profile_manager = ProfileManager()
    if not profile_manager.profile_exists(args.profile):
        logger.error(f"Profile '{args.profile}' does not exist")
        sys.exit(1)
    
    # Deploy the server
    if not deploy_server(args.profile):
        logger.error("Server deployment failed")
        sys.exit(1)
    
    # Test the server
    results = test_server(args.profile, args.timeout)
    
    # Generate and print report
    report = generate_report(args.profile, results, args.full_report)
    print_report(report)
    
    # Save report to file if requested
    if args.output:
        try:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {args.output}")
        except Exception as e:
            logger.error(f"Failed to save report: {str(e)}")
    
    # Exit with appropriate status code
    sys.exit(0 if results["success"] else 1)

if __name__ == "__main__":
    main() 