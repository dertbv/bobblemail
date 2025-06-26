"""
Atlas Email CLI Module - Command-line interface.

This module contains the command-line interface components:
- Main CLI application
- Menu handling and user interaction
- Command-line tools and utilities
- Batch processing automation
"""

from .main import main
from .menu_handler import display_main_menu, get_menu_choice

__all__ = [
    "main",
    "display_main_menu",
    "get_menu_choice",
]