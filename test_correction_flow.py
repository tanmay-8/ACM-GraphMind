#!/usr/bin/env python3
"""
Test script for verifying the complete correction detection and entity deduplication flow.

This script will:
1. Send "I invested 60000 rs in HDFC" → Create node
2. Send "No I invested 60000 rs" (correction) → Should UPDATE existing node, not create duplicate
3. Verify: corrections_applied=1, nodes_created=0, nodes_updated=1

Expected behavior:
- ContradictionDetector detects "No" as correction (threshold lowered to 0.3)
- EntityDeduplicator finds existing HDFC asset
- UpdateHandler updates the node
- NO duplicate created!
"""

import sys
import json
import time
import requests
from typing import Dict, Any, Optional

# Configuration
BACKEND_HOST = "http://localhost:8001"
API_BASE = f"{BACKEND_HOST}/api"

# Test user
TEST_USER_ID = "test_user_123"
TEST_TOKEN = "fake_token_for_testing"  # Set real token if needed

# Color codes for terminal output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(text: str):
    """Print formatted header."""
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}{text:^80}{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")


def print_section(text: str):
    """Print section header."""
    print(f"\n{BOLD}{YELLOW}→ {text}{RESET}")


def print_success(text: str):
    """Print success message."""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{RED}✗ {text}{RESET}")


def print_info(text: str):
    """Print info message."""
    print(f"{BLUE}ℹ {text}{RESET}")


def send_message(message: str, user_id: str = TEST_USER_ID) -> Optional[Dict[str, Any]]:
    """
    Send a message to the chat API and return the response.
    
    Args:
        message: Message text
        user_id: User ID
        
    Returns:
        Response dictionary or None if failed
    """
    headers = {
        "Authorization": f"Bearer {TEST_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": message,
        "user_id": user_id
    }
    
    url = f"{API_BASE}/chat"
    
    try:
        print_info(f"Sending: {message}")
        start_time = time.time()
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        elapsed = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Response received in {elapsed:.1f}ms")
            return data
        else:
            print_error(f"HTTP {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return None


def extract_metrics(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract metrics from response.
    
    Expected response structure:
    {
        "memory_storage_result": {
            "nodes_created": 1,
            "nodes_updated": 0,
            "corrections_applied": 0,
            "duplicates_merged": 0,
            ...
        },
        ...
    }
    """
    try:
        msr = response.get("memory_storage_result", {})
        return {
            "nodes_created": msr.get("nodes_created", 0),
            "nodes_updated": msr.get("nodes_updated", 0),
            "corrections_applied": msr.get("corrections_applied", 0),
            "duplicates_merged": msr.get("duplicates_merged", 0),
            "relationships_created": msr.get("relationships_created", 0),
            "facts_created": msr.get("facts_created", 0),
        }
    except:
        return {}


def print_metrics(metrics: Dict[str, Any], label: str = ""):
    """Print metrics in a formatted way."""
    if not metrics:
        print_error("No metrics found in response")
        return
    
    print(f"\n{BOLD}Metrics {label}:{RESET}")
    print(f"  Nodes Created:       {YELLOW}{metrics.get('nodes_created', 0):>3}{RESET}")
    print(f"  Nodes Updated:       {YELLOW}{metrics.get('nodes_updated', 0):>3}{RESET}")
    print(f"  Corrections Applied: {YELLOW}{metrics.get('corrections_applied', 0):>3}{RESET}")
    print(f"  Duplicates Merged:   {YELLOW}{metrics.get('duplicates_merged', 0):>3}{RESET}")
    print(f"  Relationships:       {YELLOW}{metrics.get('relationships_created', 0):>3}{RESET}")
    print(f"  Facts:               {YELLOW}{metrics.get('facts_created', 0):>3}{RESET}")


def print_full_response(response: Dict[str, Any], label: str = ""):
    """Print full response for debugging."""
    print(f"\n{BOLD}Full Response {label}:{RESET}")
    print(json.dumps(response, indent=2))


def test_simple_message() -> bool:
    """
    Test 1: Simple message (should create 1 node, 0 corrections)
    Message: "I invested 60000 rs in HDFC"
    Expected: nodes_created=1, corrections_applied=0
    """
    print_section("TEST 1: Simple Message (No Correction)")
    print("Message: 'I invested 60000 rs in HDFC'")
    print("Expected: Create new asset node")
    
    response = send_message("I invested 60000 rs in HDFC")
    if not response:
        print_error("Failed to get response")
        return False
    
    metrics = extract_metrics(response)
    print_metrics(metrics, "(after simple message)")
    
    # Verify expectations
    created = metrics.get("nodes_created", 0)
    updated = metrics.get("nodes_updated", 0)
    corrections = metrics.get("corrections_applied", 0)
    
    if created >= 1 and corrections == 0:
        print_success(f"Message 1 created HDFC node as expected")
        return True
    else:
        print_error(f"Unexpected metrics: created={created}, updated={updated}, corrections={corrections}")
        return False


def test_correction_message() -> bool:
    """
    Test 2: Correction message (should UPDATE existing, 0 new creates)
    Message: "No I invested 60000 rs"
    Expected: nodes_created=0, corrections_applied=1, nodes_updated=1, duplicates_merged=0
    
    This is the CRITICAL TEST - if this fails, the duplicate bug still exists!
    """
    print_section("TEST 2: Correction Message (CRITICAL)")
    print("Message: 'No I invested 60000 rs'")
    print("Expected: Detect correction, UPDATE existing HDFC node (NO new node!)")
    
    time.sleep(1)  # Small delay between messages
    
    response = send_message("No I invested 60000 rs")
    if not response:
        print_error("Failed to get response")
        return False
    
    metrics = extract_metrics(response)
    print_metrics(metrics, "(after correction)")
    
    # Verify expectations - THIS IS THE KEY TEST
    created = metrics.get("nodes_created", 0)
    updated = metrics.get("nodes_updated", 0)
    corrections = metrics.get("corrections_applied", 0)
    duplicates_merged = metrics.get("duplicates_merged", 0)
    
    print("\nVerification:")
    
    # Check 1: No new nodes created (critical!)
    if created == 0:
        print_success(f"✓ NO new nodes created (created={created})")
        check1_pass = True
    else:
        print_error(f"✗ DUPLICATE BUG STILL EXISTS! New nodes created: {created}")
        check1_pass = False
    
    # Check 2: Correction was detected
    if corrections > 0:
        print_success(f"✓ Correction detected (corrections_applied={corrections})")
        check2_pass = True
    else:
        print_error(f"✗ Correction NOT detected (corrections_applied={corrections})")
        check2_pass = False
    
    # Check 3: Update was applied
    if updated > 0:
        print_success(f"✓ Node updated (nodes_updated={updated})")
        check3_pass = True
    else:
        print_error(f"✗ Node NOT updated (nodes_updated={updated})")
        check3_pass = False
    
    if check1_pass and check2_pass and check3_pass:
        print_success("\n🎯 CRITICAL TEST PASSED! Correction flow working perfectly!")
        return True
    else:
        print_error("\n🔴 CRITICAL TEST FAILED! Duplicate bug or correction detection issue!")
        return False


def test_keyword_detection():
    """
    Test 3: Verify keyword threshold fix
    Test various correction keywords to ensure threshold=0.3 works
    """
    print_section("TEST 3: Keyword Detection")
    
    keywords_to_test = [
        "no",
        "actually I meant something else",
        "wait, that was wrong",
        "correction: I invested 50000",
    ]
    
    print("Testing keyword detection with threshold=0.3...")
    
    for keyword_msg in keywords_to_test:
        response = send_message(keyword_msg)
        if response:
            metrics = extract_metrics(response)
            corrections = metrics.get("corrections_applied", 0)
            print(f"  '{keyword_msg}' → corrections_applied={corrections}")
        time.sleep(0.5)


def main():
    """Run all tests."""
    print_header("CORRECTION DETECTION AND DEDUPLICATION TEST SUITE")
    
    # Check backend connectivity
    print_section("Pre-flight Checks")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        print_success(f"Backend is reachable at {BACKEND_HOST}")
    except:
        print_error(f"Backend is NOT reachable at {BACKEND_HOST}")
        print_error("Make sure backend is running: cd backend && python -m uvicorn api.main:app --reload")
        return
    
    # Run tests
    print_header("RUNNING TESTS")
    
    test1_pass = test_simple_message()
    time.sleep(2)  # Wait between tests
    test2_pass = test_correction_message()
    time.sleep(2)
    test_keyword_detection()
    
    # Summary
    print_header("TEST SUMMARY")
    
    if test1_pass:
        print_success("Test 1 (Simple Message): PASSED ✓")
    else:
        print_error("Test 1 (Simple Message): FAILED ✗")
    
    if test2_pass:
        print_success("Test 2 (Correction Detection): PASSED ✓")
    else:
        print_error("Test 2 (Correction Detection): FAILED ✗")
    
    print("\n" + BOLD + "OVERALL RESULT:" + RESET)
    if test1_pass and test2_pass:
        print_success("\n🎉 ALL CRITICAL TESTS PASSED! The duplicate bug is FIXED!")
        print("Correction detection and entity deduplication is now working correctly!\n")
    else:
        print_error("\n❌ SOME TESTS FAILED! Review logs above for details.\n")


if __name__ == "__main__":
    main()
