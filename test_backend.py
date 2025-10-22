#!/usr/bin/env python3
"""
Test script to verify the backend API is working
"""

import requests
import json
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_backend():
    base_url = "http://localhost:8000"
    
    print("Testing Paper Roadmap Backend API...")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Make sure the server is running on port 8000")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Root endpoint
    print("\n2. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Root endpoint passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
    
    # Test 3: Roadmap generation (this will fail if no database/papers)
    print("\n3. Testing roadmap generation...")
    try:
        test_query = "machine learning"
        response = requests.post(
            f"{base_url}/roadmap/",
            json={"query": test_query},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Roadmap generation passed")
            data = response.json()
            if 'roadmap' in data:
                print(f"   Generated {len(data['roadmap'])} papers")
            else:
                print("   No roadmap data in response")
        elif response.status_code == 503:
            print("⚠️  Roadmap generation: Backend services not ready (database/papers not set up)")
        else:
            print(f"❌ Roadmap generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Roadmap generation error: {e}")
    
    print("\n" + "=" * 50)
    print("Backend test completed!")
    print("\nIf you see any ❌ errors, check:")
    print("1. Backend server is running (python start_backend.py)")
    print("2. Database is set up with papers")
    print("3. Environment variables are configured (.env file)")
    print("4. Dependencies are installed (pip install -r requirements.txt)")
    
    return True

if __name__ == "__main__":
    test_backend()
