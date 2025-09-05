#!/usr/bin/env python3
"""
Test script for Project Management API endpoints
Run this after starting the server to validate all project endpoints
"""

import requests
import json
import sys
import os
from datetime import datetime, timedelta

# Get the API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def test_endpoint(method, endpoint, data=None, expected_status=200):
    """Test an API endpoint"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        if response.status_code == expected_status:
            print(f"✅ {method} {endpoint} - Status: {response.status_code}")
            if response.content:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   Returned {len(data)} items")
                    elif isinstance(data, dict):
                        if 'message' in data:
                            print(f"   Message: {data['message']}")
                        elif 'id' in data:
                            print(f"   Created/Updated ID: {data['id']}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            return True
        else:
            print(f"❌ {method} {endpoint} - Expected: {expected_status}, Got: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ {method} {endpoint} - Connection error: {e}")
        return False

def test_project_api():
    """Test all project API endpoints"""
    print("🧪 Testing Project Management API Endpoints")
    print("=" * 50)
    
    # Test 1: Get all projects (empty initially)
    print("\n1. Testing GET /projects/")
    test_endpoint("GET", "/projects/")
    
    # Test 2: Get project stats
    print("\n2. Testing GET /projects/stats/")
    test_endpoint("GET", "/projects/stats/")
    
    # Test 3: Get all users (needed for creating projects)
    print("\n3. Testing GET /users/ (for project creation)")
    users_response = requests.get(f"{API_BASE_URL}/users/")
    if users_response.status_code == 200:
        users = users_response.json()
        print(f"✅ Found {len(users)} users")
        
        # Test 4: Get all teams (needed for project creation)
        print("\n4. Testing GET /teams/ (for project creation)")
        teams_response = requests.get(f"{API_BASE_URL}/teams/")
        if teams_response.status_code == 200:
            teams = teams_response.json()
            print(f"✅ Found {len(teams)} teams")
            
            if len(users) >= 1 and len(teams) >= 1:
                # Test 5: Create a project
                print("\n5. Testing POST /projects/")
                
                # Calculate dates
                start_date = datetime.now()
                end_date = start_date + timedelta(days=30)
                
                project_data = {
                    "name": "Test E-commerce Platform",
                    "description": "A comprehensive e-commerce platform with modern features",
                    "manager_id": users[0]["id"],
                    "assigned_teams": [teams[0]["id"]] if teams else [],
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "status": "active"
                }
                
                create_response = requests.post(f"{API_BASE_URL}/projects/", json=project_data)
                if create_response.status_code == 201:
                    project = create_response.json()
                    project_id = project["id"]
                    print(f"✅ Created project with ID: {project_id}")
                    
                    # Test 6: Get specific project
                    print(f"\n6. Testing GET /projects/{project_id}")
                    test_endpoint("GET", f"/projects/{project_id}")
                    
                    # Test 7: Get project teams
                    print(f"\n7. Testing GET /projects/{project_id}/teams")
                    test_endpoint("GET", f"/projects/{project_id}/teams")
                    
                    # Test 8: Update project
                    print(f"\n8. Testing PUT /projects/{project_id}")
                    update_data = {
                        "description": "Updated e-commerce platform with enhanced features",
                        "status": "on_hold"
                    }
                    test_endpoint("PUT", f"/projects/{project_id}", update_data)
                    
                    # Test 9: Add team to project (if there are more teams)
                    if len(teams) > 1:
                        print(f"\n9. Testing POST /projects/{project_id}/teams")
                        team_data = {"team_id": teams[1]["id"]}
                        test_endpoint("POST", f"/projects/{project_id}/teams", team_data)
                    
                    # Test 10: Remove team from project (if we added one)
                    if len(teams) > 1:
                        print(f"\n10. Testing DELETE /projects/{project_id}/teams/{teams[1]['id']}")
                        test_endpoint("DELETE", f"/projects/{project_id}/teams/{teams[1]['id']}", expected_status=204)
                    
                    # Test 11: Delete project
                    print(f"\n11. Testing DELETE /projects/{project_id}")
                    test_endpoint("DELETE", f"/projects/{project_id}", expected_status=204)
                    
                else:
                    print(f"❌ Failed to create project: {create_response.text}")
            else:
                print("⚠️ Not enough users or teams to test project creation")
                print(f"   Users: {len(users)}, Teams: {len(teams)}")
        else:
            print(f"❌ Failed to get teams: {teams_response.text}")
    else:
        print(f"❌ Failed to get users: {users_response.text}")
    
    # Test error cases
    print("\n12. Testing error cases")
    print("   Testing GET non-existent project:")
    test_endpoint("GET", "/projects/99999", expected_status=404)
    
    print("   Testing POST invalid project data:")
    invalid_data = {"name": ""}  # Missing required fields
    test_endpoint("POST", "/projects/", invalid_data, expected_status=422)
    
    print("   Testing POST project with invalid date range:")
    start_date = datetime.now()
    end_date = start_date - timedelta(days=1)  # End date before start date
    
    invalid_date_data = {
        "name": "Invalid Date Project",
        "description": "Project with invalid dates",
        "manager_id": 1,
        "assigned_teams": [1],
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "status": "active"
    }
    test_endpoint("POST", "/projects/", invalid_date_data, expected_status=400)
    
    print("\n🎉 Project API testing completed!")

if __name__ == "__main__":
    print("Starting Project API tests...")
    print(f"API Base URL: {API_BASE_URL}")
    print("Make sure the FastAPI server is running!")
    print()
    
    # Quick connectivity test
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is running and accessible")
            test_project_api()
        else:
            print("❌ Server health check failed")
            sys.exit(1)
    except requests.RequestException:
        print(f"❌ Cannot connect to server at {API_BASE_URL}")
        print("Please make sure the FastAPI server is running:")
        print("  cd task-backend")
        print("  python -m uvicorn main:app --reload")
        sys.exit(1)
