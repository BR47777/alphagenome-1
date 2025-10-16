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
    """Validates user inputs for genomic data with comprehensive error handling."""

    @staticmethod
    def validate_api_key(api_key: str) -> Tuple[bool, str]:
        """Validate AlphaGenome API key format."""
        if not api_key:
            return False, "API key cannot be empty"

        api_key = api_key.strip()

        # Basic format validation for Google API keys
        if not api_key.startswith('AIza'):
            return False, "Invalid API key format. Google API keys should start with 'AIza'"

        if len(api_key) < 35:
            return False, "API key too short. Expected length is typically 39 characters"

        if len(api_key) > 45:
            return False, "API key too long. Expected length is typically 39 characters"

        # Check for valid characters (alphanumeric, hyphens, underscores)
        import re
        if not re.match(r'^[A-Za-z0-9_-]+$', api_key):
            return False, "API key contains invalid characters. Only alphanumeric, hyphens, and underscores allowed"

        return True, "API key format appears valid"

    @staticmethod
    def validate_dna_sequence(sequence: str) -> Tuple[bool, str]:
        """Validate DNA sequence input with enhanced checks."""
        if not sequence:
            return False, "Sequence cannot be empty"

        if not isinstance(sequence, str):
            return False, "Sequence must be a string"

        sequence = sequence.upper().strip()

        # Remove whitespace and newlines
        sequence = ''.join(sequence.split())

        if not sequence:
            return False, "Sequence cannot be empty after removing whitespace"

        valid_chars = set('ACGTN')
        invalid_chars = set(sequence) - valid_chars

        if invalid_chars:
            return False, f"Invalid characters found: {', '.join(sorted(invalid_chars))}. Only A, C, G, T, N allowed."

        if len(sequence) < 10:
            return False, "Sequence too short. Minimum 10 base pairs required."

        if len(sequence) > 1000000:
            return False, f"Sequence too long ({len(sequence):,} bp). Maximum 1,000,000 base pairs allowed."

        # Check for excessive N content
        n_count = sequence.count('N')
        n_percentage = (n_count / len(sequence)) * 100
        if n_percentage > 50:
            return False, f"Too many N bases ({n_percentage:.1f}%). Maximum 50% N content allowed."

        return True, f"Valid DNA sequence ({len(sequence):,} bp, {n_percentage:.1f}% N content)"
    
    @staticmethod
    def validate_interval(interval_str: str) -> Tuple[bool, str, Optional[genome.Interval]]:
        """Validate genomic interval input with enhanced validation."""
        if not interval_str:
            return False, "Interval cannot be empty", None

        if not isinstance(interval_str, str):
            return False, "Interval must be a string", None

        interval_str = interval_str.strip()

        try:
            # Parse interval string like 'chr22:35677410-36725986'
            if ':' not in interval_str or '-' not in interval_str:
                return False, "Invalid format. Use: chr:start-end (e.g., chr22:1000-2000)", None

            # Split and validate parts
            parts = interval_str.split(':')
            if len(parts) != 2:
                return False, "Invalid format. Use: chr:start-end (e.g., chr22:1000-2000)", None

            chrom_part, pos_part = parts

            if '-' not in pos_part:
                return False, "Invalid format. Missing '-' between start and end positions", None

            pos_parts = pos_part.split('-')
            if len(pos_parts) != 2:
                return False, "Invalid format. Use: chr:start-end (e.g., chr22:1000-2000)", None

            start_str, end_str = pos_parts

            # Validate chromosome
            chromosome = chrom_part.strip()
            if not chromosome:
                return False, "Chromosome cannot be empty", None

            # Validate chromosome format
            import re
            if not re.match(r'^(chr)?([1-9]|1[0-9]|2[0-2]|X|Y|MT?)$', chromosome, re.IGNORECASE):
                return False, f"Invalid chromosome '{chromosome}'. Use format: chr1-22, chrX, chrY, chrMT", None

            # Ensure chr prefix
            if not chromosome.lower().startswith('chr'):
                chromosome = 'chr' + chromosome

            # Parse positions
            try:
                start = int(start_str.strip().replace(',', '').replace(' ', ''))
                end = int(end_str.strip().replace(',', '').replace(' ', ''))
            except ValueError as e:
                return False, f"Invalid position format: {str(e)}", None

            # Validate positions
            if start < 0:
                return False, "Start position cannot be negative", None

            if end < 0:
                return False, "End position cannot be negative", None

            if end <= start:
                return False, f"End position ({end:,}) must be greater than start position ({start:,})", None

            width = end - start
            if width > 2000000:  # Increased to 2M bp for better genomic analysis
                return False, f"Interval too large ({width:,} bp). Maximum 2,000,000 base pairs allowed. Try a smaller region for detailed analysis.", None

            if width < 100:
                return False, f"Interval too small ({width:,} bp). Minimum 100 base pairs required.", None

            # Validate reasonable genomic coordinates
            max_chrom_length = 250000000  # Approximate max chromosome length
            if start > max_chrom_length or end > max_chrom_length:
                return False, f"Position too large. Maximum position is {max_chrom_length:,}", None

            interval = genome.Interval(chromosome=chromosome, start=start, end=end)
            return True, f"Valid interval {chromosome}:{start:,}-{end:,} ({width:,} bp)", interval

        except Exception as e:
            return False, f"Invalid interval format: {str(e)}", None
    
    @staticmethod
    def validate_variant(variant_str: str) -> Tuple[bool, str, Optional[genome.Variant]]:
        """Validate variant input with comprehensive checks."""
        if not variant_str:
            return False, "Variant cannot be empty", None

        if not isinstance(variant_str, str):
            return False, "Variant must be a string", None

        variant_str = variant_str.strip()

        try:
            # Parse variant string like 'chr22:36201698:A>C'
            if ':' not in variant_str or '>' not in variant_str:
                return False, "Invalid format. Use: chr:pos:ref>alt (e.g., chr22:1000:A>T)", None

            parts = variant_str.split(':')
            if len(parts) < 3:
                return False, "Invalid format. Use: chr:pos:ref>alt", None

            if len(parts) > 3:
                # Join extra parts back (in case there are colons in the alleles)
                parts = [parts[0], parts[1], ':'.join(parts[2:])]

            chromosome = parts[0].strip()
            position_str = parts[1].strip()
            alleles = parts[2].strip()

            # Validate chromosome
            if not chromosome:
                return False, "Chromosome cannot be empty", None

            import re
            if not re.match(r'^(chr)?([1-9]|1[0-9]|2[0-2]|X|Y|MT?)$', chromosome, re.IGNORECASE):
                return False, f"Invalid chromosome '{chromosome}'. Use format: chr1-22, chrX, chrY, chrMT", None

            # Ensure chr prefix
            if not chromosome.lower().startswith('chr'):
                chromosome = 'chr' + chromosome

            # Validate position
            try:
                position = int(position_str.replace(',', '').replace(' ', ''))
            except ValueError:
                return False, f"Invalid position '{position_str}'. Must be a positive integer", None

            if position < 1:
                return False, "Position must be positive (1-based coordinate system)", None

            # Validate reasonable genomic coordinates
            max_chrom_length = 250000000
            if position > max_chrom_length:
                return False, f"Position too large ({position:,}). Maximum position is {max_chrom_length:,}", None

            # Validate alleles
            if '>' not in alleles:
                return False, "Invalid allele format. Use: ref>alt (e.g., A>T)", None

            allele_parts = alleles.split('>', 1)
            if len(allele_parts) != 2:
                return False, "Invalid allele format. Use: ref>alt (e.g., A>T)", None

            ref, alt = allele_parts
            ref = ref.strip().upper()
            alt = alt.strip().upper()

            if not ref:
                return False, "Reference allele cannot be empty", None

            if not alt:
                return False, "Alternate allele cannot be empty", None

            # Validate allele characters
            valid_chars = set('ACGTN')
            invalid_ref = set(ref) - valid_chars
            invalid_alt = set(alt) - valid_chars

            if invalid_ref:
                return False, f"Invalid characters in reference allele: {', '.join(sorted(invalid_ref))}", None

            if invalid_alt:
                return False, f"Invalid characters in alternate allele: {', '.join(sorted(invalid_alt))}", None

            # Validate variant type
            if len(ref) > 100 or len(alt) > 100:
                return False, "Alleles too long. Maximum 100 base pairs per allele", None

            # Determine variant type
            if len(ref) == 1 and len(alt) == 1:
                variant_type = "SNV"
            elif len(ref) > len(alt):
                variant_type = "deletion"
            elif len(ref) < len(alt):
                variant_type = "insertion"
            else:
                variant_type = "complex"

            variant = genome.Variant(
                chromosome=chromosome,
                position=position,
                reference_bases=ref,
                alternate_bases=alt
            )

            return True, f"Valid {variant_type}: {chromosome}:{position:,}:{ref}>{alt}", variant

        except Exception as e:
            return False, f"Invalid variant format: {str(e)}", None

    @staticmethod
    def validate_ontology_terms(terms: List[str]) -> Tuple[bool, str, List[str]]:
        """Validate ontology terms (UBERON, CL, etc.)."""
        if not terms:
            return False, "At least one ontology term is required", []

        if not isinstance(terms, list):
            return False, "Ontology terms must be provided as a list", []

        valid_terms = []
        invalid_terms = []

        import re
        # Pattern for UBERON, CL, and other ontology terms
        ontology_pattern = r'^(UBERON|CL|GO|SO|CHEBI|MONDO):[0-9]{7,}$'

        for term in terms:
            if not isinstance(term, str):
                invalid_terms.append(f"Non-string term: {term}")
                continue

            term = term.strip()
            if not term:
                invalid_terms.append("Empty term")
                continue

            if re.match(ontology_pattern, term, re.IGNORECASE):
                valid_terms.append(term)
            else:
                invalid_terms.append(f"Invalid format: {term}")

        if invalid_terms:
            return False, f"Invalid ontology terms: {', '.join(invalid_terms)}", valid_terms

        if len(valid_terms) > 10:
            return False, f"Too many ontology terms ({len(valid_terms)}). Maximum 10 allowed", valid_terms

        return True, f"Valid ontology terms ({len(valid_terms)} terms)", valid_terms

    @staticmethod
    def validate_output_types(output_types: List[str]) -> Tuple[bool, str, List[str]]:
        """Validate AlphaGenome output types."""
        if not output_types:
            return False, "At least one output type is required", []

        if not isinstance(output_types, list):
            return False, "Output types must be provided as a list", []

        # Valid AlphaGenome output types
        valid_output_types = {
            'RNA_SEQ', 'ATAC_SEQ', 'CHIP_SEQ', 'CAGE', 'DNASE', 'H3K27AC', 'H3K27ME3',
            'H3K36ME3', 'H3K4ME1', 'H3K4ME3', 'H3K9ME3', 'HISTONE_MARKS', 'CONTACT_MAP'
        }

        validated_types = []
        invalid_types = []

        for output_type in output_types:
            if not isinstance(output_type, str):
                invalid_types.append(f"Non-string type: {output_type}")
                continue

            output_type = output_type.strip().upper()
            if output_type in valid_output_types:
                validated_types.append(output_type)
            else:
                invalid_types.append(output_type)

        if invalid_types:
            return False, f"Invalid output types: {', '.join(invalid_types)}. Valid types: {', '.join(sorted(valid_output_types))}", validated_types

        return True, f"Valid output types ({len(validated_types)} types)", validated_types

