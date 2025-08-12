#!/usr/bin/env python3
"""
Test script for ACIMguide Firebase Cloud Functions
Tests the deployed API endpoints to verify functionality
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Firebase project configuration
PROJECT_ID = "acim-guide-test"
REGION = "us-central1"

# Function URLs
CHAT_URL = f"https://{REGION}-{PROJECT_ID}.cloudfunctions.net/chatWithAssistant"
CLEAR_URL = f"https://{REGION}-{PROJECT_ID}.cloudfunctions.net/clearThread"

def test_chat_function():
    """Test the chatWithAssistant function"""
    print("🧪 Testing chatWithAssistant function...")
    
    # Test payload
    payload = {
        "data": {
            "message": "What is the main teaching of A Course in Miracles?",
            "tone": "gentle"
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(CHAT_URL, json=payload, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Chat function is working!")
            return True
        else:
            print("❌ Chat function returned an error")
            return False
            
    except Exception as e:
        print(f"❌ Error testing chat function: {e}")
        return False

def test_clear_function():
    """Test the clearThread function"""
    print("\n🧪 Testing clearThread function...")
    
    payload = {"data": {}}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(CLEAR_URL, json=payload, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Clear function is working!")
            return True
        else:
            print("❌ Clear function returned an error")
            return False
            
    except Exception as e:
        print(f"❌ Error testing clear function: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing ACIMguide API Endpoints")
    print("=" * 50)
    
    # Note: These tests will fail with authentication errors since we're not 
    # sending proper Firebase Auth tokens, but they'll confirm the functions
    # are deployed and responding
    
    chat_result = test_chat_function()
    clear_result = test_clear_function()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"Chat Function: {'✅ Deployed' if chat_result else '❌ Issues'}")
    print(f"Clear Function: {'✅ Deployed' if clear_result else '❌ Issues'}")
    
    print("\n💡 Note: Authentication errors are expected when testing without")
    print("   proper Firebase Auth tokens. The important thing is that the")
    print("   functions are deployed and responding to requests.")

if __name__ == "__main__":
    main()
