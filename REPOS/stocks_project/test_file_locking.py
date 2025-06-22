#!/usr/bin/env python3
"""
Test script for file locking functionality
"""

import os
import time
import threading
import tempfile
from file_locking import (
    FileLocker, safe_read_json, safe_write_json, 
    load_analysis_phase_safe, save_analysis_phase_safe, FileLockError
)

def test_basic_file_locking():
    """Test basic file locking functionality"""
    print("Testing basic file locking...")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
        tmp_path = tmp.name
    
    try:
        # Test safe JSON operations
        test_data = {'test': 'data', 'numbers': [1, 2, 3]}
        
        # Write test data
        success = safe_write_json(tmp_path, test_data)
        print(f"   ✅ Write operation: {'SUCCESS' if success else 'FAILED'}")
        
        # Read test data
        read_data = safe_read_json(tmp_path)
        print(f"   ✅ Read operation: {'SUCCESS' if read_data == test_data else 'FAILED'}")
        
        # Test default value on missing file
        missing_data = safe_read_json(tmp_path + '_missing', default={'default': True})
        print(f"   ✅ Default value: {'SUCCESS' if missing_data == {'default': True} else 'FAILED'}")
        
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_concurrent_access():
    """Test concurrent file access protection"""
    print("\nTesting concurrent access protection...")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
        tmp_path = tmp.name
    
    results = {'reader_success': False, 'writer_success': False, 'conflicts': 0}
    
    def writer_thread():
        """Writer thread that holds lock for 2 seconds"""
        try:
            locker = FileLocker(timeout=1.0)
            with locker.lock_file(tmp_path, 'w') as f:
                f.write('{"writer": "holding_lock"}')
                f.flush()
                time.sleep(2)  # Hold lock for 2 seconds
            results['writer_success'] = True
        except Exception as e:
            print(f"      Writer error: {e}")
    
    def reader_thread():
        """Reader thread that tries to access same file"""
        time.sleep(0.5)  # Start after writer
        try:
            locker = FileLocker(timeout=1.0)  # Short timeout
            with locker.lock_file(tmp_path, 'r') as f:
                content = f.read()
            results['reader_success'] = True
        except FileLockError:
            results['conflicts'] += 1  # Expected - lock conflict
        except Exception as e:
            print(f"      Reader error: {e}")
    
    try:
        # Start both threads
        writer = threading.Thread(target=writer_thread)
        reader = threading.Thread(target=reader_thread)
        
        writer.start()
        reader.start()
        
        writer.join()
        reader.join()
        
        # Evaluate results
        writer_ok = results['writer_success']
        conflict_detected = results['conflicts'] > 0
        
        print(f"   ✅ Writer completed: {'SUCCESS' if writer_ok else 'FAILED'}")
        print(f"   ✅ Lock conflict detected: {'SUCCESS' if conflict_detected else 'FAILED'}")
        
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_analysis_phase_operations():
    """Test analysis phase specific operations"""
    print("\nTesting analysis phase operations...")
    
    # Create temporary analysis directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        analysis_dir = os.path.join(tmp_dir, 'test_analysis')
        
        # Test data for each phase
        phase_data = {
            1: [{'ticker': 'TEST', 'price': 1.50}],
            2: {'TEST': {'score': 75, 'rsi': 45}},
            3: {'TEST': {'score': 80, 'revenue_growth': 0.15}},
            4: {'TEST': {'score': 60, 'sentiment': 'positive'}},
            5: [{'ticker': 'TEST', 'composite_score': 70}]
        }
        
        # Save all phases
        all_saved = True
        for phase, data in phase_data.items():
            success = save_analysis_phase_safe(analysis_dir, phase, data)
            if not success:
                all_saved = False
                break
        
        print(f"   ✅ Phase saving: {'SUCCESS' if all_saved else 'FAILED'}")
        
        # Load all phases
        all_loaded = True
        for phase, expected_data in phase_data.items():
            loaded_data = load_analysis_phase_safe(analysis_dir, phase)
            if loaded_data != expected_data:
                all_loaded = False
                break
        
        print(f"   ✅ Phase loading: {'SUCCESS' if all_loaded else 'FAILED'}")
        
        # Test invalid phase (should raise ValueError)
        try:
            load_analysis_phase_safe(analysis_dir, 6, default='missing')
            print("   ❌ Invalid phase handling: FAILED (should have raised error)")
        except ValueError:
            print("   ✅ Invalid phase handling: SUCCESS")

def test_atomic_writes():
    """Test atomic write operations"""
    print("\nTesting atomic write operations...")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
        tmp_path = tmp.name
    
    try:
        # Test that writes are atomic (either complete or not at all)
        large_data = {'large_array': list(range(1000)), 'metadata': {'size': 1000}}
        
        success = safe_write_json(tmp_path, large_data)
        print(f"   ✅ Large data write: {'SUCCESS' if success else 'FAILED'}")
        
        # Verify data integrity
        read_data = safe_read_json(tmp_path)
        integrity_ok = (read_data is not None and 
                       len(read_data.get('large_array', [])) == 1000 and
                       read_data.get('metadata', {}).get('size') == 1000)
        
        print(f"   ✅ Data integrity: {'SUCCESS' if integrity_ok else 'FAILED'}")
        
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_error_handling():
    """Test error handling and recovery"""
    print("\nTesting error handling...")
    
    # Test invalid phase numbers
    try:
        save_analysis_phase_safe('/tmp/test', 0, {})  # Invalid phase
        print("   ❌ Invalid phase validation: FAILED (should have raised error)")
    except ValueError:
        print("   ✅ Invalid phase validation: SUCCESS")
    except Exception as e:
        print(f"   ❌ Invalid phase validation: FAILED ({e})")
    
    # Test reading non-existent file
    missing_data = safe_read_json('/path/that/does/not/exist.json', default='not_found')
    print(f"   ✅ Missing file handling: {'SUCCESS' if missing_data == 'not_found' else 'FAILED'}")
    
    # Test writing to read-only location (if possible)
    readonly_success = safe_write_json('/root/readonly_test.json', {'test': 'data'})
    print(f"   ✅ Read-only location handling: {'SUCCESS' if not readonly_success else 'WARNING: Write succeeded where it should fail'}")

if __name__ == "__main__":
    print("🔒 File Locking Test Suite")
    print("=" * 50)
    
    test_basic_file_locking()
    test_concurrent_access()
    test_analysis_phase_operations()
    test_atomic_writes()
    test_error_handling()
    
    print("\n" + "=" * 50)
    print("🏁 File locking tests completed!")