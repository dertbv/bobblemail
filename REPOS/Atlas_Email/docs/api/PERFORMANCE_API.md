# Atlas_Email Performance API Reference

**Version**: 2.0  
**Last Updated**: 2025-07-05

## Table of Contents
1. [Performance Monitor API](#performance-monitor-api)
2. [Bulk Operations API](#bulk-operations-api)
3. [Cache Manager API](#cache-manager-api)
4. [Parallel Processor API](#parallel-processor-api)
5. [Classifier Optimizer API](#classifier-optimizer-api)
6. [Stream Processor API](#stream-processor-api)

---

## Performance Monitor API

### Module: `atlas_email.utils.performance_monitor`

#### Class: `PerformanceMetrics`
Thread-safe performance metrics collector.

##### Methods

###### `get_instance() -> PerformanceMetrics`
Returns the singleton instance.

###### `record(category: str, operation: str, duration: float, metadata: Dict[str, Any] = None)`
Records a performance metric.

**Parameters:**
- `category`: Category of operation (e.g., "database", "classification")
- `operation`: Specific operation name
- `duration`: Duration in seconds
- `metadata`: Optional additional data

###### `get_stats() -> Dict[str, Dict[str, Any]]`
Returns aggregated statistics.

**Returns:**
```python
{
    "category": {
        "count": int,
        "total": float,
        "avg": float,
        "min": float,
        "max": float,
        "operations": {...}
    }
}
```

#### Decorator: `@performance_monitor(category: str)`
Automatically times function execution.

**Example:**
```python
@performance_monitor("email_processing")
def process_email(email):
    # Function is automatically timed
    pass
```

#### Context Manager: `monitor_operation(category: str, operation: str, metadata: Dict = None)`
Times a code block.

**Example:**
```python
with monitor_operation("database", "bulk_insert", {"count": 1000}):
    # Operation is timed
    perform_bulk_insert()
```

---

## Bulk Operations API

### Module: `atlas_email.models.bulk_operations`

#### Class: `BulkOperationManager`
Manages bulk database operations with automatic batching.

##### Methods

###### `get_instance() -> BulkOperationManager`
Returns the singleton instance.

###### `add_email_record(email_data: Dict[str, Any])`
Adds an email record to the bulk insert queue.

**Parameters:**
- `email_data`: Dictionary containing email fields

**Required fields:**
```python
{
    "uid": str,
    "folder_name": str,
    "sender": str,
    "subject": str,
    # ... other email fields
}
```

###### `add_domain_record(domain_data: Dict[str, Any])`
Adds a domain record to the bulk insert queue.

###### `add_flag_record(flag_data: Dict[str, Any])`
Adds a flag record to the bulk insert queue.

###### `add_analytics_record(analytics_data: Dict[str, Any])`
Adds an analytics record to the bulk insert queue.

###### `flush_all()`
Forces immediate execution of all queued operations.

###### `get_queue_sizes() -> Dict[str, int]`
Returns current queue sizes for monitoring.

**Configuration:**
- Default batch size: 500 records
- Auto-flush triggers at batch size

---

## Cache Manager API

### Module: `atlas_email.utils.cache_manager`

#### Class: `LRUCache`
Thread-safe LRU cache with TTL support.

##### Constructor
```python
LRUCache(max_size: int = 10000, default_ttl: int = 3600)
```

##### Methods

###### `get(key: str) -> Optional[Any]`
Retrieves value from cache.

###### `set(key: str, value: Any, ttl: Optional[int] = None)`
Stores value in cache.

**Parameters:**
- `key`: Cache key
- `value`: Value to cache
- `ttl`: Time-to-live in seconds (uses default if None)

###### `delete(key: str)`
Removes item from cache.

###### `clear()`
Clears entire cache.

###### `get_stats() -> Dict[str, Any]`
Returns cache statistics.

#### Class: `MultiLevelCache`
Manages multiple specialized caches.

##### Cache Types
- `classification`: 2-hour TTL, 50K items
- `domain`: 24-hour TTL, 20K items  
- `geographic`: 7-day TTL, 10K items
- `auth`: 1-hour TTL, 5K items
- `general`: 1-hour TTL, 10K items

##### Methods

###### `get_classification(sender: str, subject: str) -> Optional[Dict]`
###### `set_classification(sender: str, subject: str, result: Dict, ttl: Optional[int] = None)`

###### `get_domain(domain: str) -> Optional[Dict]`
###### `set_domain(domain: str, data: Dict, ttl: Optional[int] = None)`

###### `get_geographic(ip: str) -> Optional[Dict]`
###### `set_geographic(ip: str, data: Dict, ttl: Optional[int] = None)`

#### Helper Functions

###### `get_classification_cache(sender: str, subject: str) -> Optional[Dict]`
Global helper for classification caching.

###### `set_classification_cache(sender: str, subject: str, result: Dict, ttl: int = 7200)`
Global helper for setting classification cache.

---

## Parallel Processor API

### Module: `atlas_email.core.parallel_processor`

#### Class: `ParallelEmailProcessor`
High-performance parallel email processor.

##### Constructor
```python
ParallelEmailProcessor(
    worker_count: int = None,  # Defaults to CPU count
    queue_size: int = 1000,
    batch_size: int = 100
)
```

##### Methods

###### `process_emails_parallel(emails: List[Dict], process_func: Callable, batch_size: int = None) -> List[Any]`
Processes emails in parallel.

**Parameters:**
- `emails`: List of email dictionaries
- `process_func`: Function to process each email
- `batch_size`: Override default batch size

**Returns:** List of results in order

###### `process_with_progress(emails: List[Dict], process_func: Callable, progress_callback: Callable)`
Processes emails with progress updates.

**Progress callback signature:**
```python
def progress_callback(current: int, total: int, percent: float):
    print(f"Progress: {current}/{total} ({percent:.1f}%)")
```

###### `shutdown(wait: bool = True)`
Shuts down the processor gracefully.

###### `get_statistics() -> Dict[str, Any]`
Returns processing statistics.

#### Class: `StreamingParallelProcessor`
Processes large email batches without loading all into memory.

##### Methods

###### `process_email_stream(mail_connection, folder: str, process_func: Callable) -> Dict[str, Any]`
Streams and processes emails from IMAP.

---

## Classifier Optimizer API

### Module: `atlas_email.ml.classifier_cache`

#### Class: `ClassifierOptimizer`
Optimizes classification through caching and early-exit patterns.

##### Methods

###### `check_early_exit(sender: str, subject: str, body: Optional[str] = None) -> Optional[Dict[str, Any]]`
Checks for early-exit spam patterns.

**Returns:**
```python
{
    "is_spam": bool,
    "category": str,
    "confidence": float,
    "method": "EARLY_EXIT",
    "reason": str,
    "processing_time_ms": float
}
```

###### `optimize_classification(classifier_func: Callable, sender: str, subject: str, body: Optional[str] = None, headers: Optional[str] = None) -> Dict[str, Any]`
Optimizes classification with caching and early exit.

**Parameters:**
- `classifier_func`: The actual classification function
- Other parameters passed to classifier

###### `get_statistics() -> Dict[str, Any]`
Returns optimization statistics.

#### Early-Exit Patterns
Pre-configured high-confidence spam patterns:
- Financial scams (95% confidence)
- Adult/dating spam (95% confidence)
- Health/medical spam (90% confidence)
- Prize/lottery scams (95% confidence)
- Phishing attempts (90-95% confidence)
- Auto warranty scams (90% confidence)

#### Function: `get_classifier_optimizer() -> ClassifierOptimizer`
Returns global optimizer instance.

---

## Stream Processor API

### Module: `atlas_email.utils.stream_processor`

#### Class: `MemoryMonitor`
Monitors memory usage and triggers optimization.

##### Constructor
```python
MemoryMonitor(
    threshold_percent: float = 80.0,
    check_interval: float = 5.0
)
```

##### Methods

###### `start_monitoring()`
Starts background memory monitoring.

###### `stop_monitoring()`
Stops memory monitoring.

###### `get_memory_stats() -> MemoryStats`
Returns current memory statistics.

###### `optimize_memory() -> float`
Forces garbage collection and returns MB freed.

#### Class: `StreamingEmailProcessor`
Processes emails in streaming fashion to minimize memory.

##### Constructor
```python
StreamingEmailProcessor(
    chunk_size: int = 100,
    memory_limit_mb: int = 500
)
```

##### Methods

###### `process_email_stream(mail_connection, folder_name: str, process_func: Callable, progress_callback: Optional[Callable] = None) -> Dict[str, Any]`
Processes emails from IMAP in chunks.

**Returns:**
```python
{
    "chunks_processed": int,
    "emails_processed": int,
    "processing_errors": int,
    "memory_optimizations": int,
    "final_memory_mb": float,
    "peak_memory_mb": float
}
```

#### Class: `EmailStreamIterator`
Iterator for streaming email data.

##### Constructor
```python
EmailStreamIterator(
    mail_connection,
    folder_name: str,
    batch_size: int = 50
)
```

##### Usage
```python
for uid, headers in EmailStreamIterator(mail, "INBOX"):
    # Process each email without loading all
    process_email(uid, headers)
```

#### Function: `create_email_stream(mail_connection, folder_name: str, batch_size: int = 50) -> Iterator[Tuple[str, str]]`
Creates an email stream iterator.

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ATLAS_WORKER_COUNT` | CPU count | Number of parallel workers |
| `ATLAS_BULK_BATCH_SIZE` | 500 | Bulk operation batch size |
| `ATLAS_CACHE_ENABLED` | true | Enable/disable caching |
| `ATLAS_MEMORY_LIMIT_MB` | 500 | Memory limit for streaming |
| `ATLAS_CACHE_SIZE_MULTIPLIER` | 1.0 | Scale cache sizes |

### Performance Tuning

#### Worker Count Guidelines
```python
# Light load (< 50 emails/sec)
processor = ParallelEmailProcessor(worker_count=2)

# Normal load (50-100 emails/sec)
processor = ParallelEmailProcessor(worker_count=4)

# Heavy load (100-200 emails/sec)
processor = ParallelEmailProcessor(worker_count=8)

# Stress load (> 200 emails/sec)
processor = ParallelEmailProcessor(worker_count=16)
```

#### Memory Optimization
```python
# Small VPS (< 2GB RAM)
processor = StreamingEmailProcessor(memory_limit_mb=200)

# Standard server (4-8GB RAM)
processor = StreamingEmailProcessor(memory_limit_mb=500)

# High-memory server (> 8GB RAM)
processor = StreamingEmailProcessor(memory_limit_mb=1000)
```

---

## Complete Integration Example

```python
from atlas_email.utils.performance_monitor import performance_monitor, monitor_operation
from atlas_email.models.bulk_operations import BulkOperationManager
from atlas_email.utils.cache_manager import MultiLevelCache
from atlas_email.core.parallel_processor import ParallelEmailProcessor
from atlas_email.ml.classifier_cache import get_classifier_optimizer
from atlas_email.utils.stream_processor import StreamingEmailProcessor

class OptimizedEmailProcessor:
    def __init__(self):
        # Initialize all optimization components
        self.bulk_manager = BulkOperationManager.get_instance()
        self.cache = MultiLevelCache()
        self.parallel_processor = ParallelEmailProcessor(worker_count=4)
        self.classifier_optimizer = get_classifier_optimizer()
        self.stream_processor = StreamingEmailProcessor()
        
    @performance_monitor("main_processing")
    def process_folder(self, mail_connection, folder_name):
        """Process emails with all optimizations"""
        
        def process_single_email(email_data):
            # Check cache first
            cached = self.cache.get_classification(
                email_data['sender'], 
                email_data['subject']
            )
            if cached:
                return cached
            
            # Optimize classification
            with monitor_operation("classification", "optimized"):
                result = self.classifier_optimizer.optimize_classification(
                    self.classify_email,
                    email_data['sender'],
                    email_data['subject'],
                    email_data.get('body')
                )
            
            # Cache result
            self.cache.set_classification(
                email_data['sender'],
                email_data['subject'],
                result
            )
            
            # Queue for bulk insert
            with monitor_operation("database", "queue"):
                self.bulk_manager.add_email_record({
                    **email_data,
                    'classification': result
                })
            
            return result
        
        # Process emails in parallel with streaming
        return self.stream_processor.process_email_stream(
            mail_connection,
            folder_name,
            lambda chunk: self.parallel_processor.process_emails_parallel(
                chunk,
                process_single_email
            )
        )
```

---

## Error Handling

All API methods follow consistent error handling:

1. **Invalid Parameters**: Raise `ValueError` with descriptive message
2. **Resource Errors**: Raise `ResourceError` for system resource issues
3. **Operation Errors**: Return error in result dict or raise specific exception
4. **Thread Safety**: All concurrent operations are thread-safe

Example error handling:
```python
try:
    result = processor.process_emails_parallel(emails, process_func)
except ValueError as e:
    logger.error(f"Invalid parameters: {e}")
except ResourceError as e:
    logger.error(f"Resource issue: {e}")
    # Fall back to sequential processing
except Exception as e:
    logger.exception("Unexpected error in parallel processing")
    # Graceful degradation
```

---

*For more examples and patterns, see the [Performance Optimization Guide](../performance/PERFORMANCE_OPTIMIZATION_GUIDE.md)*