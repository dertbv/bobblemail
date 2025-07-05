#!/usr/bin/env python3
"""
Memory-Efficient Stream Processing for Atlas_Email
Handles large email batches without loading everything into memory
"""

import os
import gc
import psutil
import threading
from typing import Iterator, Tuple, Dict, Any, Optional, Callable
from collections import deque
import time
from dataclasses import dataclass
import traceback

# Performance monitoring
try:
    from atlas_email.utils.performance_monitor import performance_monitor, monitor_operation
except ImportError:
    def performance_monitor(category):
        def decorator(func):
            return func
        return decorator
    
    def monitor_operation(*args, **kwargs):
        from contextlib import contextmanager
        @contextmanager
        def noop():
            yield
        return noop()

from atlas_email.models.db_logger import write_log


@dataclass
class MemoryStats:
    """Memory usage statistics"""
    process_memory_mb: float
    available_memory_mb: float
    memory_percent: float
    gc_collections: Dict[int, int]


class MemoryMonitor:
    """
    Monitors memory usage and triggers optimization when needed
    """
    
    def __init__(self, 
                 threshold_percent: float = 80.0,
                 check_interval: float = 5.0):
        """
        Initialize memory monitor
        
        Args:
            threshold_percent: Memory usage threshold to trigger GC
            check_interval: How often to check memory (seconds)
        """
        self.threshold_percent = threshold_percent
        self.check_interval = check_interval
        self.process = psutil.Process(os.getpid())
        self._monitoring = False
        self._monitor_thread = None
        self.stats_history = deque(maxlen=100)
        
    def start_monitoring(self):
        """Start background memory monitoring"""
        if self._monitoring:
            return
            
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="MemoryMonitor"
        )
        self._monitor_thread.start()
        write_log("Memory monitoring started", False)
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                stats = self.get_memory_stats()
                self.stats_history.append(stats)
                
                # Check if we need to trigger GC
                if stats.memory_percent > self.threshold_percent:
                    write_log(f"Memory usage {stats.memory_percent:.1f}% exceeds threshold, triggering GC", False)
                    self.optimize_memory()
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                write_log(f"Memory monitor error: {e}", True)
    
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics"""
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()
        available = psutil.virtual_memory().available
        
        gc_stats = {}
        for i in range(gc.get_count().__len__()):
            gc_stats[i] = gc.get_count()[i]
        
        return MemoryStats(
            process_memory_mb=memory_info.rss / 1024 / 1024,
            available_memory_mb=available / 1024 / 1024,
            memory_percent=memory_percent,
            gc_collections=gc_stats
        )
    
    @performance_monitor("memory")
    def optimize_memory(self):
        """Optimize memory usage"""
        with monitor_operation("memory", "garbage_collection"):
            # Force garbage collection
            before = self.get_memory_stats()
            
            # Collect all generations
            gc.collect(2)
            
            after = self.get_memory_stats()
            
            freed_mb = before.process_memory_mb - after.process_memory_mb
            write_log(f"Memory optimization freed {freed_mb:.1f}MB", False)
            
            return freed_mb


class StreamingEmailProcessor:
    """
    Processes emails in a streaming fashion to minimize memory usage
    """
    
    def __init__(self,
                 chunk_size: int = 100,
                 memory_limit_mb: int = 500):
        """
        Initialize streaming processor
        
        Args:
            chunk_size: Number of emails to process at once
            memory_limit_mb: Maximum memory usage before forcing optimization
        """
        self.chunk_size = chunk_size
        self.memory_limit_mb = memory_limit_mb
        self.memory_monitor = MemoryMonitor(
            threshold_percent=80.0
        )
        self.stats = {
            'chunks_processed': 0,
            'emails_processed': 0,
            'memory_optimizations': 0,
            'processing_errors': 0
        }
    
    @performance_monitor("streaming")
    def process_email_stream(self,
                           mail_connection,
                           folder_name: str,
                           process_func: Callable,
                           progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Process emails from IMAP connection in streaming fashion
        
        Args:
            mail_connection: IMAP connection
            folder_name: Folder to process
            process_func: Function to process each email
            progress_callback: Optional progress callback
            
        Returns:
            Processing statistics
        """
        write_log(f"Starting streaming processing of {folder_name}", False)
        
        # Start memory monitoring
        self.memory_monitor.start_monitoring()
        
        try:
            # Get email UIDs without loading all data
            mail_connection.select(folder_name)
            _, message_data = mail_connection.uid('search', None, 'ALL')
            
            if not message_data[0]:
                return self._get_final_stats()
            
            uids = message_data[0].split()
            total_emails = len(uids)
            
            write_log(f"Found {total_emails} emails to process", False)
            
            # Process in chunks
            for chunk_start in range(0, total_emails, self.chunk_size):
                chunk_end = min(chunk_start + self.chunk_size, total_emails)
                chunk_uids = uids[chunk_start:chunk_end]
                
                # Process chunk
                self._process_chunk(
                    mail_connection,
                    chunk_uids,
                    process_func,
                    chunk_start,
                    total_emails,
                    progress_callback
                )
                
                # Check memory after each chunk
                self._check_memory_usage()
                
            return self._get_final_stats()
            
        finally:
            self.memory_monitor.stop_monitoring()
    
    def _process_chunk(self,
                      mail_connection,
                      chunk_uids: list,
                      process_func: Callable,
                      chunk_start: int,
                      total_emails: int,
                      progress_callback: Optional[Callable]):
        """Process a single chunk of emails"""
        with monitor_operation("streaming", "process_chunk", {"size": len(chunk_uids)}):
            chunk_data = []
            
            # Fetch headers for chunk
            for uid in chunk_uids:
                try:
                    # Fetch only headers to minimize memory
                    _, msg_data = mail_connection.uid('fetch', uid, '(BODY.PEEK[HEADER])')
                    
                    if msg_data and msg_data[0]:
                        headers = msg_data[0][1]
                        if isinstance(headers, bytes):
                            headers = headers.decode('utf-8', errors='ignore')
                        chunk_data.append((uid.decode() if isinstance(uid, bytes) else uid, headers))
                    
                except Exception as e:
                    self.stats['processing_errors'] += 1
                    write_log(f"Error fetching UID {uid}: {e}", True)
            
            # Process chunk
            if chunk_data:
                try:
                    process_func(chunk_data)
                    self.stats['emails_processed'] += len(chunk_data)
                except Exception as e:
                    write_log(f"Error processing chunk: {e}\n{traceback.format_exc()}", True)
                    self.stats['processing_errors'] += len(chunk_data)
            
            self.stats['chunks_processed'] += 1
            
            # Update progress
            if progress_callback:
                progress = (chunk_start + len(chunk_uids)) / total_emails
                progress_callback(progress, chunk_start + len(chunk_uids), total_emails)
            
            # Clear chunk data to free memory
            chunk_data.clear()
    
    def _check_memory_usage(self):
        """Check and optimize memory if needed"""
        stats = self.memory_monitor.get_memory_stats()
        
        if stats.process_memory_mb > self.memory_limit_mb:
            write_log(f"Memory usage {stats.process_memory_mb:.1f}MB exceeds limit, optimizing", False)
            freed = self.memory_monitor.optimize_memory()
            self.stats['memory_optimizations'] += 1
    
    def _get_final_stats(self) -> Dict[str, Any]:
        """Get final processing statistics"""
        memory_stats = self.memory_monitor.get_memory_stats()
        
        return {
            'chunks_processed': self.stats['chunks_processed'],
            'emails_processed': self.stats['emails_processed'],
            'processing_errors': self.stats['processing_errors'],
            'memory_optimizations': self.stats['memory_optimizations'],
            'final_memory_mb': memory_stats.process_memory_mb,
            'peak_memory_mb': max(
                (s.process_memory_mb for s in self.memory_monitor.stats_history),
                default=memory_stats.process_memory_mb
            )
        }


