#!/usr/bin/env python3
"""
Parallel Email Processing Pipeline
Implements multi-threaded email processing with producer-consumer pattern
"""

import threading
import queue
import time
import os
from typing import List, Dict, Any, Callable, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import traceback
from datetime import datetime

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
from atlas_email.models.bulk_operations import get_bulk_manager


@dataclass
class ProcessingTask:
    """Represents a single email processing task"""
    uid: str
    headers: str
    folder_name: str
    task_id: int
    metadata: Dict[str, Any] = None


@dataclass
class ProcessingResult:
    """Result of processing a single email"""
    uid: str
    success: bool
    action: str  # DELETED, PRESERVED, ERROR
    category: str
    confidence: float
    reason: str
    error: Optional[str] = None
    processing_time: float = 0.0
    metadata: Dict[str, Any] = None


class ParallelEmailProcessor:
    """
    High-performance parallel email processor using thread pool
    """
    
    def __init__(self, 
                 worker_count: int = None,
                 queue_size: int = 1000,
                 batch_size: int = 100):
        """
        Initialize parallel processor
        
        Args:
            worker_count: Number of worker threads (default: CPU count)
            queue_size: Maximum queue size
            batch_size: Batch size for processing
        """
        self.worker_count = worker_count or min(16, (os.cpu_count() or 4) * 2)
        self.queue_size = queue_size
        self.batch_size = batch_size
        
        # Processing components
        self.task_queue = queue.Queue(maxsize=queue_size)
        self.result_queue = queue.Queue()
        self.executor = None
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'processing_times': [],
            'queue_wait_times': []
        }
        
        # Control flags
        self._shutdown = False
        self._processing_lock = threading.Lock()
        
        # Bulk operations manager
        self.bulk_manager = get_bulk_manager()
        
        write_log(f"Parallel processor initialized with {self.worker_count} workers", False)
    
    @performance_monitor("parallel_processing")
    def process_emails_parallel(self, 
                              email_processor,
                              email_tasks: List[Tuple[str, str]],  # [(uid, headers), ...]
                              folder_name: str,
                              process_callback: Optional[Callable] = None) -> List[ProcessingResult]:
        """
        Process emails in parallel using thread pool
        
        Args:
            email_processor: EmailProcessor instance with classification logic
            email_tasks: List of (uid, headers) tuples
            folder_name: Folder being processed
            process_callback: Optional callback for progress updates
            
        Returns:
            List of ProcessingResult objects
        """
        total_emails = len(email_tasks)
        write_log(f"Starting parallel processing of {total_emails} emails with {self.worker_count} workers", False)
        
        results = []
        start_time = time.time()
        
        with monitor_operation("parallel_processing", "batch_process", {"count": total_emails}):
            # Create thread pool
            with ThreadPoolExecutor(max_workers=self.worker_count) as executor:
                # Submit all tasks
                future_to_task = {}
                
                for i, (uid, headers) in enumerate(email_tasks):
                    task = ProcessingTask(
                        uid=uid,
                        headers=headers,
                        folder_name=folder_name,
                        task_id=i,
                        metadata={'batch_position': i}
                    )
                    
                    future = executor.submit(self._process_single_email, email_processor, task)
                    future_to_task[future] = task
                
                # Process results as they complete
                completed = 0
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # Update statistics
                        with self._processing_lock:
                            self.stats['total_processed'] += 1
                            if result.success:
                                self.stats['successful'] += 1
                            else:
                                self.stats['failed'] += 1
                            self.stats['processing_times'].append(result.processing_time)
                        
                        completed += 1
                        
                        # Progress callback
                        if process_callback and completed % 10 == 0:
                            progress = completed / total_emails
                            process_callback(progress, completed, total_emails)
                            
                    except Exception as e:
                        write_log(f"Error processing task {task.uid}: {e}", True)
                        results.append(ProcessingResult(
                            uid=task.uid,
                            success=False,
                            action="ERROR",
                            category="UNKNOWN",
                            confidence=0.0,
                            reason=f"Processing error: {str(e)}",
                            error=str(e)
                        ))
                
                # Final progress update
                if process_callback:
                    process_callback(1.0, total_emails, total_emails)
        
        # Flush any pending bulk operations
        self.bulk_manager.flush_all()
        
        elapsed = time.time() - start_time
        rate = total_emails / elapsed if elapsed > 0 else 0
        
        write_log(f"Parallel processing complete: {total_emails} emails in {elapsed:.2f}s ({rate:.1f} emails/sec)", False)
        
        return results
    
    def _process_single_email(self, email_processor, task: ProcessingTask) -> ProcessingResult:
        """
        Process a single email (runs in worker thread)
        """
        start_time = time.time()
        
        try:
            with monitor_operation("parallel_processing", "process_email", {"uid": task.uid}):
                # Parse email headers
                import email
                try:
                    msg = email.message_from_bytes(task.headers.encode("utf-8", errors="ignore"))
                except Exception:
                    msg = email.message_from_string(task.headers)
                
                # Extract key fields
                from atlas_email.utils.domain_validator import decode_header_value
                
                subject = decode_header_value(msg.get('Subject', ''))
                sender = decode_header_value(msg.get('From', ''))
                
                # Get classification result
                classification_result = self._classify_email(
                    email_processor, 
                    sender, 
                    subject, 
                    task.headers,
                    task.uid
                )
                
                # Determine action
                if classification_result['is_spam']:
                    action = "DELETED"
                else:
                    action = "PRESERVED"
                
                # Queue for bulk database operation
                email_data = {
                    'uid': task.uid,
                    'folder_name': task.folder_name,
                    'sender': sender,
                    'subject': subject,
                    'date_received': datetime.now().isoformat(),
                    'result': action,
                    'confidence': classification_result['confidence'],
                    'predicted_category': classification_result['category'],
                    'method': classification_result.get('method', 'PARALLEL_PROCESSOR'),
                    'account_id': getattr(email_processor, 'account_id', None)
                }
                
                # Add to bulk queue (thread-safe)
                self.bulk_manager.add_email_record(email_data)
                
                processing_time = time.time() - start_time
                
                return ProcessingResult(
                    uid=task.uid,
                    success=True,
                    action=action,
                    category=classification_result['category'],
                    confidence=classification_result['confidence'],
                    reason=classification_result.get('reason', ''),
                    processing_time=processing_time,
                    metadata=classification_result
                )
                
        except Exception as e:
            error_msg = f"Error processing email {task.uid}: {str(e)}\n{traceback.format_exc()}"
            write_log(error_msg, True)
            
            return ProcessingResult(
                uid=task.uid,
                success=False,
                action="ERROR",
                category="UNKNOWN",
                confidence=0.0,
                reason=f"Processing error: {str(e)}",
                error=error_msg,
                processing_time=time.time() - start_time
            )
    
    def _classify_email(self, email_processor, sender: str, subject: str, headers: str, uid: str) -> Dict[str, Any]:
        """
        Classify email using the processor's classification logic
        """
        # Check if A/B testing is enabled
        if email_processor.ab_testing_enabled and email_processor.ab_classifier:
            # Extract domain from sender
            domain = None
            if '<' in sender and '>' in sender:
                email_part = sender.split('<')[1].split('>')[0]
                if '@' in email_part:
                    domain = email_part.split('@')[1]
            elif '@' in sender:
                domain = sender.split('@')[1]
            
            # Use A/B classifier
            ab_result = email_processor.ab_classifier.classify_with_ab_testing(
                sender=sender,
                subject=subject,
                domain=domain,
                headers=headers
            )
            
            # Map results
            if ab_result['classifier_used'] == 'new':
                category_mapping = {
                    'Dangerous': 'Phishing',
                    'Commercial Spam': 'Business Opportunity Spam',
                    'Scams': 'Payment Scam',
                    'Legitimate Marketing': 'Promotional Email'
                }
                category = category_mapping.get(ab_result['category'], ab_result['category'])
                confidence = ab_result['confidence']
            else:
                category = ab_result.get('predicted_category', 'Unknown')
                confidence = ab_result.get('category_confidence', 0.75)
                
            spam_categories = [
                'Financial & Investment Spam', 'Gambling Spam', 'Health & Medical Spam',
                'Adult & Dating Spam', 'Business Opportunity Spam', 'Brand Impersonation',
                'Payment Scam', 'Phishing', 'Education/Training Spam', 'Real Estate Spam',
                'Legal & Compensation Scams', 'Marketing Spam', 'Promotional Email'
            ]
            
            is_spam = category in spam_categories
            
        else:
            # Use keyword processor
            category = email_processor.keyword_processor.process_keywords(
                headers="",
                sender=sender,
                subject=subject
            )
            
            # Simple spam detection based on category
            spam_keywords = ['spam', 'phishing', 'scam', 'adult', 'gambling']
            is_spam = any(keyword in category.lower() for keyword in spam_keywords)
            confidence = 0.75  # Default confidence
        
        return {
            'is_spam': is_spam,
            'category': category,
            'confidence': confidence,
            'reason': f"Classified as {category}",
            'method': 'PARALLEL_CLASSIFICATION'
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        with self._processing_lock:
            avg_time = sum(self.stats['processing_times']) / len(self.stats['processing_times']) \
                      if self.stats['processing_times'] else 0
            
            return {
                'total_processed': self.stats['total_processed'],
                'successful': self.stats['successful'],
                'failed': self.stats['failed'],
                'success_rate': self.stats['successful'] / self.stats['total_processed'] \
                               if self.stats['total_processed'] > 0 else 0,
                'avg_processing_time': avg_time,
                'worker_count': self.worker_count,
                'queue_size': self.queue_size
            }
    
    def shutdown(self):
        """Graceful shutdown"""
        self._shutdown = True
        
        # Flush pending operations
        self.bulk_manager.flush_all()
        
        write_log("Parallel processor shutdown complete", False)


# Producer-consumer implementation for streaming processing
class StreamingParallelProcessor:
    """
    Streaming parallel processor for handling very large email batches
    """
    
    def __init__(self, worker_count: int = None):
        self.processor = ParallelEmailProcessor(worker_count=worker_count)
        self.producer_thread = None
        self.consumer_threads = []
        self._stop_event = threading.Event()
    
    @performance_monitor("parallel_processing")
    def process_email_stream(self,
                           email_generator,
                           email_processor,
                           folder_name: str,
                           chunk_size: int = 100) -> Dict[str, Any]:
        """
        Process emails in streaming fashion
        
        Args:
            email_generator: Generator yielding (uid, headers) tuples
            email_processor: EmailProcessor instance
            folder_name: Folder being processed
            chunk_size: Size of chunks to process
            
        Returns:
            Processing statistics
        """
        chunks_processed = 0
        total_processed = 0
        
        try:
            # Process in chunks
            chunk = []
            for uid, headers in email_generator:
                chunk.append((uid, headers))
                
                if len(chunk) >= chunk_size:
                    # Process chunk
                    results = self.processor.process_emails_parallel(
                        email_processor,
                        chunk,
                        folder_name
                    )
                    
                    chunks_processed += 1
                    total_processed += len(results)
                    chunk = []
                    
                    # Check for stop signal
                    if self._stop_event.is_set():
                        break
            
            # Process remaining emails
            if chunk and not self._stop_event.is_set():
                results = self.processor.process_emails_parallel(
                    email_processor,
                    chunk,
                    folder_name
                )
                total_processed += len(results)
        
        finally:
            # Ensure all operations are flushed
            self.processor.bulk_manager.flush_all()
        
        return {
            'chunks_processed': chunks_processed,
            'total_processed': total_processed,
            'statistics': self.processor.get_statistics()
        }
    
    def stop(self):
        """Stop streaming processing"""
        self._stop_event.set()
        self.processor.shutdown()