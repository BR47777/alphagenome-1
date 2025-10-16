"""
UI Components for AlphaGenome Chainlit Application

This module contains reusable UI components and utilities for the AlphaGenome interface.
"""

import chainlit as cl
from typing import Dict, List, Optional, Any, Tuple
import asyncio

# AlphaGenome imports
from alphagenome.data import genome, ontology
from alphagenome.models import dna_client

class InputValidator:
    """Validates user inputs for genomic data."""
    
    @staticmethod
    def validate_dna_sequence(sequence: str) -> Tuple[bool, str]:
        """Validate DNA sequence input."""
        if not sequence:
            return False, "Sequence cannot be empty"
        
        sequence = sequence.upper().strip()
        valid_chars = set('ACGTN')
        invalid_chars = set(sequence) - valid_chars
        
        if invalid_chars:
            return False, f"Invalid characters found: {', '.join(invalid_chars)}. Only A, C, G, T, N allowed."
        
        if len(sequence) < 10:
            return False, "Sequence too short. Minimum 10 base pairs required."
        
        if len(sequence) > 1000000:
            return False, "Sequence too long. Maximum 1,000,000 base pairs allowed."
        
        return True, "Valid DNA sequence"
    
    @staticmethod
    def validate_interval(interval_str: str) -> Tuple[bool, str, Optional[genome.Interval]]:
        """Validate genomic interval input."""
        try:
            # Parse interval string like 'chr22:35677410-36725986'
            if ':' not in interval_str or '-' not in interval_str:
                return False, "Invalid format. Use: chr:start-end (e.g., chr22:1000-2000)", None
            
            chrom_part, pos_part = interval_str.split(':', 1)
            start_str, end_str = pos_part.split('-', 1)
            
            chromosome = chrom_part.strip()
            start = int(start_str.strip().replace(',', ''))
            end = int(end_str.strip().replace(',', ''))
            
            if start < 0:
                return False, "Start position cannot be negative", None
            
            if end <= start:
                return False, "End position must be greater than start position", None
            
            width = end - start
            if width > 1000000:
                return False, "Interval too large. Maximum 1,000,000 base pairs allowed.", None
            
            if width < 100:
                return False, "Interval too small. Minimum 100 base pairs required.", None
            
            interval = genome.Interval(chromosome=chromosome, start=start, end=end)
            return True, f"Valid interval ({width:,} bp)", interval
            
        except (ValueError, IndexError) as e:
            return False, f"Invalid interval format: {str(e)}", None
    
    @staticmethod
    def validate_variant(variant_str: str) -> Tuple[bool, str, Optional[genome.Variant]]:
        """Validate variant input."""
        try:
            # Parse variant string like 'chr22:36201698:A>C'
            if ':' not in variant_str or '>' not in variant_str:
                return False, "Invalid format. Use: chr:pos:ref>alt (e.g., chr22:1000:A>T)", None
            
            parts = variant_str.split(':')
            if len(parts) < 3:
                return False, "Invalid format. Use: chr:pos:ref>alt", None
            
            chromosome = parts[0].strip()
            position = int(parts[1].strip().replace(',', ''))
            alleles = parts[2].strip()
            
            if '>' not in alleles:
                return False, "Invalid allele format. Use: ref>alt (e.g., A>T)", None
            
            ref, alt = alleles.split('>', 1)
            ref = ref.strip().upper()
            alt = alt.strip().upper()
            
            if not ref or not alt:
                return False, "Reference and alternate alleles cannot be empty", None
            
            valid_chars = set('ACGTN')
            if not set(ref).issubset(valid_chars) or not set(alt).issubset(valid_chars):
                return False, "Invalid allele characters. Only A, C, G, T, N allowed.", None
            
            if position < 1:
                return False, "Position must be positive (1-based)", None
            
            variant = genome.Variant(
                chromosome=chromosome,
                position=position,
                reference_bases=ref,
                alternate_bases=alt
            )
            
            return True, f"Valid variant ({ref}>{alt} at {chromosome}:{position})", variant
            
        except (ValueError, IndexError) as e:
            return False, f"Invalid variant format: {str(e)}", None

