#!/usr/bin/env python3
"""
Demo script for AlphaGenome Chainlit UI

This script demonstrates the core functionality without requiring the full UI.
Useful for testing and understanding the application components.
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def demo_input_validation():
    """Demonstrate input validation functionality."""
    print("🧪 Demo: Input Validation")
    print("-" * 40)

    from ui_components import InputValidator

    # Test sequences
    sequences = [
        "ATCGATCGATCGATCGATCGATCGATCGATCGATCG",
        "ATCGATCXGATCG",  # Invalid
        "ATCG"  # Too short
    ]

    print("DNA Sequence Validation:")
    for seq in sequences:
        is_valid, message = InputValidator.validate_dna_sequence(seq)
        status = "✅" if is_valid else "❌"
        print(f"{status} {seq[:20]}{'...' if len(seq) > 20 else ''}: {message}")

    # Test intervals
    intervals = [
        "chr22:1000-2000",
        "chr1:100000-200000",
        "chr22:2000-1000"  # Invalid
    ]

    print("\nGenomic Interval Validation:")
    for interval in intervals:
        is_valid, message, _ = InputValidator.validate_interval(interval)
        status = "✅" if is_valid else "❌"
        print(f"{status} {interval}: {message}")

    # Test variants
    variants = [
        "chr22:1000:A>T",
        "chr1:100000:ATG>C",
        "chr22:1000:A>X"  # Invalid
    ]

    print("\nGenetic Variant Validation:")
    for variant in variants:
        is_valid, message, _ = InputValidator.validate_variant(variant)
        status = "✅" if is_valid else "❌"
        print(f"{status} {variant}: {message}")

def demo_genome_objects():
    """Demonstrate AlphaGenome data objects."""
    print("\n🧬 Demo: AlphaGenome Data Objects")
    print("-" * 40)

    from alphagenome.data import genome

    # Create genomic interval
    interval = genome.Interval(
        chromosome="chr22",
        start=35677410,
        end=36725986
    )

    print(f"Genomic Interval:")
    print(f"  Chromosome: {interval.chromosome}")
    print(f"  Start: {interval.start:,}")
    print(f"  End: {interval.end:,}")
    print(f"  Width: {interval.width:,} bp")
    print(f"  Strand: {interval.strand}")

    # Create genetic variant
    variant = genome.Variant(
        chromosome="chr22",
        position=36201698,
        reference_bases="A",
        alternate_bases="C"
    )

    print(f"\nGenetic Variant:")
    print(f"  Chromosome: {variant.chromosome}")
    print(f"  Position: {variant.position:,}")
    print(f"  Reference: {variant.reference_bases}")
    print(f"  Alternate: {variant.alternate_bases}")
    print(f"  Type: {'SNV' if len(variant.reference_bases) == 1 and len(variant.alternate_bases) == 1 else 'INDEL'}")

    # Check overlap
    overlaps = variant.reference_overlaps(interval)
    print(f"\nVariant overlaps interval: {overlaps}")

def demo_ui_helpers():
    """Demonstrate UI helper functions."""
    print("\n🎨 Demo: UI Helper Functions")
    print("-" * 40)

    from ui_components import UIHelpers
    from alphagenome.data import genome

    # Create test data
    interval = genome.Interval("chr22", 1000, 2000)
    variant = genome.Variant("chr22", 1500, "A", "T")

    # Format information
    print("Formatted Interval Info:")
    print(UIHelpers.format_interval_info(interval))

    print("\nFormatted Variant Info:")
    print(UIHelpers.format_variant_info(variant))

def demo_visualization():
    """Demonstrate visualization capabilities."""
    print("\n📊 Demo: Visualization")
    print("-" * 40)

    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend

    import matplotlib.pyplot as plt
    import numpy as np
    import io

    # Create sample genomic data
    positions = np.arange(0, 1000)
    rna_seq_data = np.random.exponential(2, 1000) + np.sin(positions / 100) * 0.5
    atac_data = np.random.gamma(2, 2, 1000) + np.cos(positions / 150) * 1.0

    # Create visualization
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # RNA-seq plot
    ax1.plot(positions, rna_seq_data, color='blue', alpha=0.7, linewidth=1)
    ax1.fill_between(positions, rna_seq_data, alpha=0.3, color='blue')
    ax1.set_title('RNA-seq Expression Prediction')
    ax1.set_ylabel('Expression Level')
    ax1.grid(True, alpha=0.3)

    # ATAC-seq plot
    ax2.plot(positions, atac_data, color='red', alpha=0.7, linewidth=1)
    ax2.fill_between(positions, atac_data, alpha=0.3, color='red')
    ax2.set_title('ATAC-seq Accessibility Prediction')
    ax2.set_ylabel('Accessibility')
    ax2.set_xlabel('Genomic Position')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save to buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()

    print(f"Created sample visualization ({len(buffer.getvalue()):,} bytes)")
    print("✅ Visualization system working correctly")

def demo_model_interface():
    """Demonstrate model interface (without actual API calls)."""
    print("\n🤖 Demo: Model Interface")
    print("-" * 40)

    from alphagenome.models import dna_client

    # Show available output types
    print("Available Output Types:")
    for output_type in dna_client.OutputType:
        print(f"  - {output_type.name}")

    # Show available organisms
    print("\nSupported Organisms:")
    for organism in dna_client.Organism:
        print(f"  - {organism.name}")

    print("\nNote: Actual predictions require a valid API key and network connection.")

def main():
    """Run all demos."""
    print("🧬 AlphaGenome Chainlit UI - Demo")
    print("=" * 50)
    print("This demo showcases the core functionality without requiring an API key.")
    print()

    demos = [
        demo_input_validation,
        demo_genome_objects,
        demo_ui_helpers,
        demo_visualization,
        demo_model_interface
    ]

    for demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"❌ Error in {demo_func.__name__}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 50)
    print("🎉 Demo completed!")
    print("\nTo run the full application:")
    print("1. Set your API key: export ALPHAGENOME_API_KEY=your_key_here")
    print("2. Run: python run_app.py")
    print("3. Open: http://localhost:8000")

if __name__ == "__main__":
    main()