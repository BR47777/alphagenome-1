#!/usr/bin/env python3
"""
Comprehensive test suite for AlphaGenome UI validation components.
"""

import pytest
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui_components import InputValidator, APIValidator


class TestInputValidator:
    """Test cases for InputValidator class."""
    
    def test_validate_api_key_valid(self):
        """Test valid API key validation."""
        valid_key = "AIzaSyCD4-gO0ZpTQhV2twqzIeASAUE7ks8986M"
        is_valid, message = InputValidator.validate_api_key(valid_key)
        assert is_valid
        assert "valid" in message.lower()
    
    def test_validate_api_key_invalid_format(self):
        """Test invalid API key formats."""
        invalid_keys = [
            "",  # Empty
            "invalid_key",  # Wrong format
            "AIza123",  # Too short
            "AIza" + "x" * 50,  # Too long
            "AIza@#$%^&*()",  # Invalid characters
        ]
        
        for key in invalid_keys:
            is_valid, message = InputValidator.validate_api_key(key)
            assert not is_valid
            assert len(message) > 0
    
    def test_validate_dna_sequence_valid(self):
        """Test valid DNA sequence validation."""
        valid_sequences = [
            "ATCGATCGATCG",  # Basic sequence
            "ATCGATCGATCGATCGATCGATCGATCGATCGATCG",  # Longer sequence
            "ATCGNNNATCG",  # With N bases
            "atcgatcgatcg",  # Lowercase (should be converted)
            "ATCG ATCG ATCG",  # With spaces (should be removed)
        ]
        
        for seq in valid_sequences:
            is_valid, message = InputValidator.validate_dna_sequence(seq)
            assert is_valid, f"Sequence '{seq}' should be valid: {message}"
    
    def test_validate_dna_sequence_invalid(self):
        """Test invalid DNA sequence validation."""
        invalid_sequences = [
            "",  # Empty
            "ATCG",  # Too short
            "ATCGATCXGATCG",  # Invalid character
            "A" * 1000001,  # Too long
            "N" * 100,  # Too many Ns (>50%)
        ]
        
        for seq in invalid_sequences:
            is_valid, message = InputValidator.validate_dna_sequence(seq)
            assert not is_valid, f"Sequence '{seq[:20]}...' should be invalid"
    
    def test_validate_interval_valid(self):
        """Test valid genomic interval validation."""
        valid_intervals = [
            "chr22:1000-2000",
            "chr1:100000-200000",
            "chrX:1000-5000",
            "chrY:1000-5000",
            "chrMT:1000-5000",
            "1:1000-2000",  # Without chr prefix
        ]
        
        for interval in valid_intervals:
            is_valid, message, interval_obj = InputValidator.validate_interval(interval)
            assert is_valid, f"Interval '{interval}' should be valid: {message}"
            assert interval_obj is not None
    
    def test_validate_interval_invalid(self):
        """Test invalid genomic interval validation."""
        invalid_intervals = [
            "",  # Empty
            "chr22:1000",  # Missing end
            "chr22:2000-1000",  # End before start
            "chr22:1000-1050",  # Too small
            "chr22:1000-2000000",  # Too large
            "chr99:1000-2000",  # Invalid chromosome
            "invalid:1000-2000",  # Invalid format
        ]
        
        for interval in invalid_intervals:
            is_valid, message, interval_obj = InputValidator.validate_interval(interval)
            assert not is_valid, f"Interval '{interval}' should be invalid"
    
    def test_validate_variant_valid(self):
        """Test valid variant validation."""
        valid_variants = [
            "chr22:1000:A>T",  # SNV
            "chr1:100000:ATG>C",  # Deletion
            "chr22:1000:A>TTG",  # Insertion
            "chrX:1000:G>C",  # X chromosome
            "1:1000:A>T",  # Without chr prefix
        ]
        
        for variant in valid_variants:
            is_valid, message, variant_obj = InputValidator.validate_variant(variant)
            assert is_valid, f"Variant '{variant}' should be valid: {message}"
            assert variant_obj is not None
    
    def test_validate_variant_invalid(self):
        """Test invalid variant validation."""
        invalid_variants = [
            "",  # Empty
            "chr22:1000:A",  # Missing alternate
            "chr22:1000:A>X",  # Invalid character
            "chr22:0:A>T",  # Invalid position
            "chr99:1000:A>T",  # Invalid chromosome
            "chr22:1000:A>" + "T" * 101,  # Allele too long
        ]
        
        for variant in invalid_variants:
            is_valid, message, variant_obj = InputValidator.validate_variant(variant)
            assert not is_valid, f"Variant '{variant}' should be invalid"
    
    def test_validate_ontology_terms_valid(self):
        """Test valid ontology terms validation."""
        valid_terms = [
            ["UBERON:0001157"],
            ["CL:0000001", "UBERON:0001157"],
            ["GO:0008150"],
        ]
        
        for terms in valid_terms:
            is_valid, message, validated_terms = InputValidator.validate_ontology_terms(terms)
            assert is_valid, f"Terms '{terms}' should be valid: {message}"
            assert len(validated_terms) == len(terms)
    
    def test_validate_ontology_terms_invalid(self):
        """Test invalid ontology terms validation."""
        invalid_terms = [
            [],  # Empty list
            ["invalid_term"],  # Invalid format
            ["UBERON:123"],  # Too short ID
            ["INVALID:0001157"],  # Invalid ontology
        ]
        
        for terms in invalid_terms:
            is_valid, message, validated_terms = InputValidator.validate_ontology_terms(terms)
            assert not is_valid, f"Terms '{terms}' should be invalid"
    
    def test_validate_output_types_valid(self):
        """Test valid output types validation."""
        valid_types = [
            ["RNA_SEQ"],
            ["ATAC_SEQ", "RNA_SEQ"],
            ["CHIP_SEQ", "H3K27AC"],
        ]
        
        for types in valid_types:
            is_valid, message, validated_types = InputValidator.validate_output_types(types)
            assert is_valid, f"Types '{types}' should be valid: {message}"
            assert len(validated_types) == len(types)
    
    def test_validate_output_types_invalid(self):
        """Test invalid output types validation."""
        invalid_types = [
            [],  # Empty list
            ["INVALID_TYPE"],  # Invalid type
            ["RNA_SEQ", "INVALID_TYPE"],  # Mixed valid/invalid
        ]
        
        for types in invalid_types:
            is_valid, message, validated_types = InputValidator.validate_output_types(types)
            assert not is_valid, f"Types '{types}' should be invalid"


