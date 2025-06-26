#!/usr/bin/env python3
"""
Atlas Email Integration Tests
============================

Integration tests to verify the complete Atlas_Email package functionality.
Tests the full pipeline from imports to core functionality.
"""

import sys
import os
from pathlib import Path

# Add src to path for testing
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Simple test runner without pytest
def run_test(test_func, test_name):
    """Simple test runner."""
    try:
        test_func()
        print(f"✅ {test_name}: PASSED")
        return True
    except Exception as e:
        print(f"❌ {test_name}: FAILED - {e}")
        return False


class TestPackageImports:
    """Test that all package imports work correctly."""
    
    def test_main_package_imports(self):
        """Test main package level imports."""
        from atlas_email import (
            EnsembleHybridClassifier, 
            EmailProcessor, 
            DomainValidator,
            classify_spam_type,
            NaiveBayesClassifier
        )
        assert EnsembleHybridClassifier is not None
        assert EmailProcessor is not None
        assert DomainValidator is not None
        assert classify_spam_type is not None
        assert NaiveBayesClassifier is not None
    
    def test_core_module_imports(self):
        """Test core module imports."""
        from atlas_email.core import (
            classify_spam_type,
            EmailProcessor,
            authenticate_email_headers
        )
        assert classify_spam_type is not None
        assert EmailProcessor is not None
        assert authenticate_email_headers is not None
    
    def test_ml_module_imports(self):
        """Test ML module imports."""
        from atlas_email.ml import (
            EnsembleHybridClassifier,
            NaiveBayesClassifier,
            MLFeatureExtractor,
            RandomForestClassifier
        )
        assert EnsembleHybridClassifier is not None
        assert NaiveBayesClassifier is not None
        assert MLFeatureExtractor is not None
        assert RandomForestClassifier is not None
    
    def test_filters_module_imports(self):
        """Test filters module imports."""
        from atlas_email.filters import (
            KeywordProcessor,
            SelectiveVendorFilter,
            UnifiedKeywordManager
        )
        assert KeywordProcessor is not None
        assert SelectiveVendorFilter is not None
        assert UnifiedKeywordManager is not None
    
    def test_utils_module_imports(self):
        """Test utils module imports."""
        from atlas_email.utils import (
            DomainValidator,
            detect_provider_from_sender,
            safe_json_load,
            clear_screen
        )
        assert DomainValidator is not None
        assert detect_provider_from_sender is not None
        assert safe_json_load is not None
        assert clear_screen is not None


class TestCoreComponents:
    """Test that core components can be instantiated and used."""
    
    def test_domain_validator_instantiation(self):
        """Test DomainValidator can be created and used."""
        from atlas_email import DomainValidator
        validator = DomainValidator()
        assert validator is not None
        
        # Test basic domain validation method exists
        assert hasattr(validator, 'validate_domain_before_deletion')
    
    def test_keyword_processor_instantiation(self):
        """Test KeywordProcessor can be created."""
        from atlas_email.filters import KeywordProcessor
        processor = KeywordProcessor()
        assert processor is not None
    
    def test_naive_bayes_instantiation(self):
        """Test NaiveBayesClassifier can be created."""
        from atlas_email.ml import NaiveBayesClassifier
        # Test basic instantiation (will use default database)
        classifier = NaiveBayesClassifier()
        assert classifier is not None
        assert hasattr(classifier, 'train')
        assert hasattr(classifier, 'classify')
    
    def test_ensemble_classifier_instantiation(self):
        """Test EnsembleHybridClassifier can be created."""
        from atlas_email import EnsembleHybridClassifier
        # Use in-memory database for testing
        classifier = EnsembleHybridClassifier(":memory:")
        assert classifier is not None


