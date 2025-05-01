#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Server Testing Script for Minecraft Modpack Manager

Tests server startup, detects issues with mods and datapacks,
and provides performance metrics.
"""

import os
import sys
import json
import time
import argparse
import logging
import subprocess
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib.core.profile_manager import ProfileManager
from lib.core.server_manager import ServerManager
from lib.core.log_analyzer import LogAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('server_testing')

# Default timeout values (in seconds)
DEFAULT_TOTAL_TIMEOUT = 900  # 15 minutes
DEFAULT_STARTUP_TIMEOUT = 300  # 5 minutes
DEFAULT_READY_TIMEOUT = 20  # 20 seconds after server_ready milestone

class ServerTester:
    """Class for testing Minecraft server functionality and performance."""
    
    def __init__(self, profile_name, docker_name=None, timeout=DEFAULT_TOTAL_TIMEOUT):
        """
        Initialize the ServerTester.
        
        Args:
            profile_name: Name of the modpack profile to test
            docker_name: Name of the Docker container (default: profile_name)
            timeout: Total timeout in seconds (default: 15 minutes)
        """
        self.profile_name = profile_name
        self.docker_name = docker_name or f"mc_{profile_name}"
        self.timeout = timeout
        
        # Load profile data
        self.profile_manager = ProfileManager()
        self.profile = self.profile_manager.load_profile(profile_name)
        if not self.profile:
            raise ValueError(f"Profile '{profile_name}' not found")
        
        # Initialize server manager and log analyzer
        self.server_manager = ServerManager(self.profile)
        self.log_analyzer = LogAnalyzer(self.profile)
        
        # Initialize test results
        self.results = {
            'profile_name': profile_name,
            'minecraft_version': self.profile.get('minecraft_version', 'unknown'),
            'loader': self.profile.get('loader', 'unknown'),
            'start_time': None,
            'end_time': None,
            'total_duration': None,
            'startup_milestones': {},
            'mod_loading_times': {},
            'slow_mods': [],
            'errors': [],
            'warnings': [],
            'datapacks': {
                'loaded': [],
                'failed': []
            },
            'success': False,
            'server_ready': False
        }
    
    def check_server_status(self):
        """
        Check if the server is currently running.
        
        Returns:
            Boolean indicating if the server is running
        """
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={self.docker_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True
            )
            return self.docker_name in result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Error checking server status: {e}")
            return False
    
    def start_server(self):
        """
        Start the Minecraft server.
        
        Returns:
            Boolean indicating success
        """
        if self.check_server_status():
            logger.warning(f"Server '{self.docker_name}' is already running")
            return True
        
        logger.info(f"Starting server for profile '{self.profile_name}'...")
        try:
            return self.server_manager.start_server(self.docker_name)
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """
        Stop the Minecraft server.
        
        Returns:
            Boolean indicating success
        """
        if not self.check_server_status():
            logger.warning(f"Server '{self.docker_name}' is not running")
            return True
        
        logger.info(f"Stopping server '{self.docker_name}'...")
        try:
            return self.server_manager.stop_server(self.docker_name)
        except Exception as e:
            logger.error(f"Failed to stop server: {e}")
            return False
    
    def get_logs(self):
        """
        Get logs from the Docker container.
        
        Returns:
            String containing logs
        """
        try:
            result = subprocess.run(
                ["docker", "logs", self.docker_name],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Error retrieving logs: {e}")
            return ""
    
    def test_startup(self, startup_timeout=DEFAULT_STARTUP_TIMEOUT):
        """
        Test server startup time and monitor for errors.
        
        Args:
            startup_timeout: Timeout in seconds for startup phase
            
        Returns:
            Boolean indicating success
        """
        # Record test start time
        self.results['start_time'] = datetime.now().isoformat()
        start_time = datetime.now()
        
        # Start the server
        if not self.start_server():
            self.results['errors'].append("Failed to start server")
            self.results['end_time'] = datetime.now().isoformat()
            return False
        
        # Monitor server startup
        logger.info("Monitoring server startup...")
        
        milestones_reached = set()
        errors_found = []
        warnings_found = []
        
        # Loop until server is ready or timeout
        end_time = start_time + timedelta(seconds=startup_timeout)
        while datetime.now() < end_time:
            # Get current logs
            logs = self.get_logs()
            
            # Check for new milestones
            new_milestones = self.log_analyzer.check_milestones(logs)
            for milestone, timestamp in new_milestones.items():
                if milestone not in milestones_reached:
                    logger.info(f"Milestone reached: {milestone}")
                    self.results['startup_milestones'][milestone] = timestamp.isoformat()
                    milestones_reached.add(milestone)
            
            # Check for new errors
            new_errors = self.log_analyzer.check_errors(logs)
            for error in new_errors:
                if error not in errors_found:
                    logger.error(f"Error detected: {error}")
                    self.results['errors'].append(error)
                    errors_found.append(error)
            
            # Check for new warnings
            new_warnings = self.log_analyzer.check_warnings(logs)
            for warning in new_warnings:
                if warning not in warnings_found:
                    logger.warning(f"Warning detected: {warning}")
                    self.results['warnings'].append(warning)
                    warnings_found.append(warning)
            
            # Check if server is ready
            if self.log_analyzer.is_server_ready(logs):
                self.results['server_ready'] = True
                logger.info("Server is ready to accept connections")
                
                # Wait a short period to collect final logs
                time.sleep(DEFAULT_READY_TIMEOUT)
                
                # Get final logs and analyze
                final_logs = self.get_logs()
                self._analyze_final_logs(final_logs)
                
                # Record test end time and duration
                self.results['end_time'] = datetime.now().isoformat()
                duration = (datetime.now() - start_time).total_seconds()
                self.results['total_duration'] = duration
                logger.info(f"Server startup completed in {duration:.2f} seconds")
                
                self.results['success'] = True
                return True
            
            # Sleep to avoid excessive CPU usage
            time.sleep(1)
        
        # If we reach here, startup timed out
        self.results['errors'].append(f"Server startup timed out after {startup_timeout} seconds")
        self.results['end_time'] = datetime.now().isoformat()
        logger.error(f"Server startup timed out after {startup_timeout} seconds")
        
        # Try to get final logs for analysis
        final_logs = self.get_logs()
        self._analyze_final_logs(final_logs)
        
        return False
    
    def _analyze_final_logs(self, logs):
        """
        Analyze the final logs to extract mod loading times and other metrics.
        
        Args:
            logs: String containing server logs
        """
        # Analyze mod loading times
        mod_times = self.log_analyzer.analyze_mod_loading_times(logs)
        self.results['mod_loading_times'] = mod_times
        
        # Identify slow mods
        slow_mods = self.log_analyzer.identify_slow_mods(mod_times)
        self.results['slow_mods'] = slow_mods
        
        # Analyze datapack loading
        datapack_info = self.log_analyzer.analyze_datapack_loading(logs)
        self.results['datapacks'] = datapack_info
        
        # Calculate total duration
        if self.results['start_time']:
            start_time = datetime.fromisoformat(self.results['start_time'])
            end_time = datetime.fromisoformat(self.results['end_time'])
            self.results['total_duration'] = (end_time - start_time).total_seconds()
    
    def run_test(self):
        """
        Run the server test and return results.
        
        Returns:
            Dictionary containing test results
        """
        try:
            # Run the startup test
            success = self.test_startup()
            
            # Always stop the server at the end
            self.stop_server()
            
            return self.results
        except Exception as e:
            logger.error(f"Error during test: {e}")
            self.results['errors'].append(f"Test failure: {str(e)}")
            self.results['success'] = False
            
            # Try to stop the server in case of error
            try:
                self.stop_server()
            except Exception as stop_error:
                logger.error(f"Failed to stop server after error: {stop_error}")
            
            return self.results
    
    def save_results(self, output_file=None):
        """
        Save test results to a JSON file.
        
        Args:
            output_file: Path to output file (default: None, generates a filename)
            
        Returns:
            Path to the saved file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            output_file = f"server_test_{self.profile_name}_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        # Save results
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Test results saved to: {output_file}")
        return output_file
    
    def print_summary(self):
        """Print a summary of the test results."""
        print("\n===== SERVER TEST SUMMARY =====")
        print(f"Profile: {self.results['profile_name']}")
        print(f"Minecraft Version: {self.results['minecraft_version']}")
        print(f"Loader: {self.results['loader']}")
        print(f"Status: {'SUCCESS' if self.results['success'] else 'FAILED'}")
        print(f"Server Ready: {'Yes' if self.results['server_ready'] else 'No'}")
        
        if self.results.get('total_duration'):
            print(f"Total Duration: {self.results['total_duration']:.2f} seconds")
        
        # Print milestones
        if self.results.get('startup_milestones'):
            print("\nStartup Milestones:")
            for milestone, timestamp in self.results['startup_milestones'].items():
                print(f"  - {milestone}: {timestamp}")
        
        # Print slow mods
        if self.results.get('slow_mods'):
            print("\nSlow Mods:")
            for mod in self.results['slow_mods']:
                print(f"  - {mod['name']}: {mod['time']:.2f} seconds")
        
        # Print errors and warnings
        if self.results.get('errors'):
            print("\nErrors:")
            for error in self.results['errors']:
                print(f"  - {error}")
        
        if self.results.get('warnings'):
            print("\nWarnings:")
            for warning in self.results['warnings']:
                print(f"  - {warning}")
        
        # Print datapacks
        if self.results.get('datapacks'):
            print("\nDatapacks:")
            print(f"  - Loaded: {len(self.results['datapacks']['loaded'])}")
            print(f"  - Failed: {len(self.results['datapacks']['failed'])}")
            if self.results['datapacks']['failed']:
                for dp in self.results['datapacks']['failed']:
                    print(f"    * {dp}")
        
        print("==============================\n")


