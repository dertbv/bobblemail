#!/usr/bin/env python3
"""
Thread Pool Manager
Manages worker threads for parallel email processing with proper lifecycle management
"""

import threading
import queue
import time
import signal
import atexit
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager
import multiprocessing

from atlas_email.models.db_logger import write_log


class ThreadPoolManager:
    """
    Manages a pool of worker threads with graceful shutdown and error isolation
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure single thread pool"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize thread pool manager"""
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.pools = {}
            self.default_worker_count = min(16, (multiprocessing.cpu_count() or 4) * 2)
            self._shutdown = False
            
            # Register cleanup handlers
            atexit.register(self.shutdown_all)
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            write_log(f"ThreadPoolManager initialized with default {self.default_worker_count} workers", False)
    
    def create_pool(self, 
                   pool_name: str,
                   worker_count: Optional[int] = None,
                   queue_size: int = 1000,
                   worker_function: Optional[Callable] = None) -> 'WorkerPool':
        """
        Create a new worker pool
        
        Args:
            pool_name: Unique name for the pool
            worker_count: Number of worker threads
            queue_size: Maximum task queue size
            worker_function: Function to run in each worker
            
        Returns:
            WorkerPool instance
        """
        if pool_name in self.pools:
            write_log(f"Pool '{pool_name}' already exists, returning existing pool", False)
            return self.pools[pool_name]
        
        worker_count = worker_count or self.default_worker_count
        pool = WorkerPool(pool_name, worker_count, queue_size, worker_function)
        self.pools[pool_name] = pool
        
        write_log(f"Created worker pool '{pool_name}' with {worker_count} workers", False)
        return pool
    
    def get_pool(self, pool_name: str) -> Optional['WorkerPool']:
        """Get existing pool by name"""
        return self.pools.get(pool_name)
    
    def shutdown_pool(self, pool_name: str):
        """Shutdown specific pool"""
        if pool_name in self.pools:
            self.pools[pool_name].shutdown()
            del self.pools[pool_name]
            write_log(f"Shutdown pool '{pool_name}'", False)
    
    def shutdown_all(self):
        """Shutdown all pools"""
        if self._shutdown:
            return
            
        self._shutdown = True
        write_log("Shutting down all thread pools...", False)
        
        for pool_name, pool in list(self.pools.items()):
            pool.shutdown()
        
        self.pools.clear()
        write_log("All thread pools shutdown complete", False)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        write_log(f"Received signal {signum}, initiating graceful shutdown", False)
        self.shutdown_all()
    
    def get_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all pools"""
        return {
            pool_name: pool.get_statistics()
            for pool_name, pool in self.pools.items()
        }


class WorkerPool:
    """
    A pool of worker threads processing tasks from a queue
    """
    
    def __init__(self, 
                 name: str,
                 worker_count: int,
                 queue_size: int,
                 worker_function: Optional[Callable] = None):
        self.name = name
        self.worker_count = worker_count
        self.task_queue = queue.Queue(maxsize=queue_size)
        self.workers = []
        self._shutdown = False
        self._lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_processing_time': 0.0,
            'worker_errors': {}
        }
        
        # Start workers
        self._start_workers(worker_function)
    
    def _start_workers(self, worker_function: Optional[Callable] = None):
        """Start worker threads"""
        for i in range(self.worker_count):
            worker = WorkerThread(
                name=f"{self.name}-worker-{i}",
                task_queue=self.task_queue,
                stats=self.stats,
                stats_lock=self._lock,
                worker_function=worker_function
            )
            worker.start()
            self.workers.append(worker)
    
    def submit_task(self, task: Any, timeout: Optional[float] = None) -> bool:
        """
        Submit task to the pool
        
        Args:
            task: Task to process
            timeout: Queue timeout in seconds
            
        Returns:
            True if task was queued, False if queue is full
        """
        if self._shutdown:
            return False
        
        try:
            self.task_queue.put(task, timeout=timeout)
            with self._lock:
                self.stats['tasks_submitted'] += 1
            return True
        except queue.Full:
            write_log(f"Task queue full for pool '{self.name}'", True)
            return False
    
    def wait_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all tasks to complete
        
        Args:
            timeout: Maximum time to wait
            
        Returns:
            True if all tasks completed, False if timeout
        """
        start_time = time.time()
        
        while True:
            with self._lock:
                pending = self.stats['tasks_submitted'] - \
                         (self.stats['tasks_completed'] + self.stats['tasks_failed'])
            
            if pending <= 0:
                return True
            
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            time.sleep(0.1)
    
    def shutdown(self, wait: bool = True, timeout: float = 30):
        """
        Shutdown the pool
        
        Args:
            wait: Wait for pending tasks to complete
            timeout: Maximum time to wait for completion
        """
        if self._shutdown:
            return
        
        self._shutdown = True
        
        if wait:
            write_log(f"Waiting for pool '{self.name}' to complete pending tasks...", False)
            self.wait_completion(timeout)
        
        # Send stop signal to all workers
        for _ in self.workers:
            self.task_queue.put(None)
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
            if worker.is_alive():
                write_log(f"Worker {worker.name} did not stop gracefully", True)
        
        self.workers.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self._lock:
            pending = self.stats['tasks_submitted'] - \
                     (self.stats['tasks_completed'] + self.stats['tasks_failed'])
            
            avg_time = self.stats['total_processing_time'] / self.stats['tasks_completed'] \
                      if self.stats['tasks_completed'] > 0 else 0
            
            return {
                'name': self.name,
                'worker_count': self.worker_count,
                'tasks_submitted': self.stats['tasks_submitted'],
                'tasks_completed': self.stats['tasks_completed'],
                'tasks_failed': self.stats['tasks_failed'],
                'tasks_pending': pending,
                'queue_size': self.task_queue.qsize(),
                'avg_processing_time': avg_time,
                'worker_errors': dict(self.stats['worker_errors'])
            }


