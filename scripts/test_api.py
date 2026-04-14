#!/usr/bin/env python3
"""
Test script for the Galaxy Classification Database and API
"""

import requests
import json
import time

def test_api():
    """Test the API endpoints"""
    base_url = "http://127.0.0.1:5000"

    print("🧪 Testing Galaxy Classification API")
    print("=" * 50)

    # Test health check
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data['status']}")
            print(f"   Database: {data['database']}")
            print(f"   Records: {data['records']}")
        else:
            print(f"❌ Health Check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health Check error: {e}")

    # Test observations endpoint
    try:
        response = requests.get(f"{base_url}/api/observations")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Observations API: {len(data)} records retrieved")
            if data:
                print(f"   Sample: {data[0]['id']} - {data[0]['classification']}")
        else:
            print(f"❌ Observations API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Observations API error: {e}")

    # Test stats endpoint
    try:
        response = requests.get(f"{base_url}/api/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Statistics API: {len(data)} classes")
            for stat in data[:3]:  # Show first 3
                print(f"   {stat['class']}: {stat['count']} samples")
        else:
            print(f"❌ Statistics API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Statistics API error: {e}")

    print("\n📊 API Test Complete")

if __name__ == "__main__":
    print("🚀 Starting Galaxy Classification System Test")
    print("Make sure the Flask app is running on http://127.0.0.1:5000")
    print("Run: cd web && python app.py")
    print()

    time.sleep(2)  # Give user time to start the server
    test_api()