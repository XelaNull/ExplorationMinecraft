#!/bin/bash
# Minecraft Modpack Manager
# Main entry point for managing modpacks

# Set script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

# Source the PYTHONPATH setup script
source "$SCRIPT_DIR/export_pythonpath.sh" > /dev/null

# Configuration
PYTHON_CMD="python"  # Will be dynamically determined
LIB_DIR="$SCRIPT_DIR/lib"
PROFILES_DIR="$PROJECT_ROOT/modpack_profiles"
CACHE_DIR="$PROJECT_ROOT/modpack_cache"
CLIENT_PACKS_DIR="$PROJECT_ROOT/client_packs"
BACKUPS_DIR="$PROJECT_ROOT/backups"
VENV_DIR="$PROJECT_ROOT/.venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

# Determine Python version and command
function determine_python_command() {
    # Try Python 3 first, then fall back to Python 2.7
    if command -v python3 &> /dev/null; then
        BASE_PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        # Check Python version
        PY_VERSION=$(python -c "import sys; print(sys.version_info[0])")
        if [ "$PY_VERSION" -eq "3" ]; then
            BASE_PYTHON_CMD="python"
        elif [ "$PY_VERSION" -eq "2" ]; then
            # Check if it's at least 2.7
            PY_MINOR=$(python -c "import sys; print(sys.version_info[1])")
            if [ "$PY_MINOR" -lt "7" ]; then
                echo "Error: Python 2.7 or higher is required"
                exit 1
            fi
            BASE_PYTHON_CMD="python"
        else
            echo "Error: Unsupported Python version"
            exit 1
        fi
    else
        echo "Error: Python not found"
        exit 1
    fi
    
    echo "Found Python command: $BASE_PYTHON_CMD"
}

# Set up Python virtual environment
function setup_venv() {
    echo "Setting up Python virtual environment..."
    
    # Check if venv already exists
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating new virtual environment..."
        $BASE_PYTHON_CMD -m venv "$VENV_DIR" 2>/dev/null || $BASE_PYTHON_CMD -m virtualenv "$VENV_DIR"
        
        if [ $? -ne 0 ]; then
            echo "Failed to create virtual environment. Trying to install virtualenv..."
            $BASE_PYTHON_CMD -m pip install virtualenv
            if [ $? -ne 0 ]; then
                echo "Could not install virtualenv. Running with system Python."
                PYTHON_CMD=$BASE_PYTHON_CMD
                return
            fi
            $BASE_PYTHON_CMD -m virtualenv "$VENV_DIR"
            if [ $? -ne 0 ]; then
                echo "Failed to create virtual environment. Running with system Python."
                PYTHON_CMD=$BASE_PYTHON_CMD
                return
            fi
        fi
        FRESH_ENV=true
    else
        FRESH_ENV=false
    fi
    
    # Activate the virtual environment
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
        PYTHON_CMD="$VENV_DIR/bin/python"
    elif [ -f "$VENV_DIR/Scripts/activate" ]; then
        # Windows support
        source "$VENV_DIR/Scripts/activate"
        PYTHON_CMD="$VENV_DIR/Scripts/python"
    else
        echo "Virtual environment exists but activation script not found. Using system Python."
        PYTHON_CMD=$BASE_PYTHON_CMD
        return
    fi
    
    # Create requirements file if it doesn't exist
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        echo "Creating requirements.txt file..."
        cat > "$REQUIREMENTS_FILE" << EOF
requests>=2.25.1
six>=1.16.0
urllib3>=1.26.5
virtualenv>=20.0.0
EOF
    fi
    
    # Upgrade pip first if this is a fresh environment or every 7 days
    PIP_UPGRADE_FILE="$VENV_DIR/.pip_last_upgrade"
    CURRENT_TIME=$(date +%s)
    UPGRADE_INTERVAL=$((7*24*60*60))  # 7 days in seconds
    
    if [ "$FRESH_ENV" = true ] || [ ! -f "$PIP_UPGRADE_FILE" ] || 
       [ $((CURRENT_TIME - $(cat "$PIP_UPGRADE_FILE" 2>/dev/null || echo 0))) -gt $UPGRADE_INTERVAL ]; then
        echo "Upgrading pip to latest version..."
        $PYTHON_CMD -m pip install --upgrade pip
        echo "$CURRENT_TIME" > "$PIP_UPGRADE_FILE"
    fi
    
    # Install required packages
    echo "Installing required packages..."
    $PYTHON_CMD -m pip install -r "$REQUIREMENTS_FILE"
    
    echo "Python environment ready: $PYTHON_CMD"
}