class UIHelpers:
    """Helper functions for UI interactions."""
    
    @staticmethod
    async def show_loading_message(message: str) -> cl.Message:
        """Show a loading message with spinner."""
        return await cl.Message(content=f"🔄 {message}").send()
    
    @staticmethod
    async def show_success_message(message: str) -> cl.Message:
        """Show a success message."""
        return await cl.Message(content=f"✅ {message}", author="System").send()
    
    @staticmethod
    async def show_error_message(message: str) -> cl.Message:
        """Show an error message."""
        return await cl.Message(content=f"❌ {message}", author="System").send()
    
    @staticmethod
    async def show_warning_message(message: str) -> cl.Message:
        """Show a warning message."""
        return await cl.Message(content=f"⚠️ {message}", author="System").send()
    
    @staticmethod
    async def show_info_message(message: str) -> cl.Message:
        """Show an info message."""
        return await cl.Message(content=f"ℹ️ {message}", author="System").send()
    
    @staticmethod
    def format_interval_info(interval: genome.Interval) -> str:
        """Format interval information for display."""
        return (
            f"**Chromosome**: {interval.chromosome}\n"
            f"**Start**: {interval.start:,}\n"
            f"**End**: {interval.end:,}\n"
            f"**Width**: {interval.width:,} bp\n"
            f"**Strand**: {interval.strand}"
        )
    
    @staticmethod
    def format_variant_info(variant: genome.Variant) -> str:
        """Format variant information for display."""
        return (
            f"**Chromosome**: {variant.chromosome}\n"
            f"**Position**: {variant.position:,}\n"
            f"**Reference**: {variant.reference_bases}\n"
            f"**Alternate**: {variant.alternate_bases}\n"
            f"**Type**: {'SNV' if len(variant.reference_bases) == 1 and len(variant.alternate_bases) == 1 else 'INDEL'}"
        )
    
    @staticmethod
    def format_prediction_summary(outputs) -> str:
        """Format prediction output summary."""
        summary_lines = ["**Available Outputs:**"]
        
        output_types = [
            ('RNA-seq', outputs.rna_seq),
            ('ATAC-seq', outputs.atac),
            ('DNase-seq', outputs.dnase),
            ('CAGE', outputs.cage),
            ('ChIP-histone', outputs.chip_histone),
            ('ChIP-TF', outputs.chip_tf),
            ('Splice sites', outputs.splice_sites),
            ('Splice junctions', outputs.splice_junctions),
            ('Contact maps', outputs.contact_maps),
            ('ProCAP', outputs.procap)
        ]
        
        for name, output in output_types:
            if output is not None:
                if hasattr(output, 'values'):
                    shape = output.values.shape
                    summary_lines.append(f"- {name}: {shape}")
                else:
                    summary_lines.append(f"- {name}: Available")
        
        return "\n".join(summary_lines)

class AdvancedInputForms:
    """Advanced input forms for complex genomic analyses."""
    
    @staticmethod
    async def get_prediction_parameters() -> Dict[str, Any]:
        """Get advanced prediction parameters from user."""
        
        # Organism selection
        organism_msg = await cl.AskUserMessage(
            content="Select organism (human/mouse):",
            timeout=30
        ).send()
        
        organism_input = organism_msg['content'].lower().strip() if organism_msg else 'human'
        organism = dna_client.Organism.HOMO_SAPIENS if organism_input in ['human', 'h'] else dna_client.Organism.MUS_MUSCULUS
        
        # Output types selection
        output_msg = await cl.AskUserMessage(
            content="Select output types (comma-separated, or 'all' for all types):\n"
                   "Available: rna_seq, atac, dnase, cage, chip_histone, chip_tf, splice_sites, contact_maps",
            timeout=60
        ).send()
        
        output_input = output_msg['content'].strip() if output_msg else 'rna_seq,atac'
        
        if output_input.lower() == 'all':
            requested_outputs = list(dna_client.OutputType)
        else:
            output_map = {
                'rna_seq': dna_client.OutputType.RNA_SEQ,
                'atac': dna_client.OutputType.ATAC,
                'dnase': dna_client.OutputType.DNASE,
                'cage': dna_client.OutputType.CAGE,
                'chip_histone': dna_client.OutputType.CHIP_HISTONE,
                'chip_tf': dna_client.OutputType.CHIP_TF,
                'splice_sites': dna_client.OutputType.SPLICE_SITES,
                'contact_maps': dna_client.OutputType.CONTACT_MAPS
            }
            
            requested_outputs = []
            for output_name in output_input.split(','):
                output_name = output_name.strip().lower()
                if output_name in output_map:
                    requested_outputs.append(output_map[output_name])
        
        if not requested_outputs:
            requested_outputs = [dna_client.OutputType.RNA_SEQ, dna_client.OutputType.ATAC]
        
        # Ontology terms (optional)
        ontology_msg = await cl.AskUserMessage(
            content="Enter ontology terms (comma-separated, or press Enter to skip):",
            timeout=30
        ).send()
        
        ontology_input = ontology_msg['content'].strip() if ontology_msg else ''
        ontology_terms = None
        if ontology_input:
            ontology_terms = [term.strip() for term in ontology_input.split(',')]
        
        return {
            'organism': organism,
            'requested_outputs': requested_outputs,
            'ontology_terms': ontology_terms
        }
    
    @staticmethod
    async def get_batch_input() -> List[str]:
        """Get batch input for multiple predictions."""
        
        batch_msg = await cl.AskUserMessage(
            content="Enter multiple items (one per line):\n"
                   "For sequences: paste DNA sequences\n"
                   "For intervals: chr:start-end format\n"
                   "For variants: chr:pos:ref>alt format",
            timeout=120
        ).send()
        
        if batch_msg:
            items = [line.strip() for line in batch_msg['content'].split('\n') if line.strip()]
            return items
        
        return []

