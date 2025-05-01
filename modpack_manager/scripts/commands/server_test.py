#!/usr/bin/env python
"""
Server Test Script
Deploys a Minecraft server and analyzes logs to determine if it starts properly.
Reports on startup time, errors, and mod loading performance.
"""

import os
import sys
import time
import json
import logging
import argparse
import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('server_test')

# Parse arguments
def parse_args():
    parser = argparse.ArgumentParser(description='Test if a Minecraft server starts properly')
    parser.add_argument('--profile', required=True, help='Profile name to test')
    parser.add_argument('--timeout', type=int, default=300, help='Maximum time to wait for server startup (seconds)')
    parser.add_argument('--full-report', action='store_true', help='Generate a full report with mod loading times')
    parser.add_argument('--output', help='Output file path for the test report (JSON format)')
    
    return parser.parse_args()

# Generate report from log analysis
def generate_report(log_analysis, start_time, end_time, profile_name, full_report=False):
    """Generate a comprehensive report based on log analysis results"""
    startup_duration = end_time - start_time
    
    report = {
        "profile": profile_name,
        "test_time": datetime.datetime.now().isoformat(),
        "startup_duration_seconds": startup_duration.total_seconds(),
        "success": log_analysis.get("success", False),
        "server_started": log_analysis.get("server_started", False),
        "errors": log_analysis.get("errors", []),
        "warnings": log_analysis.get("warnings", []),
        "mod_count": log_analysis.get("mod_count", 0),
        "loaded_mod_count": log_analysis.get("loaded_mod_count", 0),
        "forge_version": log_analysis.get("forge_version", "unknown"),
        "minecraft_version": log_analysis.get("minecraft_version", "unknown"),
    }
    
    # Include slow mods if they exist
    slow_mods = log_analysis.get("slow_mods", [])
    if slow_mods:
        report["slow_mods"] = slow_mods[:10]  # List the top 10 slowest mods
    
    # Include detailed mod loading times if requested
    if full_report and "mod_loading_times" in log_analysis:
        report["mod_loading_times"] = log_analysis["mod_loading_times"]
    
    # Include missing dependencies if they exist
    missing_deps = log_analysis.get("missing_dependencies", [])
    if missing_deps:
        report["missing_dependencies"] = missing_deps
    
    # Include class loading issues if they exist
    class_loading_issues = log_analysis.get("class_loading_issues", [])
    if class_loading_issues:
        report["class_loading_issues"] = class_loading_issues
    
    return report

# Print report in a user-friendly format
def print_report(report):
    """Print the test report in a user-friendly format"""
    print("\n" + "="*80)
    print(f"SERVER TEST REPORT: {report['profile']}")
    print("="*80)
    
    # Status
    if report["success"]:
        print("\n✅ Server started successfully!")
    else:
        print("\n❌ Server failed to start properly!")
    
    # Basic information
    print(f"\nTest time: {report['test_time']}")
    print(f"Startup duration: {report['startup_duration_seconds']:.2f} seconds")
    print(f"Minecraft version: {report['minecraft_version']}")
    print(f"Forge version: {report['forge_version']}")
    print(f"Mods: {report['loaded_mod_count']}/{report['mod_count']} loaded successfully")
    
    # Errors
    if report["errors"]:
        print("\n❌ ERRORS:")
        for error in report["errors"]:
            print(f"  - {error}")
    
    # Warnings
    if report.get("warnings"):
        print("\n⚠️ WARNINGS:")
        for warning in report["warnings"]:
            print(f"  - {warning}")
    
    # Missing dependencies
    if report.get("missing_dependencies"):
        print("\n❓ MISSING DEPENDENCIES:")
        for dep in report["missing_dependencies"]:
            print(f"  - {dep}")
    
    # Slow mods
    if report.get("slow_mods"):
        print("\n🐢 SLOWEST MODS:")
        for mod in report["slow_mods"]:
            print(f"  - {mod['name']}: {mod['time']:.2f} ms")
    
    print("\n" + "="*80)

def main():
    args = parse_args()
    profile_name = args.profile
    timeout = args.timeout
    full_report = args.full_report
    output_file = args.output
    
    logger.info(f"Testing server for profile: {profile_name}")
    
    # Import necessary modules
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lib_dir = os.path.join(script_dir, "..", "lib")
    sys.path.insert(0, os.path.abspath(lib_dir))
    
    from core.profile_manager import ProfileManager
    from core.server_manager import ServerManager
    from core.log_analyzer import LogAnalyzer
    
    # Check if profile exists
    profile_manager = ProfileManager()
    if not profile_manager.profile_exists(profile_name):
        logger.error(f"Profile '{profile_name}' does not exist.")
        return 1
    
    server_manager = ServerManager()
    log_analyzer = LogAnalyzer()
    
    # Check if server is already running
    if server_manager.is_running(profile_name):
        logger.warning(f"Server for profile '{profile_name}' is already running. Stopping it first.")
        server_manager.stop_server(profile_name)
        time.sleep(5)  # Wait for server to stop
    
    try:
        # Deploy server
        logger.info(f"Deploying server for profile '{profile_name}'...")
        start_time = datetime.datetime.now()
        server_deployed = server_manager.deploy_server(profile_name)
        
        if not server_deployed:
            logger.error("Failed to deploy server")
            return 1
        
        # Monitor logs
        logger.info(f"Server deployed, monitoring logs (timeout: {timeout} seconds)...")
        log_analysis = log_analyzer.analyze_server_logs(profile_name, timeout=timeout)
        
        # Get end time
        end_time = datetime.datetime.now()
        
        # Generate report
        report = generate_report(log_analysis, start_time, end_time, profile_name, full_report)
        
        # Print report
        print_report(report)
        
        # Save report to file if specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to: {output_file}")
        
        # Stop server
        logger.info("Stopping server...")
        server_manager.stop_server(profile_name)
        
        return 0 if report["success"] else 1
    
    except Exception as e:
        logger.exception(f"Error during server testing: {str(e)}")
        # Ensure server is stopped in case of error
        try:
            server_manager.stop_server(profile_name)
        except:
            pass
        return 1

if __name__ == "__main__":
    sys.exit(main()) 