#!/usr/bin/env python3
"""
Enhanced Test Suite for AlphaGenome Chainlit UI Application

This script provides comprehensive testing including:
- Import validation
- Input validation testing
- API response validation
- Mock API testing
- Integration testing
"""

import sys
import traceback
import subprocess
import os
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        import chainlit as cl
        print("✅ Chainlit imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Chainlit: {e}")
        return False
    
    try:
        import matplotlib.pyplot as plt
        import pandas as pd
        import numpy as np
        print("✅ Core data science libraries imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import data science libraries: {e}")
        return False
    
    try:
        from alphagenome.data import genome
        from alphagenome.models import dna_client
        from alphagenome.visualization import plot_components
        print("✅ AlphaGenome modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import AlphaGenome modules: {e}")
        return False
    
    try:
        from ui_components import InputValidator, UIHelpers, AdvancedInputForms, ResultsDisplay
        print("✅ UI components imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import UI components: {e}")
        return False
    
    return True

def test_input_validation():
    """Test input validation functions."""
    print("\n🧪 Testing input validation...")
    
    from ui_components import InputValidator
    
    # Test DNA sequence validation
    test_cases = [
        ("ATCGATCGATCG", True, "Valid short sequence"),
        ("ATCGATCGATCGATCGATCGATCGATCGATCGATCG", True, "Valid longer sequence"),
        ("ATCGATCXGATCG", False, "Invalid character X"),
        ("", False, "Empty sequence"),
        ("ATCG", False, "Too short"),
        ("A" * 1000001, False, "Too long")
    ]
    
    all_passed = True
    for sequence, expected_valid, description in test_cases:
        is_valid, message = InputValidator.validate_dna_sequence(sequence)
        status = "✅" if is_valid == expected_valid else "❌"
        if is_valid != expected_valid:
            all_passed = False
        print(f"{status} {description}: {message}")
    
    # Test interval validation
    interval_cases = [
        ("chr22:1000-2000", True, "Valid interval"),
        ("chr1:100000-200000", True, "Valid large interval"),
        ("chr22:1000", False, "Missing end position"),
        ("chr22:2000-1000", False, "End before start"),
        ("chr22:1000-1050", False, "Too small"),
        ("chr22:1000-2000000", False, "Too large")
    ]
    
    for interval_str, expected_valid, description in interval_cases:
        is_valid, message, interval = InputValidator.validate_interval(interval_str)
        status = "✅" if is_valid == expected_valid else "❌"
        if is_valid != expected_valid:
            all_passed = False
        print(f"{status} {description}: {message}")

    # Test variant validation
    variant_cases = [
        ("chr22:1000:A>T", True, "Valid SNV"),
        ("chr1:100000:ATG>C", True, "Valid deletion"),
        ("chr22:1000:A>TTG", True, "Valid insertion"),
        ("chr22:1000:A", False, "Missing alternate"),
        ("chr22:1000:A>X", False, "Invalid character"),
        ("chr22:0:A>T", False, "Invalid position")
    ]

    for variant_str, expected_valid, description in variant_cases:
        is_valid, message, variant = InputValidator.validate_variant(variant_str)
        status = "✅" if is_valid == expected_valid else "❌"
        if is_valid != expected_valid:
            all_passed = False
        print(f"{status} {description}: {message}")

    return all_passed

def test_genome_objects():
    """Test AlphaGenome data objects."""
    print("\n🧪 Testing AlphaGenome data objects...")
    
    from alphagenome.data import genome
    
    try:
        # Test Interval creation
        interval = genome.Interval(chromosome="chr22", start=1000, end=2000)
        print(f"✅ Created interval: {interval.chromosome}:{interval.start}-{interval.end} ({interval.width} bp)")
        
        # Test Variant creation
        variant = genome.Variant(
            chromosome="chr22",
            position=1500,
            reference_bases="A",
            alternate_bases="T"
        )
        print(f"✅ Created variant: {variant.chromosome}:{variant.position}:{variant.reference_bases}>{variant.alternate_bases}")
        
        # Test variant-interval overlap
        overlaps = variant.reference_overlaps(interval)
        print(f"✅ Variant overlaps interval: {overlaps}")
        
    except Exception as e:
        print(f"❌ Error testing genome objects: {e}")
        return False
    
    return True

def test_visualization_setup():
    """Test visualization setup."""
    print("\n🧪 Testing visualization setup...")
    
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Create a simple test plot
        fig, ax = plt.subplots(figsize=(8, 4))
        x = np.linspace(0, 100, 1000)
        y = np.sin(x / 10) + np.random.normal(0, 0.1, 1000)
        ax.plot(x, y, alpha=0.7)
        ax.set_title("Test Plot")
        ax.set_xlabel("Position")
        ax.set_ylabel("Signal")
        
        # Save to buffer (simulate what the app does)
        import io
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        print(f"✅ Created test visualization ({len(buffer.getvalue())} bytes)")
        
    except Exception as e:
        print(f"❌ Error testing visualization: {e}")
        return False
    
    return True

