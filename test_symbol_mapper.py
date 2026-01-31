"""
Test script for symbol mapper
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.symbol_mapper import symbol_mapper

def test_symbol_mapper():
    print("Testing Symbol Mapper...")
    print("=" * 60)
    
    # Test gold mappings
    assert symbol_mapper.normalize_symbol("GOLD") == "GLD", "GOLD should map to GLD"
    assert symbol_mapper.normalize_symbol("XAU") == "GLD", "XAU should map to GLD"
    assert symbol_mapper.normalize_symbol("XAUUSD") == "GLD", "XAUUSD should map to GLD"
    print("✓ Gold mappings work")
    
    # Test silver mappings
    assert symbol_mapper.normalize_symbol("SILVER") == "SLV", "SILVER should map to SLV"
    assert symbol_mapper.normalize_symbol("XAG") == "SLV", "XAG should map to SLV"
    print("✓ Silver mappings work")
    
    # Test oil mappings
    assert symbol_mapper.normalize_symbol("OIL") == "USO", "OIL should map to USO"
    assert symbol_mapper.normalize_symbol("CRUDE") == "USO", "CRUDE should map to USO"
    print("✓ Oil mappings work")
    
    # Test crypto mappings
    assert symbol_mapper.normalize_symbol("BITCOIN") == "BITO", "BITCOIN should map to BITO"
    assert symbol_mapper.normalize_symbol("BTC") == "BITO", "BTC should map to BITO"
    print("✓ Crypto mappings work")
    
    # Test that valid symbols pass through
    assert symbol_mapper.normalize_symbol("PLTR") == "PLTR", "PLTR should stay PLTR"
    assert symbol_mapper.normalize_symbol("AAPL") == "AAPL", "AAPL should stay AAPL"
    assert symbol_mapper.normalize_symbol("TSLA") == "TSLA", "TSLA should stay TSLA"
    print("✓ Valid symbols pass through unchanged")
    
    # Test case insensitivity
    assert symbol_mapper.normalize_symbol("gold") == "GLD", "lowercase gold should map to GLD"
    assert symbol_mapper.normalize_symbol("Gold") == "GLD", "mixed case Gold should map to GLD"
    print("✓ Case insensitivity works")
    
    # Test custom mapping
    symbol_mapper.add_mapping("TEST", "TESTSTOCK")
    assert symbol_mapper.normalize_symbol("TEST") == "TESTSTOCK", "Custom mapping should work"
    print("✓ Custom mappings work")
    
    print("=" * 60)
    print("All tests passed! ✓")
    
    # Show all mappings
    print("\nAll symbol mappings:")
    mappings = symbol_mapper.get_all_mappings()
    for alt, official in sorted(mappings.items())[:10]:
        print(f"  {alt:15} → {official}")
    print(f"  ... and {len(mappings) - 10} more")

if __name__ == "__main__":
    test_symbol_mapper()
