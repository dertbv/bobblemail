#!/usr/bin/env python3
"""
Configuration Loader - Pure configuration loading functions

This module contains configuration loading functions extracted to break
circular dependencies between utils and configuration_manager modules.

Extracted functions:
- get_filters
"""

from config_auth import parse_config_file


def get_filters():
    """Get filters from config file"""
    filters = parse_config_file()
    if filters is False or not filters:
        # Return empty list if config file doesn't exist or is empty
        # The system now uses database-driven spam detection, so no fallback keywords needed
        return []
    return filters

# Export all functions
__all__ = ['get_filters']