class EmailStreamIterator:
    """
    Iterator for streaming email data without loading all into memory
    """
    
    def __init__(self,
                 mail_connection,
                 folder_name: str,
                 batch_size: int = 50):
        """
        Initialize email stream iterator
        
        Args:
            mail_connection: IMAP connection
            folder_name: Folder to iterate
            batch_size: Number of emails to fetch at once
        """
        self.mail = mail_connection
        self.folder_name = folder_name
        self.batch_size = batch_size
        self.current_batch = []
        self.current_index = 0
        self.uids = []
        self.uid_index = 0
        
        # Initialize
        self._initialize()
    
    def _initialize(self):
        """Initialize the iterator"""
        self.mail.select(self.folder_name)
        _, message_data = self.mail.uid('search', None, 'ALL')
        
        if message_data[0]:
            self.uids = message_data[0].split()
    
    def __iter__(self):
        """Return iterator"""
        return self
    
    def __next__(self) -> Tuple[str, str]:
        """Get next email (uid, headers)"""
        # Check if we need to fetch more
        if self.current_index >= len(self.current_batch):
            self._fetch_next_batch()
            
            # No more emails
            if not self.current_batch:
                raise StopIteration
        
        # Return next email
        email_data = self.current_batch[self.current_index]
        self.current_index += 1
        
        return email_data
    
    def _fetch_next_batch(self):
        """Fetch next batch of emails"""
        self.current_batch = []
        self.current_index = 0
        
        # Check if more UIDs available
        if self.uid_index >= len(self.uids):
            return
        
        # Get next batch of UIDs
        batch_end = min(self.uid_index + self.batch_size, len(self.uids))
        batch_uids = self.uids[self.uid_index:batch_end]
        self.uid_index = batch_end
        
        # Fetch headers for batch
        for uid in batch_uids:
            try:
                _, msg_data = self.mail.uid('fetch', uid, '(BODY.PEEK[HEADER])')
                
                if msg_data and msg_data[0]:
                    headers = msg_data[0][1]
                    if isinstance(headers, bytes):
                        headers = headers.decode('utf-8', errors='ignore')
                    
                    uid_str = uid.decode() if isinstance(uid, bytes) else uid
                    self.current_batch.append((uid_str, headers))
                    
            except Exception as e:
                write_log(f"Error fetching UID {uid}: {e}", True)


def create_email_stream(mail_connection, folder_name: str, batch_size: int = 50) -> Iterator[Tuple[str, str]]:
    """
    Create an email stream iterator
    
    Args:
        mail_connection: IMAP connection
        folder_name: Folder to stream
        batch_size: Batch size for fetching
        
    Returns:
        Iterator yielding (uid, headers) tuples
    """
    return EmailStreamIterator(mail_connection, folder_name, batch_size)


# Global memory monitor instance
_memory_monitor = None

def get_memory_monitor() -> MemoryMonitor:
    """Get global memory monitor instance"""
    global _memory_monitor
    if _memory_monitor is None:
        _memory_monitor = MemoryMonitor()
    return _memory_monitor


def optimize_memory_now():
    """Force immediate memory optimization"""
    monitor = get_memory_monitor()
    return monitor.optimize_memory()