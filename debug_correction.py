#!/usr/bin/env python3
"""
Debug script to test correction detection with full logging.
Shows exactly what's happening at each step.
"""

import requests
import json
import time

BACKEND = "http://localhost:8001"

def test_correction_with_logs():
    """Test correction detection and show detailed logs."""
    
    print("\n" + "="*80)
    print("CORRECTION DETECTION DEBUG TEST")
    print("="*80 + "\n")
    
    # Message 1: Create initial asset
    print("📝 MESSAGE 1: 'I invested ₹50,000 in HDFC mutual fund'")
    print("-" * 80)
    
    response1 = requests.post(
        f"{BACKEND}/api/chat",
        json={"message": "I invested ₹50,000 in HDFC mutual fund"},
        headers={"Content-Type": "application/json"}
    )
    
    if response1.status_code == 200:
        data1 = response1.json()
        result1 = data1.get("memory_storage_result", {})
        
        print(f"✓ Nodes created: {result1.get('nodes_created', 0)}")
        print(f"✓ Corrections applied: {result1.get('corrections_applied', 0)}")
        print(f"✓ Nodes updated: {result1.get('nodes_updated', 0)}")
    else:
        print(f"✗ Error: {response1.status_code}")
        print(response1.text)
    
    time.sleep(2)
    
    # Message 2: Correction
    print("\n📝 MESSAGE 2: 'No sorry I invested ₹5,000 in HDFC mutual fund'")
    print("-" * 80)
    
    response2 = requests.post(
        f"{BACKEND}/api/chat",
        json={"message": "No sorry I invested ₹5,000 in HDFC mutual fund"},
        headers={"Content-Type": "application/json"}
    )
    
    if response2.status_code == 200:
        data2 = response2.json()
        result2 = data2.get("memory_storage_result", {})
        
        print(f"✓ Nodes created: {result2.get('nodes_created', 0)}")
        print(f"✓ Corrections applied: {result2.get('corrections_applied', 0)}")
        print(f"✓ Nodes updated: {result2.get('nodes_updated', 0)}")
        print(f"✓ Duplicates merged: {result2.get('duplicates_merged', 0)}")
        
        # Full response for debugging
        print("\n📋 Full response:")
        print(json.dumps(data2, indent=2))
        
        # Verify the fix worked
        print("\n✅ VERIFICATION:")
        if result2.get('nodes_created', 0) == 0:
            print("  ✓ NO new nodes created (duplicate bug FIXED!)")
        else:
            print(f"  ✗ New nodes created: {result2.get('nodes_created', 0)} (DUPLICATE BUG STILL EXISTS!)")
        
        if result2.get('corrections_applied', 0) > 0:
            print(f"  ✓ Correction detected ({result2.get('corrections_applied', 0)})")
        else:
            print("  ✗ Correction NOT detected (threshold issue?)")
            
    else:
        print(f"✗ Error: {response2.status_code}")
        print(response2.text)
    
    print("\n" + "="*80)
    print("END OF DEBUG TEST")
    print("="*80 + "\n")
    
    print("\n📋 IMPORTANT: Check the backend terminal for detailed logs:")
    print("  - [ContradictionDetector] messages")
    print("  - [EntityDedup] messages")
    print("  - [CorrectionOrch] messages")
    print("\nIf you see 'NO correction detected', the keyword threshold fix didn't work.")
    print("Look for: [ContradictionDetector] NO correction. Explicit:xxx")

if __name__ == "__main__":
    test_correction_with_logs()