# Display help information
function show_help() {
    echo "Minecraft Modpack Manager"
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  Profile Management:"
    echo "    create [profile_name] --minecraft [version] --loader [fabric|forge] --loader-version [version]"
    echo "    delete [profile_name]"
    echo "    list                      List all modpack profiles"
    echo "    show [profile_name]       Show modpack profile details"
    echo ""
    echo "  Mod Management:"
    echo "    search [search_terms] --profile [profile_name] --source [modrinth|curseforge|both]"
    echo "    add [mod_id] --profile [profile_name]"
    echo "    remove [mod_id] --profile [profile_name]"
    echo "    list-mods --profile [profile_name]"
    echo ""
    echo "  Package Management:"
    echo "    download --profile [profile_name]        Download all mods for a profile"
    echo "    package --profile [profile_name]         Create a client pack"
    echo "    create-server-pack --profile [profile_name]  Create server pack in server_pack directory"
    echo "    check-updates --profile [profile_name]   Check for mod updates"
    echo "    update --profile [profile_name]          Update mods to latest compatible versions"
    echo "    resolve-dependencies --profile [profile_name]  Resolve all dependencies including datapacks"
    echo ""
    echo "  Server Management:"
    echo "    deploy --profile [profile_name]          Deploy server to Docker"
    echo "    test --profile [profile_name]            Test server compatibility"
    echo "    status --profile [profile_name]          Check server status"
    echo "    start --profile [profile_name]           Start server"
    echo "    stop --profile [profile_name]            Stop server"
    echo "    restart --profile [profile_name]         Restart server"
    echo "    logs --profile [profile_name]            View server logs"
    echo "    backup --profile [profile_name]          Backup server world"
    echo "    restore --profile [profile_name] --backup [backup_name]  Restore from backup"
    echo ""
    echo "  Data Pack Management:"
    echo "    add-datapack [datapack_id] --profile [profile_name]     Add a data pack to profile"
    echo "    remove-datapack [datapack_id] --profile [profile_name]  Remove a data pack from profile"
    echo "    list-datapacks --profile [profile_name]                 List data packs in profile"
    echo "    check-datapacks --profile [profile_name]                Check for compatible datapacks"
    echo ""
    echo "Options:"
    echo "  --profile [profile_name]    Specify the modpack profile"
    echo "  --minecraft [version]       Specify Minecraft version"
    echo "  --loader [fabric|forge]     Specify mod loader"
    echo "  --loader-version [version]  Specify mod loader version"
    echo "  --source [modrinth|curseforge|both]  Specify mod source"
    echo "  --help                      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 create exploration_pack --minecraft 1.20.1 --loader fabric --loader-version 0.14.21"
    echo "  $0 search \"Create mod\" --profile exploration_pack --source both"
    echo "  $0 add-datapack \"better_villages\" --profile exploration_pack"
    echo "  $0 deploy --profile exploration_pack"
}

# Check if Docker is available
function check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed or not in PATH"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        echo "Error: Docker is not running or you don't have sufficient permissions"
        return 1
    fi
    
    return 0
}

# Run a Python script directly with proper Python path
function run_python_module() {
    local module=$1
    local func=$2
    shift 2
    
    # Use Python's -c option to run code directly
    $PYTHON_CMD -c "
import sys, os
sys.path.insert(0, '$SCRIPT_DIR')
from $module import $func
$func($@)
" "$@"
    
    return $?
}

# Main function to parse arguments and execute commands
function main() {
    # Ensure Python is available
    determine_python_command
    
    # Set up virtual environment
    setup_venv
    
    # Create required directories if they don't exist
    mkdir -p "$PROFILES_DIR" "$CACHE_DIR" "$CLIENT_PACKS_DIR" "$BACKUPS_DIR"
    
    # Check if no arguments provided
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    # Parse command
    COMMAND=$1
    shift
    
    case $COMMAND in
        # Help
        --help|-h|help)
            show_help
            exit 0
            ;;
        
        # Profile Management
        create)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/create_profile.py" "$@"
            ;;
        
        delete)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/delete_profile.py" "$@"
            ;;
        
        list)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/list_profiles.py" "$@"
            ;;
        
        show)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/show_profile.py" "$@"
            ;;
        
        # Mod Management
        search)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/search_mods.py" "$@"
            ;;
        
        add)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/add_mod.py" "$@"
            ;;
        
        remove)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/remove_mod.py" "$@"
            ;;
        
        list-mods)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/list_mods.py" "$@"
            ;;
        
        # Data Pack Management
        add-datapack)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/add_datapack.py" "$@"
            ;;
        
        remove-datapack)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/remove_datapack.py" "$@"
            ;;
        
        list-datapacks)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/list_datapacks.py" "$@"
            ;;
        
        check-datapacks)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/check_datapacks.py" "$@"
            ;;
        
        # Package Management
        download)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/download_mods.py" "$@"
            ;;
        
        package)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/create_client_pack.py" "$@"
            ;;
        
        create-server-pack)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/create_server_pack.py" "$@"
            ;;
        
        check-updates)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/check_updates.py" "$@"
            ;;
        
        update)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/update_profile.py" "$@"
            ;;
        
        resolve-dependencies)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/resolve_dependencies.py" "$@"
            ;;
        
        # Server Management
        deploy|test|status|start|stop|restart|logs|backup|restore)
            PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH" $PYTHON_CMD "$SCRIPT_DIR/commands/server_management.py" "$COMMAND" "$@"
            ;;
        
        *)
            echo "Error: Unknown command $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# Execute main function
main "$@" 