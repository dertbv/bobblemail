#!/usr/bin/env python3
"""
Test script for real penny stock analysis
"""

from app_real_data import RealPennyStockAnalyzer

def test_analysis():
    print("Testing Real Penny Stock Analysis...")
    
    try:
        analyzer = RealPennyStockAnalyzer()
        results = analyzer.run_analysis()
        
        print(f"\nAnalysis completed successfully!")
        print(f"Total stocks analyzed: {results['total_analyzed']}")
        print(f"Top 10 picks found: {len(results['top_10_picks'])}")
        
        print("\nTop 5 Picks:")
        for i, pick in enumerate(results['top_10_picks'][:5], 1):
            print(f"{i}. {pick['ticker']}: ${pick['current_price']:.2f} → ${pick['target_price']:.2f} "
                  f"({pick['upside_potential']:.1f}% upside, Score: {pick['composite_score']:.1f})")
        
        return True
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        return False

if __name__ == "__main__":
    test_analysis()