class WorkerThread(threading.Thread):
    """
    Worker thread that processes tasks from a queue
    """
    
    def __init__(self, 
                 name: str,
                 task_queue: queue.Queue,
                 stats: Dict[str, Any],
                 stats_lock: threading.Lock,
                 worker_function: Optional[Callable] = None):
        super().__init__(name=name, daemon=True)
        self.task_queue = task_queue
        self.stats = stats
        self.stats_lock = stats_lock
        self.worker_function = worker_function or self._default_worker
        self._stop = False
    
    def run(self):
        """Main worker loop"""
        write_log(f"Worker {self.name} started", False)
        
        while not self._stop:
            try:
                # Get task from queue
                task = self.task_queue.get(timeout=1)
                
                if task is None:  # Stop signal
                    self._stop = True
                    break
                
                # Process task
                start_time = time.time()
                try:
                    self.worker_function(task)
                    
                    # Update statistics
                    with self.stats_lock:
                        self.stats['tasks_completed'] += 1
                        self.stats['total_processing_time'] += time.time() - start_time
                        
                except Exception as e:
                    # Log error
                    error_msg = f"Task processing error: {str(e)}"
                    write_log(f"{self.name}: {error_msg}", True)
                    
                    # Update statistics
                    with self.stats_lock:
                        self.stats['tasks_failed'] += 1
                        if self.name not in self.stats['worker_errors']:
                            self.stats['worker_errors'][self.name] = 0
                        self.stats['worker_errors'][self.name] += 1
                
                finally:
                    self.task_queue.task_done()
                    
            except queue.Empty:
                continue
            except Exception as e:
                write_log(f"{self.name}: Unexpected error in worker loop: {e}", True)
        
        write_log(f"Worker {self.name} stopped", False)
    
    def _default_worker(self, task):
        """Default worker function (can be overridden)"""
        # Simulate work
        time.sleep(0.01)
        print(f"Processed task: {task}")


# Global thread pool manager instance
_thread_pool_manager = None

def get_thread_pool_manager() -> ThreadPoolManager:
    """Get the global thread pool manager instance"""
    global _thread_pool_manager
    if _thread_pool_manager is None:
        _thread_pool_manager = ThreadPoolManager()
    return _thread_pool_manager


@contextmanager
def worker_pool(name: str, worker_count: Optional[int] = None):
    """
    Context manager for temporary worker pool
    
    Usage:
        with worker_pool('my-pool', worker_count=8) as pool:
            for task in tasks:
                pool.submit_task(task)
            pool.wait_completion()
    """
    manager = get_thread_pool_manager()
    pool = manager.create_pool(name, worker_count)
    
    try:
        yield pool
    finally:
        manager.shutdown_pool(name)