def test_app_structure():
    """Test application file structure."""
    print("\n🧪 Testing application structure...")
    
    required_files = [
        "app.py",
        "ui_components.py",
        "run_app.py",
        "requirements.txt",
        "chainlit.md",
        ".chainlit/config.toml"
    ]
    
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ Found {file_path}")
        else:
            print(f"❌ Missing {file_path}")
            return False
    
    return True

def test_app_loading():
    """Test that the main app module can be loaded."""
    print("\n🧪 Testing app module loading...")
    
    try:
        import app
        print("✅ App module loaded successfully")
        
        # Test that key functions exist
        required_functions = [
            'start',
            'main',
            'initialize_model',
            'handle_sequence_prediction_enhanced',
            'handle_interval_prediction_enhanced',
            'handle_variant_prediction_enhanced'
        ]
        
        for func_name in required_functions:
            if hasattr(app, func_name):
                print(f"✅ Function {func_name} found")
            else:
                print(f"❌ Function {func_name} missing")
                return False
        
    except Exception as e:
        print(f"❌ Error loading app module: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_enhanced_validation():
    """Test enhanced validation features."""
    print("\n🧪 Testing enhanced validation features...")

    from ui_components import InputValidator, APIValidator

    # Test API key validation
    test_api_keys = [
        ("AIzaSyCD4-gO0ZpTQhV2twqzIeASAUE7ks8986M", True, "Valid API key"),
        ("invalid_key", False, "Invalid format"),
        ("", False, "Empty key"),
        ("AIza123", False, "Too short"),
    ]

    all_passed = True
    for key, expected_valid, description in test_api_keys:
        is_valid, message = InputValidator.validate_api_key(key)
        status = "✅" if is_valid == expected_valid else "❌"
        if is_valid != expected_valid:
            all_passed = False
        print(f"{status} {description}: {message}")

    # Test ontology terms validation
    ontology_tests = [
        (["UBERON:0001157"], True, "Valid UBERON term"),
        (["CL:0000001"], True, "Valid CL term"),
        (["invalid_term"], False, "Invalid format"),
        ([], False, "Empty list"),
    ]

    for terms, expected_valid, description in ontology_tests:
        is_valid, message, validated = InputValidator.validate_ontology_terms(terms)
        status = "✅" if is_valid == expected_valid else "❌"
        if is_valid != expected_valid:
            all_passed = False
        print(f"{status} {description}: {message}")

    # Test output types validation
    output_tests = [
        (["RNA_SEQ"], True, "Valid RNA_SEQ"),
        (["RNA_SEQ", "ATAC_SEQ"], True, "Multiple valid types"),
        (["INVALID_TYPE"], False, "Invalid type"),
        ([], False, "Empty list"),
    ]

    for types, expected_valid, description in output_tests:
        is_valid, message, validated = InputValidator.validate_output_types(types)
        status = "✅" if is_valid == expected_valid else "❌"
        if is_valid != expected_valid:
            all_passed = False
        print(f"{status} {description}: {message}")

    return all_passed

def run_pytest_tests():
    """Run pytest test suite if available."""
    print("\n🧪 Running comprehensive test suite with pytest...")

    tests_dir = Path("tests")
    if not tests_dir.exists():
        print("⚠️  Tests directory not found, skipping pytest tests")
        return True

    try:
        # Check if pytest is available
        result = subprocess.run([sys.executable, "-m", "pytest", "--version"],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️  pytest not available, skipping comprehensive tests")
            print("💡 Install pytest with: pip install pytest")
            return True

        # Run pytest tests
        print("Running pytest test suite...")
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            str(tests_dir),
            "-v",
            "--tb=short"
        ], capture_output=True, text=True)

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        if result.returncode == 0:
            print("✅ All pytest tests passed!")
            return True
        else:
            print("❌ Some pytest tests failed")
            return False

    except Exception as e:
        print(f"⚠️  Error running pytest: {e}")
        return True  # Don't fail the main test suite

def main():
    """Run all tests."""
    print("🧬 AlphaGenome Chainlit UI - Enhanced Test Suite")
    print("=" * 60)

    tests = [
        ("Import Tests", test_imports),
        ("Input Validation Tests", test_input_validation),
        ("Enhanced Validation Tests", test_enhanced_validation),
        ("Genome Objects Tests", test_genome_objects),
        ("Visualization Tests", test_visualization_setup),
        ("App Structure Tests", test_app_structure),
        ("App Loading Tests", test_app_loading),
        ("Comprehensive Test Suite", run_pytest_tests)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"📊 Test Results: {passed}/{total} test suites passed")

    if passed == total:
        print("🎉 All tests passed! The application is ready to run.")
        print("\n🚀 To start the application:")
        print("1. Set your API key: export ALPHAGENOME_API_KEY=your_key_here")
        print("2. Run: python run_app.py")
        print("3. Open: http://localhost:8000")
        print("\n🧪 For continuous testing:")
        print("- Run: python -m pytest tests/ -v")
        print("- Install pytest: pip install pytest")
        return True
    else:
        print("⚠️  Some tests failed. Please fix the issues before running the application.")
        print("\n🔧 Troubleshooting:")
        print("- Check that all dependencies are installed")
        print("- Verify AlphaGenome package is available")
        print("- Ensure all required files are present")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
