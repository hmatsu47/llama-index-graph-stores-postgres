#!/usr/bin/env python3
"""Simple script to run documentation tests."""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the Japanese documentation tests."""
    print("🔍 Running Japanese documentation tests...")
    
    # Change to the workspace directory
    workspace_dir = Path(__file__).parent
    
    try:
        # Run only the Japanese documentation tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_japanese_documentation.py", 
            "-v"
        ], cwd=workspace_dir, capture_output=True, text=True)
        
        print("📋 Test Output:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  Test Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ All Japanese documentation tests passed!")
            return True
        else:
            print("❌ Some tests failed.")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)