class ResultsDisplay:
    """Display and format prediction results."""
    
    @staticmethod
    async def display_prediction_results(outputs, input_type: str, input_data: str):
        """Display comprehensive prediction results."""
        
        # Summary message
        summary = UIHelpers.format_prediction_summary(outputs)
        await cl.Message(
            content=f"## 📊 Prediction Results\n\n"
                   f"**Input Type**: {input_type}\n"
                   f"**Input**: {input_data[:100]}{'...' if len(input_data) > 100 else ''}\n\n"
                   f"{summary}"
        ).send()
        
        # Detailed results for each output type
        if outputs.rna_seq is not None:
            await ResultsDisplay._display_track_data("RNA-seq Expression", outputs.rna_seq)
        
        if outputs.atac is not None:
            await ResultsDisplay._display_track_data("ATAC-seq Accessibility", outputs.atac)
        
        if outputs.contact_maps is not None:
            await ResultsDisplay._display_contact_maps("Contact Maps", outputs.contact_maps)
    
    @staticmethod
    async def _display_track_data(title: str, track_data):
        """Display track data information."""
        try:
            shape = track_data.values.shape
            metadata_count = len(track_data.metadata) if hasattr(track_data, 'metadata') else 0
            
            content = f"### {title}\n\n"
            content += f"**Data Shape**: {shape}\n"
            content += f"**Tracks**: {metadata_count}\n"
            
            if hasattr(track_data, 'interval'):
                content += f"**Interval**: {track_data.interval.chromosome}:{track_data.interval.start:,}-{track_data.interval.end:,}\n"
            
            # Basic statistics
            if hasattr(track_data.values, 'mean'):
                content += f"**Mean Value**: {track_data.values.mean():.4f}\n"
                content += f"**Max Value**: {track_data.values.max():.4f}\n"
                content += f"**Min Value**: {track_data.values.min():.4f}\n"
            
            await cl.Message(content=content).send()
            
        except Exception as e:
            await UIHelpers.show_error_message(f"Error displaying {title}: {str(e)}")
    
    @staticmethod
    async def _display_contact_maps(title: str, contact_data):
        """Display contact map information."""
        try:
            content = f"### {title}\n\n"
            
            if hasattr(contact_data, 'values'):
                shape = contact_data.values.shape
                content += f"**Data Shape**: {shape}\n"
            
            if hasattr(contact_data, 'interval'):
                content += f"**Interval**: {contact_data.interval.chromosome}:{contact_data.interval.start:,}-{contact_data.interval.end:,}\n"
            
            content += "Contact maps represent 3D chromatin organization and interactions."
            
            await cl.Message(content=content).send()
            
        except Exception as e:
            await UIHelpers.show_error_message(f"Error displaying {title}: {str(e)}")