class TestAPIValidator:
    """Test cases for APIValidator class."""
    
    def test_validate_api_response_valid(self):
        """Test valid API response validation."""
        # Mock valid response
        class MockResponse:
            def __init__(self):
                self.__dataclass_fields__ = {'field1': None, 'field2': None}
        
        response = MockResponse()
        is_valid, message = APIValidator.validate_api_response(response, 'metadata')
        assert is_valid
    
    def test_validate_api_response_invalid(self):
        """Test invalid API response validation."""
        # Test None response
        is_valid, message = APIValidator.validate_api_response(None)
        assert not is_valid
        
        # Test response with error
        class MockErrorResponse:
            def __init__(self):
                self.error = "Test error"
        
        response = MockErrorResponse()
        is_valid, message = APIValidator.validate_api_response(response)
        assert not is_valid
        assert "error" in message.lower()
    
    def test_handle_api_error(self):
        """Test API error handling."""
        test_errors = [
            Exception("PERMISSION_DENIED"),
            Exception("QUOTA_EXCEEDED"),
            Exception("INVALID_ARGUMENT"),
            Exception("UNAVAILABLE"),
            Exception("DEADLINE_EXCEEDED"),
            Exception("Generic error"),
        ]
        
        for error in test_errors:
            error_msg = APIValidator.handle_api_error(error)
            assert len(error_msg) > 0
            assert "❌" in error_msg


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
