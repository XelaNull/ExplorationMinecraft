#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manages Minecraft server deployment and maintenance using Docker.
Handles deployment, starting, stopping, and monitoring of Docker containers.
"""

import sys
import os
import argparse
import json
import subprocess
import shutil
from datetime import datetime

# Add parent directory to path for module imports
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(lib_path)

from core.profile_manager import ProfileManager
from utils import config

# Constants
DOCKER_COMPOSE_TEMPLATE = """services:
  minecraft:
    container_name: mc_{profile_name}
    image: minecraft-{profile_name}:latest
    ports:
      - "{server_port}:25565"
    environment:
      - MEMORY={memory}
      - EULA=TRUE
    volumes:
      - ./data/{profile_name}:/data
    restart: unless-stopped
"""

def ensure_server_pack_exists(profile_name):
    """Ensure the server pack exists for the profile."""
    server_pack_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'server_pack')
    
    if not os.path.exists(server_pack_dir) or not os.listdir(server_pack_dir):
        print(f"Server pack for '{profile_name}' does not exist. Creating it now...")
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        create_server_script = os.path.join(script_dir, 'commands', 'create_server_pack.py')
        
        python_cmd = sys.executable
        result = subprocess.run([python_cmd, create_server_script, '--profile', profile_name], check=False)
        
        if result.returncode != 0:
            print(f"Failed to create server pack for '{profile_name}'.")
            sys.exit(1)

def build_docker_image(profile_name):
    """Build Docker image for the server pack."""
    server_pack_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'server_pack')
    
    print(f"Building Docker image for '{profile_name}'...")
    print("=" * 60)
    
    # Load profile to get Minecraft and loader versions
    profile_manager = ProfileManager()
    profile = profile_manager.load_profile(profile_name)
    
    if not profile:
        print(f"Error: Profile '{profile_name}' not found.")
        sys.exit(1)
    
    minecraft_version = profile.get('minecraft_version')
    loader = profile.get('loader')
    loader_version = profile.get('loader_version')
    
    print(f"Profile details: Minecraft {minecraft_version} with {loader} {loader_version}")
    
    # Run the docker_image_manager.sh script with verbose output
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docker_manager_script = os.path.join(script_dir, 'docker_image_manager.sh')
    
    print("Using docker_image_manager.sh to build the image (this may take several minutes)...")
    
    try:
        # Use the --verbose flag for more detailed output
        result = subprocess.run(['bash', docker_manager_script, 'build', profile_name, '--verbose'], 
                                check=False, 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.STDOUT,
                                text=True,
                                bufsize=1,
                                universal_newlines=True)
        
        # Print output line by line during execution
        for line in result.stdout.splitlines():
            print(line)
        
        if result.returncode != 0:
            print(f"Failed to build Docker image for '{profile_name}'.")
            print("=" * 60)
            sys.exit(1)
        
    except subprocess.SubprocessError as e:
        print(f"Error executing docker_image_manager.sh: {e}")
        print("=" * 60)
        sys.exit(1)
    
    print(f"Docker image 'minecraft-{profile_name}:latest' built successfully.")
    print("=" * 60)

def create_docker_compose(profile_name, server_port=25565, memory="4G"):
    """Create docker-compose.yml file for the server."""
    servers_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'servers')
    os.makedirs(servers_dir, exist_ok=True)
    
    profile_dir = os.path.join(servers_dir, profile_name)
    os.makedirs(profile_dir, exist_ok=True)
    
    # Create data directory
    data_dir = os.path.join(profile_dir, 'data', profile_name)
    os.makedirs(data_dir, exist_ok=True)
    
    # Create docker-compose.yml
    compose_path = os.path.join(profile_dir, 'docker-compose.yml')
    with open(compose_path, 'w') as f:
        f.write(DOCKER_COMPOSE_TEMPLATE.format(
            profile_name=profile_name,
            server_port=server_port,
            memory=memory
        ))
    
    print(f"Docker Compose configuration created at {compose_path}")
    return profile_dir

def deploy_server(profile_name, server_port=25565, memory="4G"):
    """Deploy a server for the given profile."""
    # Ensure server pack exists
    ensure_server_pack_exists(profile_name)
    
    # Build Docker image
    build_docker_image(profile_name)
    
    # Create docker-compose.yml
    profile_dir = create_docker_compose(profile_name, server_port, memory)
    
    # Start the server
    print(f"Starting Minecraft server for '{profile_name}'...")
    print("=" * 60)
    os.chdir(profile_dir)
    
    try:
        result = subprocess.run(['docker-compose', 'up', '-d'], 
                                check=False,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True)
        
        # Print output
        if result.stdout:
            print(result.stdout)
        
        if result.returncode != 0:
            print(f"Failed to start server for '{profile_name}'.")
            print("=" * 60)
            sys.exit(1)
        
    except subprocess.SubprocessError as e:
        print(f"Error starting Docker container: {e}")
        print("=" * 60)
        sys.exit(1)
    
    print(f"Server for '{profile_name}' deployed successfully!")
    print(f"Server is running on port {server_port}")
    print("Use the following commands to manage the server:")
    print(f"  ./modpack_manager.sh status --profile {profile_name}")
    print(f"  ./modpack_manager.sh logs --profile {profile_name}")
    print(f"  ./modpack_manager.sh stop --profile {profile_name}")
    print("=" * 60)

def get_server_dir(profile_name):
    """Get the server directory for a profile."""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'servers', profile_name)

def start_server(profile_name):
    """Start the server for a profile."""
    server_dir = get_server_dir(profile_name)
    
    if not os.path.exists(server_dir):
        print(f"Server for '{profile_name}' not found. Deploy it first with 'deploy' command.")
        sys.exit(1)
    
    os.chdir(server_dir)
    result = subprocess.run(['docker-compose', 'start'], check=False)
    
    if result.returncode != 0:
        print(f"Failed to start server for '{profile_name}'.")
        sys.exit(1)
    
    print(f"Server for '{profile_name}' started successfully.")

def stop_server(profile_name):
    """Stop the server for a profile."""
    server_dir = get_server_dir(profile_name)
    
    if not os.path.exists(server_dir):
        print(f"Server for '{profile_name}' not found.")
        sys.exit(1)
    
    os.chdir(server_dir)
    result = subprocess.run(['docker-compose', 'stop'], check=False)
    
    if result.returncode != 0:
        print(f"Failed to stop server for '{profile_name}'.")
        sys.exit(1)
    
    print(f"Server for '{profile_name}' stopped successfully.")

def restart_server(profile_name):
    """Restart the server for a profile."""
    server_dir = get_server_dir(profile_name)
    
    if not os.path.exists(server_dir):
        print(f"Server for '{profile_name}' not found.")
        sys.exit(1)
    
    os.chdir(server_dir)
    result = subprocess.run(['docker-compose', 'restart'], check=False)
    
    if result.returncode != 0:
        print(f"Failed to restart server for '{profile_name}'.")
        sys.exit(1)
    
    print(f"Server for '{profile_name}' restarted successfully.")

def check_status(profile_name):
    """Check the status of the server for a profile."""
    server_dir = get_server_dir(profile_name)
    
    if not os.path.exists(server_dir):
        print(f"Server for '{profile_name}' not found.")
        sys.exit(1)
    
    os.chdir(server_dir)
    subprocess.run(['docker-compose', 'ps'], check=False)

def view_logs(profile_name):
    """View the logs of the server for a profile."""
    server_dir = get_server_dir(profile_name)
    
    if not os.path.exists(server_dir):
        print(f"Server for '{profile_name}' not found.")
        sys.exit(1)
    
    os.chdir(server_dir)
    subprocess.run(['docker-compose', 'logs'], check=False)

def create_backup(profile_name):
    """Create a backup of the server data."""
    server_dir = get_server_dir(profile_name)
    data_dir = os.path.join(server_dir, 'data', profile_name)
    
    if not os.path.exists(data_dir):
        print(f"Server data for '{profile_name}' not found.")
        sys.exit(1)
    
    # Create backups directory
    backups_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backups', profile_name)
    os.makedirs(backups_dir, exist_ok=True)
    
    # Create timestamped backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{profile_name}_{timestamp}"
    backup_dir = os.path.join(backups_dir, backup_name)
    
    print(f"Creating backup of '{profile_name}' server data...")
    
    # Stop the server if it's running
    os.chdir(server_dir)
    subprocess.run(['docker-compose', 'stop'], check=False)
    
    # Create backup
    shutil.copytree(data_dir, backup_dir)
    
    # Restart the server
    subprocess.run(['docker-compose', 'start'], check=False)
    
    print(f"Backup created successfully: {backup_dir}")
    return backup_name

def restore_backup(profile_name, backup_name):
    """Restore a backup of the server data."""
    server_dir = get_server_dir(profile_name)
    data_dir = os.path.join(server_dir, 'data', profile_name)
    backups_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backups', profile_name)
    backup_dir = os.path.join(backups_dir, backup_name)
    
    if not os.path.exists(backup_dir):
        print(f"Backup '{backup_name}' not found.")
        sys.exit(1)
    
    print(f"Restoring backup '{backup_name}' for '{profile_name}'...")
    
    # Stop the server if it's running
    os.chdir(server_dir)
    subprocess.run(['docker-compose', 'stop'], check=False)
    
    # Rename current data directory as backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_backup = f"{profile_name}_current_{timestamp}"
    current_backup_dir = os.path.join(backups_dir, current_backup)
    
    if os.path.exists(data_dir):
        shutil.move(data_dir, current_backup_dir)
        print(f"Current server data backed up to: {current_backup_dir}")
    
    # Restore from backup
    os.makedirs(os.path.dirname(data_dir), exist_ok=True)
    shutil.copytree(backup_dir, data_dir)
    
    # Restart the server
    subprocess.run(['docker-compose', 'start'], check=False)
    
    print(f"Backup '{backup_name}' restored successfully.")

def main():
    """Handle server management commands."""
    parser = argparse.ArgumentParser(description='Manage Minecraft server deployment with Docker.')
    parser.add_argument('command', help='Command to execute (deploy, start, stop, restart, status, logs, backup, restore)')
    parser.add_argument('--profile', required=True, help='Profile name')
    parser.add_argument('--port', type=int, default=25565, help='Server port (default: 25565)')
    parser.add_argument('--memory', default='4G', help='Memory allocation (default: 4G)')
    parser.add_argument('--backup', help='Backup name for restore command')
    
    args = parser.parse_args()
    
    if args.command == 'deploy':
        deploy_server(args.profile, args.port, args.memory)
    elif args.command == 'start':
        start_server(args.profile)
    elif args.command == 'stop':
        stop_server(args.profile)
    elif args.command == 'restart':
        restart_server(args.profile)
    elif args.command == 'status':
        check_status(args.profile)
    elif args.command == 'logs':
        view_logs(args.profile)
    elif args.command == 'backup':
        create_backup(args.profile)
    elif args.command == 'restore':
        if not args.backup:
            print("Error: --backup argument is required for restore command.")
            sys.exit(1)
        restore_backup(args.profile, args.backup)
    elif args.command == 'test':
        print(f"Testing server for '{args.profile}'...")
        print("This functionality is not yet implemented.")
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)

if __name__ == '__main__':
    main() 