#!/usr/bin/env python3
"""
File locking module for concurrent access protection
Provides thread-safe file operations to prevent data corruption
"""

import fcntl
import json
import os
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional
import threading
from logging_config import main_logger

class FileLockError(Exception):
    """Exception raised when file locking fails"""
    pass

class FileLocker:
    """Thread-safe file locking manager"""
    
    # Class-level lock to ensure thread safety for lock acquisition
    _global_lock = threading.Lock()
    _active_locks = {}  # Track active file locks by path
    
    def __init__(self, timeout: float = 10.0):
        """
        Initialize file locker
        
        Args:
            timeout: Maximum time to wait for lock acquisition (seconds)
        """
        self.timeout = timeout
    
    @contextmanager
    def lock_file(self, file_path: str, mode: str = 'r'):
        """
        Context manager for safe file locking
        
        Args:
            file_path: Path to file to lock
            mode: File open mode ('r', 'w', 'a', etc.)
            
        Yields:
            File object with exclusive lock
            
        Raises:
            FileLockError: If lock cannot be acquired
        """
        file_path = os.path.abspath(file_path)
        
        with self._global_lock:
            # Check if file is already locked by this process
            if file_path in self._active_locks:
                raise FileLockError(f"File already locked: {file_path}")
        
        file_obj = None
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Open file
            file_obj = open(file_path, mode)
            
            # Acquire exclusive lock with timeout
            start_time = time.time()
            while True:
                try:
                    fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except (IOError, OSError):
                    if time.time() - start_time > self.timeout:
                        raise FileLockError(f"Failed to acquire lock for {file_path} within {self.timeout}s")
                    time.sleep(0.1)  # Wait 100ms before retry
            
            # Track active lock
            with self._global_lock:
                self._active_locks[file_path] = threading.current_thread().ident
            
            yield file_obj
            
        finally:
            if file_obj:
                try:
                    # Release lock
                    fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)
                    file_obj.close()
                finally:
                    # Remove from active locks
                    with self._global_lock:
                        self._active_locks.pop(file_path, None)

    def safe_read_json(self, file_path: str, default: Any = None) -> Any:
        """
        Safely read JSON file with locking
        
        Args:
            file_path: Path to JSON file
            default: Default value if file doesn't exist or can't be read
            
        Returns:
            Parsed JSON data or default value
        """
        if not os.path.exists(file_path):
            return default
            
        try:
            with self.lock_file(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, FileLockError) as e:
            main_logger.error(f"Error reading JSON file {file_path}: {e}", exc_info=True)
            return default
    
    def safe_write_json(self, file_path: str, data: Any, indent: int = 2) -> bool:
        """
        Safely write JSON file with locking
        
        Args:
            file_path: Path to JSON file
            data: Data to write
            indent: JSON indentation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Write to temporary file first
            temp_path = f"{file_path}.tmp"
            
            with self.lock_file(temp_path, 'w') as f:
                json.dump(data, f, indent=indent)
                f.flush()  # Ensure data is written
                os.fsync(f.fileno())  # Force write to disk
            
            # Atomic rename to final location
            os.rename(temp_path, file_path)
            return True
            
        except (IOError, FileLockError) as e:
            print(f"Error writing JSON file {file_path}: {e}")
            # Clean up temp file if it exists
            if os.path.exists(f"{file_path}.tmp"):
                try:
                    os.remove(f"{file_path}.tmp")
                except OSError:
                    pass
            return False
    
    def safe_append_file(self, file_path: str, content: str) -> bool:
        """
        Safely append to file with locking
        
        Args:
            file_path: Path to file
            content: Content to append
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.lock_file(file_path, 'a') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            return True
        except (IOError, FileLockError) as e:
            print(f"Error appending to file {file_path}: {e}")
            return False

# Global file locker instance
file_locker = FileLocker()

# Convenience functions for common operations
def safe_read_json(file_path: str, default: Any = None) -> Any:
    """Convenience function for safe JSON reading"""
    return file_locker.safe_read_json(file_path, default)

def safe_write_json(file_path: str, data: Any, indent: int = 2) -> bool:
    """Convenience function for safe JSON writing"""
    return file_locker.safe_write_json(file_path, data, indent)

def safe_append_file(file_path: str, content: str) -> bool:
    """Convenience function for safe file appending"""
    return file_locker.safe_append_file(file_path, content)

@contextmanager
def lock_file(file_path: str, mode: str = 'r'):
    """Convenience context manager for file locking"""
    with file_locker.lock_file(file_path, mode) as f:
        yield f

# Analysis-specific helpers
def load_analysis_phase_safe(analysis_dir: str, phase: int, default: Any = None) -> Any:
    """
    Safely load analysis phase data with locking
    
    Args:
        analysis_dir: Analysis directory path
        phase: Phase number (1-5)
        default: Default value if file doesn't exist
        
    Returns:
        Phase data or default value
    """
    phase_files = {
        1: 'stock_universe.json',
        2: 'technical_analysis.json', 
        3: 'fundamental_analysis.json',
        4: 'sentiment_analysis.json',
        5: 'final_rankings.json'
    }
    
    if phase not in phase_files:
        raise ValueError(f"Invalid phase: {phase}. Must be 1-5")
    
    file_path = os.path.join(analysis_dir, f'phase{phase}', phase_files[phase])
    return safe_read_json(file_path, default)

def save_analysis_phase_safe(analysis_dir: str, phase: int, data: Any) -> bool:
    """
    Safely save analysis phase data with locking
    
    Args:
        analysis_dir: Analysis directory path
        phase: Phase number (1-5)
        data: Data to save
        
    Returns:
        True if successful, False otherwise
    """
    phase_files = {
        1: 'stock_universe.json',
        2: 'technical_analysis.json',
        3: 'fundamental_analysis.json', 
        4: 'sentiment_analysis.json',
        5: 'final_rankings.json'
    }
    
    if phase not in phase_files:
        raise ValueError(f"Invalid phase: {phase}. Must be 1-5")
    
    phase_dir = os.path.join(analysis_dir, f'phase{phase}')
    os.makedirs(phase_dir, exist_ok=True)
    
    file_path = os.path.join(phase_dir, phase_files[phase])
    return safe_write_json(file_path, data)

def is_analysis_complete(analysis_dir: str) -> bool:
    """
    Check if analysis is complete by verifying all phase files exist
    
    Args:
        analysis_dir: Analysis directory path
        
    Returns:
        True if all phases are complete
    """
    for phase in range(1, 6):
        if load_analysis_phase_safe(analysis_dir, phase) is None:
            return False
    return True