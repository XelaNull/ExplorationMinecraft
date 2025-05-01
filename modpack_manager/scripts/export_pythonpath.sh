#!/bin/bash
# Script to set up the PYTHONPATH for modpack manager scripts

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/lib:$PYTHONPATH"

echo "PYTHONPATH set to include script directories"