class TestDataPaths:
    """Test that data files can be found and loaded."""
    
    def test_data_directory_exists(self):
        """Test that data directory and files exist."""
        data_dir = project_root / "data"
        assert data_dir.exists(), "Data directory should exist"
        
        models_dir = data_dir / "models"
        assert models_dir.exists(), "Models directory should exist"
        
        keywords_file = data_dir / "keywords.txt" 
        assert keywords_file.exists(), "Keywords file should exist"
    
    def test_ml_model_files_exist(self):
        """Test that ML model files exist."""
        models_dir = project_root / "data" / "models"
        
        naive_bayes_model = models_dir / "naive_bayes_model.json"
        assert naive_bayes_model.exists(), "Naive Bayes model should exist"
        
        category_classifier = models_dir / "category_classifier.json"
        assert category_classifier.exists(), "Category classifier should exist"


class TestBasicFunctionality:
    """Test basic functionality of key components."""
    
    def test_spam_classification_function(self):
        """Test spam classification function works."""
        from atlas_email import classify_spam_type
        
        # Test with sample headers and content
        headers = {"From": "test@example.com", "Subject": "Test email"}
        sender = "test@example.com"
        subject = "Test email"
        
        result = classify_spam_type(headers, sender, subject)
        assert isinstance(result, str), "Should return a classification string"
    
    def test_provider_detection(self):
        """Test provider detection functionality."""
        from atlas_email.utils import detect_provider_from_sender
        
        # Test that function exists and returns reasonable values
        gmail_provider = detect_provider_from_sender("test@gmail.com") 
        assert gmail_provider is not None
        assert isinstance(gmail_provider, str)
        
        yahoo_provider = detect_provider_from_sender("test@yahoo.com")
        assert yahoo_provider is not None  
        assert isinstance(yahoo_provider, str)


if __name__ == "__main__":
    """Run all integration tests."""
    print("🧪 Atlas Email Integration Tests")
    print("=" * 50)
    
    # Test instances
    package_tests = TestPackageImports()
    core_tests = TestCoreComponents()
    data_tests = TestDataPaths()
    func_tests = TestBasicFunctionality()
    
    total_tests = 0
    passed_tests = 0
    
    # Run package import tests
    print("\n📦 Package Import Tests:")
    tests = [
        (package_tests.test_main_package_imports, "Main package imports"),
        (package_tests.test_core_module_imports, "Core module imports"),
        (package_tests.test_ml_module_imports, "ML module imports"),
        (package_tests.test_filters_module_imports, "Filters module imports"),
        (package_tests.test_utils_module_imports, "Utils module imports"),
    ]
    
    for test_func, test_name in tests:
        total_tests += 1
        if run_test(test_func, test_name):
            passed_tests += 1
    
    # Run core component tests
    print("\n🔧 Core Component Tests:")
    tests = [
        (core_tests.test_domain_validator_instantiation, "DomainValidator instantiation"),
        (core_tests.test_keyword_processor_instantiation, "KeywordProcessor instantiation"),
        (core_tests.test_naive_bayes_instantiation, "NaiveBayesClassifier instantiation"),
        (core_tests.test_ensemble_classifier_instantiation, "EnsembleHybridClassifier instantiation"),
    ]
    
    for test_func, test_name in tests:
        total_tests += 1
        if run_test(test_func, test_name):
            passed_tests += 1
    
    # Run data path tests
    print("\n📁 Data Path Tests:")
    tests = [
        (data_tests.test_data_directory_exists, "Data directory structure"),
        (data_tests.test_ml_model_files_exist, "ML model files"),
    ]
    
    for test_func, test_name in tests:
        total_tests += 1
        if run_test(test_func, test_name):
            passed_tests += 1
    
    # Run basic functionality tests
    print("\n⚙️ Basic Functionality Tests:")
    tests = [
        (func_tests.test_spam_classification_function, "Spam classification function"),
        (func_tests.test_provider_detection, "Provider detection"),
    ]
    
    for test_func, test_name in tests:
        total_tests += 1
        if run_test(test_func, test_name):
            passed_tests += 1
    
    # Final results
    print("\n" + "=" * 50)
    print(f"🎯 Integration Test Results: {passed_tests}/{total_tests} passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Atlas_Email is fully functional!")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Review the issues above.")
        sys.exit(1)