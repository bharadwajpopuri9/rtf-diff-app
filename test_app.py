#!/usr/bin/env python3
"""
Test script for RTF Diff App
Run this to verify the app works before deploying to Render
"""

import os
import sys
import tempfile
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work"""
    try:
        from app import app
        from utils.rtf_processor import RTFProcessor
        from utils.diff_generator import DiffGenerator
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_rtf_processing():
    """Test RTF processing functionality"""
    try:
        from utils.rtf_processor import RTFProcessor
        from utils.diff_generator import DiffGenerator
        
        processor = RTFProcessor()
        diff_gen = DiffGenerator()
        
        # Test basic diff functionality
        content1 = "This is the original text."
        content2 = "This is the modified text."
        
        options = {
            'ignore_boilerplate': True,
            'normalize_whitespace': True,
            'ignore_case': False,
            'ignore_punctuation': False,
            'diff_granularity': 'word'
        }
        
        result = diff_gen.compare_texts(content1, content2, 'source.rtf', 'comp.rtf', options)
        
        if result['has_differences'] and result['change_count'] > 0:
            print("✅ Diff generation works correctly")
            return True
        else:
            print("❌ Diff generation failed")
            return False
            
    except Exception as e:
        print(f"❌ RTF processing error: {e}")
        return False

def test_file_validation():
    """Test file validation functionality"""
    try:
        from app import validate_rtf_file
        
        # Create a test RTF file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rtf', delete=False) as f:
            f.write('Test RTF content')
            test_file = Path(f.name)
        
        is_valid, error = validate_rtf_file(test_file)
        test_file.unlink()  # Clean up
        
        print(f"✅ File validation works: {is_valid}")
        return True
        
    except Exception as e:
        print(f"❌ File validation error: {e}")
        return False

def test_flask_app():
    """Test Flask app initialization"""
    try:
        from app import app
        
        # Test app configuration
        app.config['TESTING'] = True
        client = app.test_client()
        
        # Test home page
        response = client.get('/')
        if response.status_code == 200:
            print("✅ Flask app works correctly")
            return True
        else:
            print(f"❌ Flask app returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Flask app error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing RTF Diff App for Render deployment...\n")
    
    tests = [
        ("Imports", test_imports),
        ("RTF Processing", test_rtf_processing),
        ("File Validation", test_file_validation),
        ("Flask App", test_flask_app)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Testing {test_name}...")
        result = test_func()
        results.append(result)
        print()
    
    if all(results):
        print("🎉 All tests passed! App is ready for Render deployment.")
        return 0
    else:
        print("❌ Some tests failed. Please fix issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
