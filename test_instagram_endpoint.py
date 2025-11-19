#!/usr/bin/env python3
"""
Test script for the Instagram data endpoint.
Run this against local dev server or production.
"""
import requests
import json

# Change this to test locally or production
BASE_URL = "http://127.0.0.1:5000"  # Local dev
# BASE_URL = "https://funr-production.up.railway.app"  # Production

ENDPOINT = f"{BASE_URL}/api/save-instagram-data"

# Test cases
test_messages = [
    "Check out this reel: https://www.instagram.com/reel/ABC123xyz/",
    "Look at this https://instagram.com/p/DEF456/ amazing post!",
    "Just a message with no Instagram link",
    "Multiple links: https://www.instagram.com/reel/GHI789/ and https://instagram.com/reel/JKL012/",
]

print(f"Testing endpoint: {ENDPOINT}\n")
print("=" * 60)

for i, message in enumerate(test_messages, 1):
    print(f"\nTest {i}: {message[:50]}...")
    
    # Test with form-encoded data (Twilio format)
    print("  → Sending as form-encoded...")
    try:
        response = requests.post(
            ENDPOINT,
            data={"Body": message},
            headers={"Accept": "application/json"},
            timeout=10
        )
        print(f"  ✓ Status: {response.status_code}")
        print(f"  ✓ Response: {json.dumps(response.json(), indent=4)}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # Test with JSON data
    print("  → Sending as JSON...")
    try:
        response = requests.post(
            ENDPOINT,
            json={"Body": message},
            headers={"Accept": "application/json"},
            timeout=10
        )
        print(f"  ✓ Status: {response.status_code}")
        print(f"  ✓ Response: {json.dumps(response.json(), indent=4)}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n" + "=" * 60)
print("Testing complete!")
