#!/usr/bin/env python3
"""
Integration tests for AlphaGenome UI application.
"""

import pytest
import sys
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import app
from ui_components import InputValidator, APIValidator
from alphagenome.data import genome


class TestAppIntegration:
    """Integration tests for the main application."""
    
    @pytest.fixture
    def mock_api_key(self):
        """Provide a mock API key for testing."""
        return "AIzaSyCD4-gO0ZpTQhV2twqzIeASAUE7ks8986M"
    
    @pytest.fixture
    def mock_dna_client(self):
        """Mock DNA client for testing."""
        mock_client = Mock()
        mock_metadata = Mock()
        mock_metadata.__dataclass_fields__ = {
            'rna_seq': None,
            'atac_seq': None,
            'chip_seq': None
        }
        mock_client.output_metadata.return_value = mock_metadata
        return mock_client
    
    @pytest.fixture
    def mock_prediction_response(self):
        """Mock prediction response for testing."""
        mock_response = Mock()
        mock_response.reference = Mock()
        mock_response.alternate = Mock()
        mock_response.reference.rna_seq = Mock()
        mock_response.alternate.rna_seq = Mock()
        return mock_response
    
    def test_input_validation_integration(self):
        """Test that input validation works correctly with real genomic objects."""
        # Test interval validation creates valid genome.Interval
        is_valid, message, interval = InputValidator.validate_interval("chr22:1000-2000")
        assert is_valid
        assert isinstance(interval, genome.Interval)
        assert interval.chromosome == "chr22"
        assert interval.start == 1000
        assert interval.end == 2000
        assert interval.width == 1000
        
        # Test variant validation creates valid genome.Variant
        is_valid, message, variant = InputValidator.validate_variant("chr22:1500:A>T")
        assert is_valid
        assert isinstance(variant, genome.Variant)
        assert variant.chromosome == "chr22"
        assert variant.position == 1500
        assert variant.reference_bases == "A"
        assert variant.alternate_bases == "T"
        
        # Test variant-interval overlap
        overlaps = variant.reference_overlaps(interval)
        assert overlaps  # Variant at position 1500 should overlap interval 1000-2000
    
    @patch('app.dna_client')
    @pytest.mark.asyncio
    async def test_initialize_model_success(self, mock_dna_client_module, mock_api_key, mock_dna_client):
        """Test successful model initialization."""
        # Setup mock
        mock_dna_client_module.create.return_value = mock_dna_client
        
        # Test initialization
        result = await app.initialize_model(mock_api_key)
        
        # Verify calls
        mock_dna_client_module.create.assert_called_once_with(mock_api_key)
        mock_dna_client.output_metadata.assert_called_once()
        
        # Check global state
        assert app.dna_model == mock_dna_client
        assert app.current_session_data['model'] == mock_dna_client
        assert app.current_session_data['api_key'] == mock_api_key
    
    @patch('app.dna_client')
    @pytest.mark.asyncio
    async def test_initialize_model_invalid_key(self, mock_dna_client_module):
        """Test model initialization with invalid API key."""
        invalid_key = "invalid_key"
        
        result = await app.initialize_model(invalid_key)
        
        # Should fail validation before calling API
        mock_dna_client_module.create.assert_not_called()
        assert result is False
    
    @patch('app.dna_client')
    @pytest.mark.asyncio
    async def test_initialize_model_api_error(self, mock_dna_client_module, mock_api_key):
        """Test model initialization with API error."""
        # Setup mock to raise exception
        mock_dna_client_module.create.side_effect = Exception("PERMISSION_DENIED")
        
        result = await app.initialize_model(mock_api_key)
        
        # Should handle error gracefully
        assert result is False
    
    def test_genomic_data_validation_edge_cases(self):
        """Test edge cases in genomic data validation."""
        # Test chromosome format normalization
        test_cases = [
            ("1:1000-2000", "chr1"),
            ("chr1:1000-2000", "chr1"),
            ("X:1000-2000", "chrX"),
            ("chrX:1000-2000", "chrX"),
            ("MT:1000-2000", "chrMT"),
            ("chrMT:1000-2000", "chrMT"),
        ]
        
        for input_str, expected_chr in test_cases:
            is_valid, message, interval = InputValidator.validate_interval(input_str)
            assert is_valid, f"Failed for {input_str}: {message}"
            assert interval.chromosome == expected_chr
    
    def test_sequence_validation_edge_cases(self):
        """Test edge cases in DNA sequence validation."""
        # Test sequence with various formats
        test_sequences = [
            ("ATCG\nATCG\nATCG", True),  # With newlines
            ("ATCG ATCG ATCG", True),   # With spaces
            ("atcgatcgatcg", True),     # Lowercase
            ("ATCG\tATCG\tATCG", True), # With tabs
        ]
        
        for seq, should_be_valid in test_sequences:
            is_valid, message = InputValidator.validate_dna_sequence(seq)
            assert is_valid == should_be_valid, f"Sequence '{seq}' validation failed: {message}"
    
    def test_variant_type_detection(self):
        """Test variant type detection in validation."""
        variant_types = [
            ("chr1:1000:A>T", "SNV"),
            ("chr1:1000:ATG>A", "deletion"),
            ("chr1:1000:A>ATG", "insertion"),
            ("chr1:1000:ATG>GCA", "complex"),
        ]
        
        for variant_str, expected_type in variant_types:
            is_valid, message, variant = InputValidator.validate_variant(variant_str)
            assert is_valid, f"Variant {variant_str} should be valid"
            assert expected_type.lower() in message.lower(), f"Expected {expected_type} in message: {message}"
    
    def test_api_error_handling_comprehensive(self):
        """Test comprehensive API error handling."""
        error_scenarios = [
            ("PERMISSION_DENIED: Invalid API key", "Authentication Error"),
            ("QUOTA_EXCEEDED: Daily limit reached", "Quota Exceeded"),
            ("INVALID_ARGUMENT: Bad request", "Invalid Request"),
            ("UNAVAILABLE: Service down", "Service Unavailable"),
            ("DEADLINE_EXCEEDED: Timeout", "Timeout Error"),
            ("RESOURCE_EXHAUSTED: Server overloaded", "Resource Exhausted"),
            ("Unknown error occurred", "API Error"),
        ]
        
        for error_msg, expected_category in error_scenarios:
            error = Exception(error_msg)
            handled_msg = APIValidator.handle_api_error(error)
            assert expected_category.lower() in handled_msg.lower(), f"Expected {expected_category} in {handled_msg}"
    
    def test_ontology_validation_comprehensive(self):
        """Test comprehensive ontology term validation."""
        # Test various ontology formats
        valid_ontologies = [
            ["UBERON:0001157"],  # Tissue ontology
            ["CL:0000001"],      # Cell ontology
            ["GO:0008150"],      # Gene ontology
            ["SO:0000001"],      # Sequence ontology
            ["CHEBI:0000001"],   # Chemical entities
            ["MONDO:0000001"],   # Disease ontology
        ]
        
        for terms in valid_ontologies:
            is_valid, message, validated = InputValidator.validate_ontology_terms(terms)
            assert is_valid, f"Ontology terms {terms} should be valid: {message}"
            assert len(validated) == len(terms)
    
    def test_output_types_comprehensive(self):
        """Test comprehensive output type validation."""
        # Test all valid AlphaGenome output types
        all_valid_types = [
            'RNA_SEQ', 'ATAC_SEQ', 'CHIP_SEQ', 'CAGE', 'DNASE', 
            'H3K27AC', 'H3K27ME3', 'H3K36ME3', 'H3K4ME1', 
            'H3K4ME3', 'H3K9ME3', 'HISTONE_MARKS', 'CONTACT_MAP'
        ]
        
        # Test individual types
        for output_type in all_valid_types:
            is_valid, message, validated = InputValidator.validate_output_types([output_type])
            assert is_valid, f"Output type {output_type} should be valid: {message}"
            assert output_type in validated
        
        # Test multiple types
        is_valid, message, validated = InputValidator.validate_output_types(all_valid_types)
        assert is_valid, f"All output types should be valid: {message}"
        assert len(validated) == len(all_valid_types)
    
    def test_coordinate_boundary_validation(self):
        """Test genomic coordinate boundary validation."""
        # Test maximum coordinate limits
        max_coord = 250000000

        # Valid coordinates within the 1M bp limit
        valid_interval = f"chr1:1000-500000"  # 499K bp, within limit
        is_valid, message, interval = InputValidator.validate_interval(valid_interval)
        assert is_valid, f"Interval within limit should be valid: {message}"
        
        # Invalid coordinates exceeding the limit
        invalid_interval = f"chr1:1000-{max_coord + 1000}"
        is_valid, message, interval = InputValidator.validate_interval(invalid_interval)
        assert not is_valid, f"Interval exceeding max should be invalid: {message}"
        
        # Test variant position limits
        valid_variant = f"chr1:{max_coord - 1000}:A>T"
        is_valid, message, variant = InputValidator.validate_variant(valid_variant)
        assert is_valid, f"Variant near max should be valid: {message}"
        
        invalid_variant = f"chr1:{max_coord + 1000}:A>T"
        is_valid, message, variant = InputValidator.validate_variant(invalid_variant)
        assert not is_valid, f"Variant exceeding max should be invalid: {message}"


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
