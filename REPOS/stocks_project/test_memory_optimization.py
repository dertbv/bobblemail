#!/usr/bin/env python3
"""
Test script for memory optimization improvements
"""

import sys
import os
sys.path.append('.')

from app import get_latest_analysis_dir, get_stock_from_analysis, get_category_data_optimized

def test_memory_optimizations():
    """Test the memory optimization functions"""
    print("Testing memory optimizations...")
    
    # Test 1: Directory caching
    print("\n1. Testing directory caching...")
    dir1 = get_latest_analysis_dir()
    dir2 = get_latest_analysis_dir()  # Should use cache
    print(f"   Latest directory: {dir1}")
    print(f"   Cache hit (same result): {dir1 == dir2}")
    
    # Test 2: Individual stock lookup
    print("\n2. Testing individual stock lookup...")
    if dir1:
        # Try to find a stock without loading full dataset
        test_tickers = ['HUYA', 'YMM', 'WB', 'SNDL', 'NOK']
        for ticker in test_tickers:
            stock = get_stock_from_analysis(ticker)
            if stock:
                print(f"   Found {ticker}: ${stock.get('current_price', 'N/A'):.2f}")
                break
        else:
            print("   No test stocks found in analysis")
    
    # Test 3: Category filtering
    print("\n3. Testing category data optimization...")
    for category in ['under-5', '5-to-10', '10-to-20']:
        data = get_category_data_optimized(category)
        if data:
            print(f"   {category}: {data['count']} stocks")
        else:
            print(f"   {category}: No data")
    
    print("\nMemory optimization tests completed!")

if __name__ == "__main__":
    test_memory_optimizations()