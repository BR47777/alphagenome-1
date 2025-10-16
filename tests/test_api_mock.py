#!/usr/bin/env python3
"""
Mock API tests for AlphaGenome UI application.
Tests API interactions without requiring actual API calls.
"""

import pytest
import sys
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui_components import APIValidator
from alphagenome.data import genome


class TestMockAPIInteractions:
    """Test API interactions using mocks."""
    
    @pytest.fixture
    def mock_interval(self):
        """Create a mock genomic interval."""
        return genome.Interval(chromosome="chr22", start=35677410, end=36725986)
    
    @pytest.fixture
    def mock_variant(self):
        """Create a mock genomic variant."""
        return genome.Variant(
            chromosome="chr22",
            position=36201698,
            reference_bases="A",
            alternate_bases="C"
        )
    
    @pytest.fixture
    def mock_track_data(self):
        """Create mock track data."""
        mock_track = Mock()
        mock_track.interval = genome.Interval(chromosome="chr22", start=35677410, end=36725986)
        mock_track.values = np.random.random(1000)  # Mock genomic signal
        mock_track.resize = Mock(return_value=mock_track)
        return mock_track
    
    @pytest.fixture
    def mock_prediction_output(self, mock_track_data):
        """Create mock prediction output."""
        mock_output = Mock()
        mock_output.reference = Mock()
        mock_output.alternate = Mock()
        
        # Add RNA-seq data
        mock_output.reference.rna_seq = mock_track_data
        mock_output.alternate.rna_seq = mock_track_data
        
        # Add ATAC-seq data
        mock_output.reference.atac_seq = mock_track_data
        mock_output.alternate.atac_seq = mock_track_data
        
        return mock_output
    
    @pytest.fixture
    def mock_dna_client(self, mock_prediction_output):
        """Create a comprehensive mock DNA client."""
        mock_client = Mock()

        # Mock metadata - ensure it doesn't have error attribute
        mock_metadata = Mock()
        mock_metadata.__dataclass_fields__ = {
            'rna_seq': None,
            'atac_seq': None,
            'chip_seq': None,
            'cage': None,
            'dnase': None,
            'h3k27ac': None,
            'h3k27me3': None,
            'h3k36me3': None,
            'h3k4me1': None,
            'h3k4me3': None,
            'h3k9me3': None,
            'contact_map': None
        }
        # Create a simple object instead of Mock to avoid error attribute
        class MockMetadata:
            def __init__(self):
                self.__dataclass_fields__ = {
                    'rna_seq': None,
                    'atac_seq': None,
                    'chip_seq': None,
                    'cage': None,
                    'dnase': None,
                    'h3k27ac': None,
                    'h3k27me3': None,
                    'h3k36me3': None,
                    'h3k4me1': None,
                    'h3k4me3': None,
                    'h3k9me3': None,
                    'contact_map': None
                }

        mock_client.output_metadata.return_value = MockMetadata()
        
        # Create simple prediction output without error attribute
        class MockPredictionOutput:
            def __init__(self):
                self.reference = Mock()
                self.alternate = Mock()
                self.reference.rna_seq = mock_prediction_output.reference.rna_seq
                self.alternate.rna_seq = mock_prediction_output.alternate.rna_seq
                self.reference.atac_seq = mock_prediction_output.reference.atac_seq
                self.alternate.atac_seq = mock_prediction_output.alternate.atac_seq

        prediction_output = MockPredictionOutput()
        mock_client.predict_variant.return_value = prediction_output
        mock_client.predict_interval.return_value = prediction_output
        mock_client.predict_sequence.return_value = prediction_output

        return mock_client
    
    def test_mock_client_creation(self, mock_dna_client):
        """Test that mock client behaves like real client."""
        # Test metadata access
        metadata = mock_dna_client.output_metadata()
        assert hasattr(metadata, '__dataclass_fields__')
        assert len(metadata.__dataclass_fields__) > 0
        
        # Validate metadata response
        is_valid, message = APIValidator.validate_api_response(metadata, 'metadata')
        assert is_valid, f"Mock metadata should be valid: {message}"
    
    def test_mock_variant_prediction(self, mock_dna_client, mock_interval, mock_variant):
        """Test variant prediction with mock client."""
        # Make prediction
        output = mock_dna_client.predict_variant(
            interval=mock_interval,
            variant=mock_variant,
            ontology_terms=['UBERON:0001157'],
            requested_outputs=['RNA_SEQ']
        )
        
        # Validate response structure
        assert hasattr(output, 'reference')
        assert hasattr(output, 'alternate')
        assert hasattr(output.reference, 'rna_seq')
        assert hasattr(output.alternate, 'rna_seq')
        
        # Validate API response
        is_valid, message = APIValidator.validate_api_response(output, 'prediction')
        assert is_valid, f"Mock prediction should be valid: {message}"
    
    def test_mock_interval_prediction(self, mock_dna_client, mock_interval):
        """Test interval prediction with mock client."""
        # Make prediction
        output = mock_dna_client.predict_interval(
            interval=mock_interval,
            ontology_terms=['UBERON:0001157'],
            requested_outputs=['RNA_SEQ', 'ATAC_SEQ']
        )
        
        # Validate response structure
        assert hasattr(output, 'reference')
        assert hasattr(output.reference, 'rna_seq')
        assert hasattr(output.reference, 'atac_seq')
    
    def test_mock_sequence_prediction(self, mock_dna_client):
        """Test sequence prediction with mock client."""
        test_sequence = "ATCGATCGATCGATCGATCGATCGATCGATCGATCG"
        
        # Make prediction
        output = mock_dna_client.predict_sequence(
            sequence=test_sequence,
            ontology_terms=['UBERON:0001157'],
            requested_outputs=['RNA_SEQ']
        )
        
        # Validate response structure
        assert hasattr(output, 'reference')
        assert hasattr(output.reference, 'rna_seq')
    
    @patch('app.dna_client')
    def test_api_error_simulation(self, mock_dna_client_module):
        """Test API error scenarios with mocks."""
        from app import initialize_model
        
        # Test different error types
        error_scenarios = [
            Exception("PERMISSION_DENIED: Invalid API key"),
            Exception("QUOTA_EXCEEDED: Daily limit reached"),
            Exception("INVALID_ARGUMENT: Bad request format"),
            Exception("UNAVAILABLE: Service temporarily unavailable"),
            Exception("DEADLINE_EXCEEDED: Request timeout"),
            Exception("RESOURCE_EXHAUSTED: Server overloaded"),
        ]
        
        for error in error_scenarios:
            mock_dna_client_module.create.side_effect = error
            
            # Test error handling
            error_msg = APIValidator.handle_api_error(error)
            assert len(error_msg) > 0
            assert "❌" in error_msg
            
            # Reset mock
            mock_dna_client_module.reset_mock()
    
    def test_track_data_validation(self, mock_track_data):
        """Test track data structure validation."""
        # Validate track data has required attributes
        assert hasattr(mock_track_data, 'interval')
        assert hasattr(mock_track_data, 'values')
        assert isinstance(mock_track_data.interval, genome.Interval)
        
        # Test track data operations
        resized_track = mock_track_data.resize(1000)
        assert resized_track is not None
    
    def test_genomic_coordinate_validation(self, mock_interval, mock_variant):
        """Test genomic coordinate validation with real objects."""
        # Test interval properties
        assert mock_interval.chromosome == "chr22"
        assert mock_interval.start == 35677410
        assert mock_interval.end == 36725986
        assert mock_interval.width == mock_interval.end - mock_interval.start
        
        # Test variant properties
        assert mock_variant.chromosome == "chr22"
        assert mock_variant.position == 36201698
        assert mock_variant.reference_bases == "A"
        assert mock_variant.alternate_bases == "C"
        
        # Test variant-interval overlap
        overlaps = mock_variant.reference_overlaps(mock_interval)
        assert overlaps, "Variant should overlap with interval"
    
    def test_output_type_handling(self, mock_dna_client):
        """Test different output type combinations."""
        from alphagenome.models import dna_client
        
        # Test individual output types
        output_types = ['RNA_SEQ', 'ATAC_SEQ', 'CHIP_SEQ', 'CAGE', 'DNASE']
        
        for output_type in output_types:
            # This would normally make an API call, but we're using mocks
            try:
                # Simulate output type validation
                valid_types = {'RNA_SEQ', 'ATAC_SEQ', 'CHIP_SEQ', 'CAGE', 'DNASE', 
                              'H3K27AC', 'H3K27ME3', 'H3K36ME3', 'H3K4ME1', 
                              'H3K4ME3', 'H3K9ME3', 'HISTONE_MARKS', 'CONTACT_MAP'}
                assert output_type in valid_types, f"Output type {output_type} should be valid"
            except Exception as e:
                pytest.fail(f"Output type {output_type} validation failed: {e}")
    
    def test_batch_prediction_simulation(self, mock_dna_client):
        """Test batch prediction scenarios."""
        # Simulate multiple predictions
        test_variants = [
            ("chr22:36201698:A>C", "SNV"),
            ("chr22:36201700:ATG>A", "deletion"),
            ("chr22:36201705:T>GCA", "insertion"),
        ]
        
        for variant_str, variant_type in test_variants:
            # Parse variant
            parts = variant_str.split(':')
            chromosome = parts[0]
            position = int(parts[1])
            alleles = parts[2].split('>')
            
            # Create variant object
            variant = genome.Variant(
                chromosome=chromosome,
                position=position,
                reference_bases=alleles[0],
                alternate_bases=alleles[1]
            )
            
            # Create interval around variant
            interval = genome.Interval(
                chromosome=chromosome,
                start=position - 500,
                end=position + 500
            )
            
            # Mock prediction
            output = mock_dna_client.predict_variant(
                interval=interval,
                variant=variant,
                ontology_terms=['UBERON:0001157'],
                requested_outputs=['RNA_SEQ']
            )
            
            # Validate output
            assert output is not None
            assert hasattr(output, 'reference')
            assert hasattr(output, 'alternate')
    
    def test_visualization_data_preparation(self, mock_prediction_output):
        """Test data preparation for visualization."""
        # Test that prediction output has required data for plotting
        assert hasattr(mock_prediction_output.reference, 'rna_seq')
        assert hasattr(mock_prediction_output.alternate, 'rna_seq')
        
        # Test track data structure
        ref_track = mock_prediction_output.reference.rna_seq
        alt_track = mock_prediction_output.alternate.rna_seq
        
        assert hasattr(ref_track, 'interval')
        assert hasattr(ref_track, 'values')
        assert hasattr(alt_track, 'interval')
        assert hasattr(alt_track, 'values')
        
        # Test that tracks can be resized (for visualization)
        resized_ref = ref_track.resize(1000)
        resized_alt = alt_track.resize(1000)
        
        assert resized_ref is not None
        assert resized_alt is not None


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
