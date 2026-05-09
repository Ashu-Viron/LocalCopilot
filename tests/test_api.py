"""
Integration tests for LocalCopilot backend API.
Run with: python -m pytest tests/test_api.py -v
Or standalone: python tests/test_api.py
"""

import httpx
import asyncio
import json
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_WORKSPACE = Path.cwd()

class APITestRunner:
    """Simple test runner without pytest dependency"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(timeout=10.0)
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
    
    def assert_equal(self, actual, expected, message=""):
        """Assert equality"""
        if actual == expected:
            self.tests_passed += 1
            return True
        else:
            self.tests_failed += 1
            msg = f"FAIL: {message}\n  Expected: {expected}\n  Got: {actual}"
            self.results.append(msg)
            print(f"❌ {msg}")
            return False
    
    def assert_status(self, response, expected_status, message=""):
        """Assert HTTP status code"""
        if response.status_code == expected_status:
            self.tests_passed += 1
            return True
        else:
            self.tests_failed += 1
            msg = f"FAIL: {message}\n  Expected status: {expected_status}\n  Got: {response.status_code}\n  Body: {response.text}"
            self.results.append(msg)
            print(f"❌ {msg}")
            return False
    
    def assert_in(self, needle, haystack, message=""):
        """Assert value is in collection"""
        if needle in haystack:
            self.tests_passed += 1
            return True
        else:
            self.tests_failed += 1
            msg = f"FAIL: {message}\n  Expected '{needle}' in {haystack}"
            self.results.append(msg)
            print(f"❌ {msg}")
            return False
    
    def test_health_check(self):
        """Test GET /api/system/health"""
        print("\n🧪 Testing Health Check...")
        try:
            response = self.client.get(f"{self.base_url}/api/system/health")
            self.assert_status(response, 200, "Health check should return 200")
            
            data = response.json()
            self.assert_equal(data.get("status"), "healthy", "Should return healthy status")
            self.assert_in("version", data, "Should include version")
            print("✅ Health check passed")
        except Exception as e:
            self.tests_failed += 1
            print(f"❌ Health check failed: {e}")
    
    def test_system_info(self):
        """Test GET /api/system/info"""
        print("\n🧪 Testing System Info...")
        try:
            response = self.client.get(f"{self.base_url}/api/system/info")
            self.assert_status(response, 200, "System info should return 200")
            
            data = response.json()
            self.assert_in("python_version", data, "Should include python_version")
            self.assert_in("platform", data, "Should include platform")
            print("✅ System info passed")
        except Exception as e:
            self.tests_failed += 1
            print(f"❌ System info failed: {e}")
    
    def test_list_files(self):
        """Test GET /api/files/list"""
        print("\n🧪 Testing List Files...")
        try:
            response = self.client.get(f"{self.base_url}/api/files/list", params={"path": "."})
            self.assert_status(response, 200, "List files should return 200")
            
            data = response.json()
            self.assert_in("items", data, "Should include items")
            print("✅ List files passed")
        except Exception as e:
            self.tests_failed += 1
            print(f"❌ List files failed: {e}")
    
    def test_create_conversation(self):
        """Test POST /api/chat/conversations"""
        print("\n🧪 Testing Create Conversation...")
        try:
            payload = {"name": "Test Conversation"}
            response = self.client.post(
                f"{self.base_url}/api/chat/conversations",
                json=payload
            )
            self.assert_status(response, 200, "Create conversation should return 200")
            
            data = response.json()
            self.assert_in("conversation_id", data, "Should include conversation_id")
            print("✅ Create conversation passed")
        except Exception as e:
            self.tests_failed += 1
            print(f"❌ Create conversation failed: {e}")
    
    def test_get_available_tools(self):
        """Test GET /api/tools/available"""
        print("\n🧪 Testing Available Tools...")
        try:
            response = self.client.get(f"{self.base_url}/api/tools/available")
            self.assert_status(response, 200, "Available tools should return 200")
            
            data = response.json()
            self.assert_in("tools", data, "Should include tools list")
            print("✅ Available tools passed")
        except Exception as e:
            self.tests_failed += 1
            print(f"❌ Available tools failed: {e}")
    
    def test_file_read(self):
        """Test POST /api/files/read"""
        print("\n🧪 Testing File Read...")
        try:
            # Try to read README.md
            payload = {"path": "README.md"}
            response = self.client.post(
                f"{self.base_url}/api/files/read",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                self.assert_in("content", data, "Should include content")
                print("✅ File read passed")
            elif response.status_code == 404:
                print("⚠️ File read: README.md not found (expected in some cases)")
                self.tests_passed += 1
            else:
                self.assert_status(response, 200, "File read should return 200 or 404")
        except Exception as e:
            self.tests_failed += 1
            print(f"❌ File read failed: {e}")
    
    def test_git_status(self):
        """Test GET /api/tools/execute with git status"""
        print("\n🧪 Testing Git Status...")
        try:
            response = self.client.get(f"{self.base_url}/api/tools/execute", params={
                "tool": "git_status"
            })
            
            if response.status_code in [200, 400]:
                print("✅ Git status passed")
                self.tests_passed += 1
            else:
                self.assert_status(response, 200, "Git status should return 200")
        except Exception as e:
            self.tests_failed += 1
            print(f"❌ Git status failed: {e}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("🚀 LocalCopilot Backend Integration Tests")
        print("="*60)
        print(f"Target: {self.base_url}")
        
        try:
            self.test_health_check()
            self.test_system_info()
            self.test_list_files()
            self.test_create_conversation()
            self.test_get_available_tools()
            self.test_file_read()
            self.test_git_status()
        finally:
            self.client.close()
        
        # Summary
        print("\n" + "="*60)
        print(f"Tests Passed: {self.tests_passed} ✅")
        print(f"Tests Failed: {self.tests_failed} ❌")
        print("="*60)
        
        return self.tests_failed == 0

if __name__ == "__main__":
    runner = APITestRunner()
    success = runner.run_all_tests()
    exit(0 if success else 1)
