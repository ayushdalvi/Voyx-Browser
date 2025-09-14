#!/usr/bin/env python3
"""
Test script to verify userscript manager functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from userscript_manager import UserscriptManager, Userscript

def test_userscript_manager():
    """Test basic userscript manager functionality."""
    print("Testing Userscript Manager...")
    
    # Create manager
    manager = UserscriptManager()
    print(f"[OK] Manager created, enabled: {manager.enabled}")
    
    # Test script creation
    test_code = """
console.log('Test userscript loaded!');
GM_log('GM_log function working!');
"""
    
    success = manager.create_script("test_script", test_code, {
        "name": "Test Script",
        "version": "1.0",
        "description": "Test userscript",
        "include": "*"
    })
    
    if success:
        print("[OK] Script created successfully")
    else:
        print("[FAIL] Failed to create script")
        return False
    
    # Test script loading
    manager.reload_scripts()
    test_script = None
    for script in manager.scripts:
        if "test_script" in script.name:
            test_script = script
            break
    
    if test_script:
        print(f"[OK] Script loaded: {test_script.name}")
        print(f"  - Enabled: {test_script.enabled}")
        print(f"  - Metadata: {test_script.metadata}")
    else:
        print("[FAIL] Failed to load script")
        return False
    
    # Test injection code generation
    injection_code = test_script.get_injection_code()
    if injection_code and "GM_log" in injection_code:
        print("[OK] Injection code generated with GM API")
    else:
        print("[FAIL] Injection code missing GM API")
        return False
    
    # Test URL matching
    if test_script.matches_url("https://example.com"):
        print("[OK] URL matching works")
    else:
        print("[FAIL] URL matching failed")
        return False
    
    # Clean up
    if test_script:
        manager.delete_script(test_script.name)
        print("[OK] Test script cleaned up")
    
    print("All tests passed! [SUCCESS]")
    return True

if __name__ == "__main__":
    test_userscript_manager()