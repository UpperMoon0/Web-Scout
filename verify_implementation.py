#!/usr/bin/env python3
"""
Quick verification script to check if the Phase 1 implementation is correct.
This script performs basic syntax and import checks.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def verify_imports():
    """Verify that all modules can be imported."""
    print("🔍 Verifying Phase 1 implementation...")
    
    try:
        # Test custom search engine import
        from services.custom_search_engine import CustomSearchEngine
        print("✅ CustomSearchEngine import successful")
        
        # Test search service import
        from services.search_service import SearchService, SearchResult, SearchResponse
        print("✅ SearchService import successful")
        
        # Test database initializer import
        from services.db_init import DatabaseInitializer
        print("✅ DatabaseInitializer import successful")
        
        # Test services __init__ import
        from services import CustomSearchEngine as CSE, SearchService as SS, DatabaseInitializer as DI
        print("✅ Services module imports successful")
        
        return True
    
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during import: {e}")
        return False

def verify_class_structure():
    """Verify that classes have the expected methods."""
    print("\n🔍 Verifying class structure...")
    
    try:
        from services.custom_search_engine import CustomSearchEngine
        from services.search_service import SearchService
        from services.db_init import DatabaseInitializer
        
        # Check CustomSearchEngine methods
        cse_methods = [
            'initialize', 'cleanup', 'search', 'get_statistics',
            '_init_database', '_search_web', '_search_images', '_search_news'
        ]
        
        for method in cse_methods:
            if hasattr(CustomSearchEngine, method):
                print(f"✅ CustomSearchEngine.{method} exists")
            else:
                print(f"❌ CustomSearchEngine.{method} missing")
                return False
        
        # Check SearchService integration
        ss_methods = ['search_web', 'search_domain', 'search_similar', '_search_custom']
        
        for method in ss_methods:
            if hasattr(SearchService, method):
                print(f"✅ SearchService.{method} exists")
            else:
                print(f"❌ SearchService.{method} missing")
                return False
        
        # Check DatabaseInitializer methods
        di_methods = ['initialize_database', 'add_seed_urls', 'get_database_stats']
        
        for method in di_methods:
            if hasattr(DatabaseInitializer, method):
                print(f"✅ DatabaseInitializer.{method} exists")
            else:
                print(f"❌ DatabaseInitializer.{method} missing")
                return False
        
        return True
    
    except Exception as e:
        print(f"❌ Error during class verification: {e}")
        return False

def verify_file_structure():
    """Verify that all required files exist."""
    print("\n🔍 Verifying file structure...")
    
    required_files = [
        'src/services/custom_search_engine.py',
        'src/services/search_service.py',
        'src/services/db_init.py',
        'src/services/__init__.py',
        'test_custom_search.py',
        'CUSTOM_SEARCH_ENGINE.md',
        'requirements.txt'
    ]
    
    all_exist = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def verify_requirements():
    """Verify that requirements.txt has necessary dependencies."""
    print("\n🔍 Verifying requirements...")
    
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
        
        required_deps = [
            'scikit-learn',
            'beautifulsoup4',
            'aiohttp',
            'nltk',
            'requests'
        ]
        
        all_found = True
        
        for dep in required_deps:
            if dep in content:
                print(f"✅ {dep} found in requirements.txt")
            else:
                print(f"❌ {dep} missing from requirements.txt")
                all_found = False
        
        return all_found
    
    except Exception as e:
        print(f"❌ Error reading requirements.txt: {e}")
        return False

def main():
    """Main verification function."""
    print("🚀 Web-Scout Custom Search Engine - Phase 1 Verification")
    print("=" * 60)
    
    tests = [
        ("File Structure", verify_file_structure),
        ("Module Imports", verify_imports),
        ("Class Structure", verify_class_structure),
        ("Requirements", verify_requirements),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Verification Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Phase 1 implementation verification SUCCESSFUL!")
        print("\n📋 Next steps:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Initialize database: python -m src.services.db_init --init")
        print("   3. Run tests: python test_custom_search.py")
        print("   4. Start using the custom search engine!")
        return True
    else:
        print("❌ Phase 1 implementation has issues that need to be resolved.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)