#!/usr/bin/env python3
"""
Simple test script to verify the backend API endpoints
Run this after starting the backend server
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Test the main API endpoints"""
    
    print("Testing Task Manager API endpoints...")
    print("=" * 50)
    
    # Test root endpoint
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✓ Root endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✓ Health endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"✗ Health endpoint failed: {e}")
    
    # Test departments endpoint
    try:
        response = requests.get(f"{BASE_URL}/users/departments/")
        print(f"✓ Departments endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"✗ Departments endpoint failed: {e}")
    
    # Test roles endpoint
    try:
        response = requests.get(f"{BASE_URL}/users/roles/")
        print(f"✓ Roles endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"✗ Roles endpoint failed: {e}")
    
    # Test supervisors endpoint
    try:
        response = requests.get(f"{BASE_URL}/users/supervisors/")
        print(f"✓ Supervisors endpoint: {response.status_code} - {len(response.json())} supervisors")
    except Exception as e:
        print(f"✗ Supervisors endpoint failed: {e}")
    
    # Test user stats endpoint
    try:
        response = requests.get(f"{BASE_URL}/users/stats/")
        print(f"✓ User stats endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"✗ User stats endpoint failed: {e}")
    
    # Test create user endpoint (this will fail without proper data, but tests the endpoint exists)
    try:
        test_user = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpass123",
            "department": "engineering",
            "role": "member"
        }
        response = requests.post(f"{BASE_URL}/users/", json=test_user)
        print(f"✓ Create user endpoint: {response.status_code}")
        if response.status_code == 201:
            print(f"  User created successfully!")
        else:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Create user endpoint failed: {e}")
    
    print("\n" + "=" * 50)
    print("API testing completed!")

if __name__ == "__main__":
    test_endpoints()
