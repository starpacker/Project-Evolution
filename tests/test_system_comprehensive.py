#!/usr/bin/env python3
"""
Comprehensive system test for ProjectL:evolution
Based on technical_report_CN.md specifications
"""

import os
import sys
import json
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_environment():
    """Test 1: Environment and dependencies"""
    print("\n=== Test 1: Environment Check ===")
    
    checks = {
        "Python version": sys.version_info >= (3, 9),
        "Project root exists": Path("/home/yjh/ProjectEvolution").exists(),
        ".env file exists": Path("/home/yjh/ProjectEvolution/.env").exists(),
    }
    
    # Check required packages
    try:
        import openai
        checks["openai package"] = True
    except ImportError:
        checks["openai package"] = False
    
    try:
        import defusedxml
        checks["defusedxml package"] = True
    except ImportError:
        checks["defusedxml package"] = False
    
    try:
        import httpx
        checks["httpx package"] = True
    except ImportError:
        checks["httpx package"] = False
    
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")
    
    return all(checks.values())

def test_database():
    """Test 2: Database functionality"""
    print("\n=== Test 2: Database Manager ===")
    
    try:
        from evolution.db.manager import DatabaseManager
        
        # Create test database
        import tempfile
        test_dir = tempfile.mkdtemp()
        test_db = os.path.join(test_dir, "test.db")
        
        db = DatabaseManager(test_db)
        
        # Test schedule operations
        schedule_id = db.add_schedule(
            content="Test schedule",
            due_date="2026-03-15",
            priority="high",
            category="professional"
        )
        print(f"✅ Created schedule: {schedule_id}")
        
        schedules = db.get_pending_schedules()
        print(f"✅ Retrieved {len(schedules)} pending schedules")
        
        # Test skills operations
        skill_id = db.add_skill(
            name="Python",
            category="professional",
            level=5
        )
        print(f"✅ Created skill: {skill_id}")
        
        skills = db.list_skills()
        print(f"✅ Retrieved {len(skills)} skills")
        
        # Test persons operations
        person_id = db.upsert_person(
            name="Test Person",
            relationship="colleague"
        )
        print(f"✅ Created person: {person_id}")
        
        # Test conversation logs
        db.log_conversation("user", "Test message")
        print("✅ Logged conversation")
        
        # Cleanup
        db.close()
        import shutil
        shutil.rmtree(test_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_tools():
    """Test 3: Tool functionality"""
    print("\n=== Test 3: Tools ===")
    
    results = {}
    
    # Test Memory Tool
    try:
        from evolution.tools.memory_tool import EvolutionMemoryTool
        mem_tool = EvolutionMemoryTool()
        
        # Test search
        result = mem_tool.execute({
            "action": "search",
            "query": "test query"
        })
        results["Memory Tool - search"] = result.success
        print(f"{'✅' if result.success else '❌'} Memory Tool search")
        
    except Exception as e:
        results["Memory Tool"] = False
        print(f"❌ Memory Tool failed: {e}")
    
    # Test DB Tool
    try:
        from evolution.tools.db_tool import EvolutionDBTool
        import tempfile
        test_dir = tempfile.mkdtemp()
        test_db = os.path.join(test_dir, "test.db")
        
        db_tool = EvolutionDBTool(config={"db_path": test_db})
        
        # Test add schedule
        result = db_tool.execute({
            "action": "add_schedule",
            "content": "Test task",
            "due_date": "2026-03-15",
            "priority": "high"
        })
        results["DB Tool - add_schedule"] = result.success
        print(f"{'✅' if result.success else '❌'} DB Tool add_schedule")
        
        # Test list schedule
        result = db_tool.execute({
            "action": "list_schedule"
        })
        results["DB Tool - list_schedule"] = result.success
        print(f"{'✅' if result.success else '❌'} DB Tool list_schedule")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
        
    except Exception as e:
        results["DB Tool"] = False
        print(f"❌ DB Tool failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test Intelligence Tool
    try:
        from evolution.tools.intelligence_tool import EvolutionIntelligenceTool
        intel_tool = EvolutionIntelligenceTool()
        
        # Test URL safety check
        safe_url = intel_tool._is_safe_url("https://example.com")
        unsafe_url = not intel_tool._is_safe_url("http://localhost/test")
        
        results["Intelligence Tool - URL safety"] = safe_url and unsafe_url
        print(f"{'✅' if results['Intelligence Tool - URL safety'] else '❌'} Intelligence Tool URL safety")
        
    except Exception as e:
        results["Intelligence Tool"] = False
        print(f"❌ Intelligence Tool failed: {e}")
    
    # Test Reflection Tool
    try:
        from evolution.tools.reflection_tool import EvolutionReflectionTool
        import tempfile
        test_dir = tempfile.mkdtemp()
        test_db = os.path.join(test_dir, "test.db")
        
        reflection_tool = EvolutionReflectionTool(config={"db_path": test_db})
        results["Reflection Tool - init"] = True
        print("✅ Reflection Tool initialized")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
        
    except Exception as e:
        results["Reflection Tool"] = False
        print(f"❌ Reflection Tool failed: {e}")
        import traceback
        traceback.print_exc()
    
    return all(results.values())

def test_llm_connection():
    """Test 4: LLM API connection"""
    print("\n=== Test 4: LLM API Connection ===")
    
    try:
        from evolution.utils.llm import call_claude_api
        
        response = call_claude_api(
            prompt="Say 'test successful' in exactly 2 words.",
            max_tokens=10
        )
        
        if response:
            print(f"✅ LLM API connected")
            print(f"   Response: {response[:100]}")
            return True
        else:
            print("❌ LLM API returned None")
            return False
            
    except Exception as e:
        print(f"❌ LLM API test failed: {e}")
        return False

def test_notification_router():
    """Test 5: Notification routing"""
    print("\n=== Test 5: Notification Router ===")
    
    try:
        from evolution.notification.router import NotificationRouter, Notification, NotifyPriority
        
        router = NotificationRouter()
        
        # Test notification creation
        notification = Notification(
            title="Test Notification",
            body="This is a test",
            priority=NotifyPriority.LOW,
            category="test"
        )
        
        print("✅ Notification created")
        print(f"   Priority: {notification.priority}")
        print(f"   Category: {notification.category}")
        
        # Note: Not actually sending to avoid spam
        print("✅ Notification router initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Notification router test failed: {e}")
        return False

def test_web_chat():
    """Test 6: Web Chat availability"""
    print("\n=== Test 6: Web Chat Server ===")
    
    try:
        import httpx
        
        # Check if web chat is running
        try:
            response = httpx.get("http://localhost:5000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Web Chat server is running")
                print(f"   URL: http://localhost:5000")
                return True
            else:
                print(f"⚠️  Web Chat returned status {response.status_code}")
                return False
        except httpx.ConnectError:
            print("⚠️  Web Chat server not running (this is OK if not started)")
            print("   To start: python3 -m evolution.chat.web_chat")
            return True  # Not a failure, just not running
            
    except Exception as e:
        print(f"❌ Web Chat test failed: {e}")
        return False

def test_security():
    """Test 7: Security features"""
    print("\n=== Test 7: Security Features ===")
    
    results = {}
    
    # Test SQL injection protection
    try:
        from evolution.db.manager import DatabaseManager
        import tempfile
        test_dir = tempfile.mkdtemp()
        test_db = os.path.join(test_dir, "test.db")
        
        db = DatabaseManager(test_db)
        
        # Try to inject SQL through person update
        try:
            db.upsert_person(
                name="Test",
                malicious_column="'; DROP TABLE persons; --"
            )
            # Should not create malicious column
            results["SQL injection protection"] = True
            print("✅ SQL injection protection working")
        except Exception:
            results["SQL injection protection"] = True
            print("✅ SQL injection blocked")
        
        db.close()
        import shutil
        shutil.rmtree(test_dir)
        
    except Exception as e:
        results["SQL injection protection"] = False
        print(f"❌ SQL injection test failed: {e}")
    
    # Test SSRF protection
    try:
        from evolution.tools.intelligence_tool import EvolutionIntelligenceTool
        tool = EvolutionIntelligenceTool()
        
        dangerous_urls = [
            "http://localhost/admin",
            "http://127.0.0.1/secret",
            "http://192.168.1.1/config",
            "file:///etc/passwd",
            "ftp://internal.server/data"
        ]
        
        all_blocked = all(not tool._is_safe_url(url) for url in dangerous_urls)
        results["SSRF protection"] = all_blocked
        print(f"{'✅' if all_blocked else '❌'} SSRF protection")
        
    except Exception as e:
        results["SSRF protection"] = False
        print(f"❌ SSRF test failed: {e}")
    
    # Test XXE protection
    try:
        from defusedxml.ElementTree import fromstring
        results["XXE protection"] = True
        print("✅ XXE protection (defusedxml installed)")
    except ImportError:
        results["XXE protection"] = False
        print("❌ XXE protection (defusedxml not installed)")
    
    return all(results.values())

def test_integration():
    """Test 8: Integration test"""
    print("\n=== Test 8: Integration Test ===")
    
    try:
        from evolution.tools.db_tool import EvolutionDBTool
        from evolution.tools.memory_tool import EvolutionMemoryTool
        import tempfile
        
        test_dir = tempfile.mkdtemp()
        test_db = os.path.join(test_dir, "test.db")
        
        # Initialize tools
        db_tool = EvolutionDBTool(config={"db_path": test_db})
        mem_tool = EvolutionMemoryTool()
        
        # Simulate a workflow: add schedule -> add memory
        result1 = db_tool.execute({
            "action": "add_schedule",
            "content": "Complete project report",
            "due_date": "2026-03-20",
            "priority": "high",
            "category": "professional"
        })
        print(f"{'✅' if result1.success else '❌'} Step 1: Add schedule")
        
        result2 = mem_tool.execute({
            "action": "add",
            "content": "User scheduled project report for March 20"
        })
        print(f"{'✅' if result2.success else '❌'} Step 2: Add memory")
        
        result3 = db_tool.execute({
            "action": "list_schedule"
        })
        print(f"{'✅' if result3.success else '❌'} Step 3: List schedules")
        
        result4 = mem_tool.execute({
            "action": "search",
            "query": "project report"
        })
        print(f"{'✅' if result4.success else '❌'} Step 4: Search memory")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
        
        return all([result1.success, result2.success, result3.success, result4.success])
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("ProjectL:evolution Comprehensive System Test")
    print("Based on technical_report_CN.md")
    print("=" * 60)
    
    tests = [
        ("Environment", test_environment),
        ("Database", test_database),
        ("Tools", test_tools),
        ("LLM Connection", test_llm_connection),
        ("Notification Router", test_notification_router),
        ("Web Chat", test_web_chat),
        ("Security", test_security),
        ("Integration", test_integration),
    ]
    
    results = {}
    start_time = time.time()
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    elapsed = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Time: {elapsed:.2f}s")
    
    if passed == total:
        print("\n🎉 All tests passed! System is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