class APIValidator:
    """Validates API responses and handles errors."""

    @staticmethod
    def validate_api_response(response: Any, expected_type: str = None) -> Tuple[bool, str]:
        """Validate API response structure and content."""
        if response is None:
            return False, "API response is None"

        try:
            # Check for common error patterns
            if hasattr(response, 'error'):
                return False, f"API error: {response.error}"

            if hasattr(response, 'status') and response.status != 'success':
                return False, f"API returned status: {response.status}"

            # Validate expected type if provided
            if expected_type:
                if expected_type == 'prediction' and not hasattr(response, 'reference'):
                    return False, "Invalid prediction response: missing reference data"

                if expected_type == 'metadata' and not hasattr(response, '__dataclass_fields__'):
                    return False, "Invalid metadata response: not a dataclass"

            return True, "Valid API response"

        except Exception as e:
            return False, f"Error validating API response: {str(e)}"

    @staticmethod
    def handle_api_error(error: Exception) -> str:
        """Handle and format API errors for user display."""
        error_str = str(error)

        # Common API error patterns
        if "PERMISSION_DENIED" in error_str or "401" in error_str:
            return "❌ **Authentication Error**: Invalid API key. Please check your AlphaGenome API key."

        if "QUOTA_EXCEEDED" in error_str or "429" in error_str:
            return "❌ **Quota Exceeded**: You have exceeded your API quota. Please try again later."

        if "INVALID_ARGUMENT" in error_str or "400" in error_str:
            return f"❌ **Invalid Request**: {error_str}"

        if "UNAVAILABLE" in error_str or "503" in error_str:
            return "❌ **Service Unavailable**: AlphaGenome API is temporarily unavailable. Please try again later."

        if "DEADLINE_EXCEEDED" in error_str or "timeout" in error_str.lower():
            return "❌ **Timeout Error**: Request took too long. Try with a smaller sequence or interval."

        if "RESOURCE_EXHAUSTED" in error_str:
            return "❌ **Resource Exhausted**: Server is overloaded. Please try again later."

        # Generic error
        return f"❌ **API Error**: {error_str}"

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
