#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Logging module for Minecraft Modpack Manager.
Configures and provides logging functions.
Compatible with Python 2.7 and 3+.
"""

from __future__ import print_function, division, unicode_literals
import os
import sys
import logging
import time
import datetime

# Add parent directory to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import config

# Python 2/3 compatibility
PY2 = sys.version_info[0] == 2

# Configure logging
logs_dir = config.LOGS_DIR
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Create log file with timestamp
timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_file = os.path.join(logs_dir, f'modpack_manager_{timestamp}.log')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('modpack_manager')

def info(message):
    """Log info message."""
    logger.info(message)
    
def debug(message):
    """Log debug message."""
    logger.debug(message)
    
def warning(message):
    """Log warning message."""
    logger.warning(message)
    
def error(message):
    """Log error message."""
    logger.error(message)
    
def critical(message):
    """Log critical message."""
    logger.critical(message)

def set_debug_mode(enabled=True):
    """
    Enable or disable debug mode.
    
    Args:
        enabled (bool): Whether to enable debug mode
    """
    if enabled:
        logger.setLevel(logging.DEBUG)
        info("Debug mode enabled")
    else:
        logger.setLevel(logging.INFO)
        info("Debug mode disabled")

def get_log_file():
    """
    Get the current log file path.
    
    Returns:
        str: Path to the log file
    """
    return log_file

if __name__ == '__main__':
    """Test logging functionality."""
    debug("This is a debug message")
    info("This is an info message")
    warning("This is a warning message")
    error("This is an error message")
    critical("This is a critical message")
    
    print("\nLog file: {}".format(get_log_file()))
    
    print("\nTesting debug mode:")
    set_debug_mode(True)
    debug("This debug message should now appear in console")
    set_debug_mode(False)
    debug("This debug message should not appear in console") 