def main():
    """Main entry point for the server testing script."""
    parser = argparse.ArgumentParser(description='Test Minecraft server startup and performance')
    parser.add_argument('profile_name', help='Name of the modpack profile to test')
    parser.add_argument('--docker-name', help='Name of the Docker container (default: mc_<profile_name>)')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TOTAL_TIMEOUT,
                        help=f'Total timeout in seconds (default: {DEFAULT_TOTAL_TIMEOUT})')
    parser.add_argument('--startup-timeout', type=int, default=DEFAULT_STARTUP_TIMEOUT,
                        help=f'Startup timeout in seconds (default: {DEFAULT_STARTUP_TIMEOUT})')
    parser.add_argument('--output', help='Path to save test results (JSON)')
    parser.add_argument('--silent', action='store_true', help='Suppress detailed output')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.silent:
        logger.setLevel(logging.WARNING)
    
    try:
        # Initialize tester
        tester = ServerTester(
            profile_name=args.profile_name,
            docker_name=args.docker_name,
            timeout=args.timeout
        )
        
        # Run test
        logger.info(f"Starting server test for profile '{args.profile_name}'")
        results = tester.run_test()
        
        # Save results if requested
        if args.output:
            tester.save_results(args.output)
        
        # Print summary
        if not args.silent:
            tester.print_summary()
        
        # Return appropriate exit code
        return 0 if results['success'] else 1
    
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 