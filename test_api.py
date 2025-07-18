#!/usr/bin/env python3
"""
Simple test script to verify the FastAPI backend is working
"""

import requests
import json

# API Configuration
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the root endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_login_endpoint():
    """Test the login endpoint"""
    try:
        # Test with invalid credentials first
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        response = requests.post(
            f"{BASE_URL}/users/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Login test (invalid): {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test with valid credentials (you'll need to create a user first)
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(
            f"{BASE_URL}/users/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Login test (valid): {response.status_code}")
        print(f"Response: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Login test failed: {e}")
        return False

def test_create_user():
    """Test user creation endpoint"""
    try:
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
        
        response = requests.post(
            f"{BASE_URL}/users/",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Create user: {response.status_code}")
        print(f"Response: {response.json()}")
        
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Create user test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing FastAPI Backend...")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Create User", test_create_user),
        ("Login Endpoint", test_login_endpoint),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        result = test_func()
        results.append((test_name, result))
        print(f"{test_name}: {'PASS' if result else 'FAIL'}")
    
    print("\n" + "=" * 50)
    print("Test Results:")
    for test_name, result in results:
        print(f"{test_name}: {'PASS' if result else 'FAIL'}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")

if __name__ == "__main__":
    main() 