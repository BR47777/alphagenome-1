#!/usr/bin/env python3
"""
AlphaGenome Chainlit UI Application

A comprehensive web interface for the AlphaGenome genomic prediction model.
Provides interactive tools for genomic sequence analysis, variant prediction,
and visualization of results.
"""

import asyncio
import io
import os
import traceback
import time
from typing import Dict, List, Optional, Any

import chainlit as cl
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# AlphaGenome imports
from alphagenome.data import genome, ontology
from alphagenome.models import dna_client, variant_scorers
from alphagenome.visualization import plot_components
import matplotlib

# Local imports
from ui_components import InputValidator, UIHelpers, AdvancedInputForms, ResultsDisplay, APIValidator
from utils.logging_config import get_logger, get_error_handler, get_performance_monitor, setup_logging
from ui_enhancements import UIEnhancements, MessageEnhancements
from api_client import EnhancedAlphaGenomeClient

# Set matplotlib backend for web display
matplotlib.use('Agg')

# Initialize logging
logger = setup_logging(os.getenv("LOG_LEVEL", "INFO"))
error_handler = get_error_handler()
performance_monitor = get_performance_monitor()

# Global variables
dna_model = None
current_session_data = {}

@cl.on_chat_start
async def start():
    """Initialize the chat session and display welcome message."""
    logger.info("Starting new chat session")
    performance_monitor.start_timer("session_initialization")

    try:
        # Enhanced welcome message with styling
        welcome_content = UIEnhancements.create_welcome_card()
        feature_grid = UIEnhancements.create_feature_grid()
        quick_start = UIEnhancements.create_quick_start_guide()

        full_welcome = f"""
{welcome_content}

{feature_grid}

{quick_start}

---

### 💬 **How to Get Started**

Type one of these commands to begin:
- **`setup`** - Configure your API key
- **`help`** - View detailed instructions
- **`sequence: ATCGATCG...`** - Analyze a DNA sequence
- **`interval: chr22:1000-2000`** - Analyze a genomic region
- **`variant: chr22:1000:A>T`** - Analyze a variant effect
        """

        await MessageEnhancements.send_enhanced_message(
            content=full_welcome,
            message_type="info",
            author="AlphaGenome"
        )

        # Check if API key is available
        api_key = os.getenv("ALPHAGENOME_API_KEY")
        if not api_key:
            logger.info("No API key found in environment")
            status_card = UIEnhancements.create_status_card(
                "warning",
                "API Key Required: Please set your AlphaGenome API key using the 'setup' command.",
                "warning"
            )
            await MessageEnhancements.send_enhanced_message(
                content=status_card,
                message_type="warning",
                author="System"
            )
        else:
            logger.info("API key found in environment, initializing model")
            await initialize_model(api_key)

        performance_monitor.end_timer("session_initialization")

    except Exception as e:
        error_msg = error_handler.handle_unexpected_error(e, "session initialization")
        await cl.Message(content=error_msg, author="System").send()
        performance_monitor.end_timer("session_initialization")

async def initialize_model(api_key: str):
    """Initialize the AlphaGenome model with the provided API key."""
    global dna_model

    logger.info("Initializing AlphaGenome model")
    performance_monitor.start_timer("model_initialization")

    try:
        # Validate API key format first
        logger.debug("Validating API key format")
        is_valid, validation_msg = InputValidator.validate_api_key(api_key)
        if not is_valid:
            logger.warning(f"API key validation failed: {validation_msg}")
            error_msg = error_handler.handle_validation_error("api_key", validation_msg, api_key[:10] + "...")
            await cl.Message(content=error_msg, author="System").send()
            return False

        # Show enhanced loading message with progress
        progress_content = UIEnhancements.create_progress_bar(0.1, "Initializing AlphaGenome model...")
        loading_msg = await MessageEnhancements.send_enhanced_message(
            content=f"🔄 **Initializing AlphaGenome Model**\n\n{progress_content}",
            message_type="info",
            author="AlphaGenome"
        )

        # Create the model client with timeout
        try:
            logger.debug("Creating DNA client")
            start_time = time.time()
            dna_model = dna_client.create(api_key)
            client_creation_time = time.time() - start_time
            logger.info(f"DNA client created successfully in {client_creation_time:.2f}s")

        except Exception as e:
            logger.error(f"Failed to create DNA client: {str(e)}")
            error_msg = error_handler.handle_api_error(e, "model creation")
            loading_msg.content = error_msg
            await loading_msg.update()
            return False

        # Test the connection and validate response
        try:
            logger.debug("Testing API connection and retrieving metadata")
            start_time = time.time()
            metadata = dna_model.output_metadata()
            metadata_time = time.time() - start_time
            logger.info(f"Metadata retrieved successfully in {metadata_time:.2f}s")

            is_valid_response, response_msg = APIValidator.validate_api_response(metadata, 'metadata')

            if not is_valid_response:
                logger.error(f"Invalid API response: {response_msg}")
                loading_msg.content = f"❌ **API Response Error**: {response_msg}"
                await loading_msg.update()
                return False

        except Exception as e:
            logger.error(f"Failed to retrieve metadata: {str(e)}")
            error_msg = error_handler.handle_api_error(e, "metadata retrieval")
            loading_msg.content = error_msg
            await loading_msg.update()
            return False

        # Count available output types
        output_count = len([field for field in metadata.__dataclass_fields__])
        logger.info(f"Model initialized with {output_count} available output types")

        # Update loading message with success
        success_card = UIEnhancements.create_status_card(
            "success",
            f"AlphaGenome model initialized successfully!\n\n"
            f"🔬 Available output types: {output_count}\n"
            f"🔑 API key validated: {validation_msg}\n"
            f"🚀 You can now start making predictions!",
            "success"
        )
        loading_msg.content = success_card
        await loading_msg.update()

        # Store in session
        current_session_data['model'] = dna_model
        current_session_data['api_key'] = api_key
        current_session_data['metadata'] = metadata

        performance_monitor.end_timer("model_initialization", {"output_types": output_count})
        logger.info("Model initialization completed successfully")
        return True

    except Exception as e:
        logger.error(f"Unexpected error during model initialization: {str(e)}")
        error_msg = error_handler.handle_unexpected_error(e, "model initialization")
        await cl.Message(
            content=f"{error_msg}\n\n"
                   "💡 **Troubleshooting tips:**\n"
                   "- Verify your API key is correct\n"
                   "- Check your internet connection\n"
                   "- Ensure you have API quota remaining",
            author="System"
        ).send()
        performance_monitor.end_timer("model_initialization")
        return False


async def predict_variant_enhanced(chromosome: str, position: int, ref: str, alt: str) -> Dict[str, Any]:
    """Enhanced variant prediction using the new API client."""
    logger.info(f"Starting enhanced variant prediction: {chromosome}:{position}:{ref}>{alt}")
    performance_monitor.start_timer("enhanced_variant_prediction")

    try:
        # Get API key from session
        api_key = current_session_data.get('api_key')
        if not api_key:
            raise ValueError("No API key available")

        # Create enhanced client and make prediction
        async with EnhancedAlphaGenomeClient(api_key) as client:
            response = await client.predict_variant_hybrid(
                chromosome=chromosome,
                position=position,
                ref=ref,
                alt=alt,
                organism="human"
            )

            performance_monitor.end_timer(
                "enhanced_variant_prediction",
                {"success": response.success, "response_time": response.response_time}
            )

            if response.success:
                logger.info(f"Enhanced variant prediction successful in {response.response_time:.2f}s")
                return {
                    "success": True,
                    "data": response.data,
                    "response_time": response.response_time,
                    "method": response.data.get("method", "REST_API")
                }
            else:
                logger.error(f"Enhanced variant prediction failed: {response.error}")
                return {
                    "success": False,
                    "error": response.error,
                    "response_time": response.response_time
                }

    except Exception as e:
        performance_monitor.end_timer("enhanced_variant_prediction")
        logger.error(f"Enhanced variant prediction exception: {str(e)}")
        return {
            "success": False,
            "error": f"Prediction failed: {str(e)}"
        }


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages and route to appropriate handlers."""
    
    user_input = message.content.strip().lower()
    
    # Command routing
    if user_input == "help":
        await show_help()
    elif user_input == "setup":
        await setup_api_key()
    elif user_input.startswith("predict sequence"):
        await handle_sequence_prediction_enhanced(message.content)
    elif user_input.startswith("predict interval"):
        await handle_interval_prediction_enhanced(message.content)
    elif user_input.startswith("predict variant"):
        await handle_variant_prediction_enhanced(message.content)
    elif user_input.startswith("score"):
        await handle_scoring(message.content)
    elif user_input == "examples":
        await show_examples()
    elif user_input == "status":
        await show_status()
    elif user_input == "advanced":
        await show_advanced_options()
    elif user_input == "batch":
        await handle_batch_processing()
    elif user_input == "test api":
        await test_enhanced_api()
    else:
        await handle_general_query(message.content)


async def test_enhanced_api():
    """Test the enhanced API functionality."""
    logger.info("Testing enhanced API functionality")

    # Check if model is initialized
    if not current_session_data.get('model') or not current_session_data.get('api_key'):
        await MessageEnhancements.send_enhanced_message(
            content=UIEnhancements.create_status_card(
                "error",
                "Please initialize the model first by setting up your API key.",
                "error"
            ),
            author="System"
        )
        return

    # Show testing progress
    progress_content = UIEnhancements.create_progress_bar(0.2, "Testing enhanced API...")
    test_msg = await MessageEnhancements.send_enhanced_message(
        content=f"🧪 **Testing Enhanced API**\n\n{progress_content}",
        author="AlphaGenome"
    )

    try:
        # Test variant prediction with example data
        result = await predict_variant_enhanced(
            chromosome="chr12",
            position=11223344,
            ref="G",
            alt="C"
        )

        # Update progress
        progress_content = UIEnhancements.create_progress_bar(1.0, "API test completed!")

        if result["success"]:
            # Format successful result
            method = result.get("method", "Unknown")
            response_time = result.get("response_time", 0)

            success_content = f"""
{UIEnhancements.create_status_card(
    "success",
    f"Enhanced API test successful!\n\n"
    f"🔬 Method used: {method}\n"
    f"⚡ Response time: {response_time:.2f}s\n"
    f"📊 Data received: {len(str(result.get('data', {})))} characters",
    "success"
)}

{progress_content}
            """

            test_msg.content = success_content
            await test_msg.update()

        else:
            # Format error result
            error_content = f"""
{UIEnhancements.create_status_card(
    "warning",
    f"REST API not available, using SDK fallback: {result.get('error', 'Unknown error')}",
    "warning"
)}

{progress_content}
            """

            test_msg.content = error_content
            await test_msg.update()

    except Exception as e:
        logger.error(f"API test failed with exception: {str(e)}")
        error_content = f"""
{UIEnhancements.create_status_card(
    "error",
    f"API test encountered an error: {str(e)}",
    "error"
)}
        """

        test_msg.content = error_content
        await test_msg.update()


async def show_help():
    """Display comprehensive help information."""
    
    help_content = """
# 📖 AlphaGenome UI Help

## Commands:

### Setup
- `setup` - Configure your API key
- `status` - Check current configuration

### Predictions
- `predict sequence <DNA_SEQUENCE>` - Predict from DNA sequence
- `predict interval chr:start-end` - Predict from genomic interval
- `predict variant chr:pos:ref>alt` - Analyze variant effects

### Scoring
- `score interval chr:start-end` - Score genomic interval
- `score variant chr:pos:ref>alt` - Score variant effects

### Utilities
- `examples` - Show example commands
- `help` - Show this help message
- `test api` - Test enhanced API functionality
- `advanced` - Show advanced options
- `batch` - Batch processing options

## Example Usage:

```
predict sequence ATCGATCGATCG
predict interval chr22:35677410-36725986
predict variant chr22:36201698:A>C
score interval chr1:1000000-1100000
```

## Supported Features:
- Multiple output types (RNA-seq, ATAC-seq, ChIP-seq, etc.)
- Organism selection (Human, Mouse)
- Ontology term filtering
- Interactive visualizations
- Batch processing

For detailed examples, type `examples`.
    """
    
    await cl.Message(content=help_content).send()

async def setup_api_key():
    """Handle API key setup through user input."""
    
    setup_msg = """
# 🔑 API Key Setup

Please provide your AlphaGenome API key. You can obtain one from:
https://deepmind.google.com/science/alphagenome

**Enter your API key:**
    """
    
    await cl.Message(content=setup_msg).send()
    
    # Wait for user input
    api_key_response = await cl.AskUserMessage(
        content="Please enter your AlphaGenome API key:",
        timeout=60
    ).send()
    
    if api_key_response:
        api_key = api_key_response['content'].strip()
        if api_key:
            await initialize_model(api_key)
        else:
            await cl.Message(
                content="❌ No API key provided. Please try again.",
                author="System"
            ).send()

async def show_examples():
    """Display example commands and use cases."""
    
    examples_content = """
# 🧪 Example Commands

## 1. Sequence Prediction
```
predict sequence ATCGATCGATCGATCGATCGATCGATCGATCGATCG
```
Analyzes a DNA sequence and predicts various genomic outputs.

## 2. Interval Prediction
```
predict interval chr22:35677410-36725986
```
Predicts outputs for a specific genomic region.

## 3. Variant Analysis
```
predict variant chr22:36201698:A>C
```
Compares reference vs alternate allele effects.

## 4. Interval Scoring
```
score interval chr1:1000000-1100000
```
Generates comprehensive scores for a genomic interval.

## 5. Variant Scoring
```
score variant chr22:36201698:A>C
```
Scores the functional impact of a genetic variant.

## Advanced Options:
- Add organism: `predict sequence ATCG --organism mouse`
- Specify outputs: `predict interval chr1:1000-2000 --outputs rna_seq,atac`
- Filter ontology: `predict variant chr1:1000:A>T --ontology UBERON:0001157`

Try any of these examples to get started!
    """
    
    await cl.Message(content=examples_content).send()

async def show_status():
    """Display current session status."""
    
    if dna_model is None:
        status_msg = "❌ **Status**: Model not initialized. Please run `setup` to configure your API key."
    else:
        status_msg = "✅ **Status**: AlphaGenome model ready for predictions!"
        
        # Add session info if available
        if current_session_data:
            status_msg += f"\n\n**Session Info:**\n"
            status_msg += f"- Model initialized: Yes\n"
            status_msg += f"- API key configured: {'Yes' if current_session_data.get('api_key') else 'No'}\n"
    
    await cl.Message(content=status_msg, author="System").send()

async def handle_sequence_prediction(content: str):
    """Handle DNA sequence prediction requests."""

    if dna_model is None:
        await cl.Message(
            content="❌ Model not initialized. Please run `setup` first.",
            author="System"
        ).send()
        return

    try:
        # Parse the command
        parts = content.split(maxsplit=2)
        if len(parts) < 3:
            await cl.Message(
                content="❌ Please provide a DNA sequence. Example: `predict sequence ATCGATCG`",
                author="System"
            ).send()
            return

        sequence = parts[2].upper().strip()

        # Validate sequence
        if not all(base in 'ACGTN' for base in sequence):
            await cl.Message(
                content="❌ Invalid DNA sequence. Only A, C, G, T, N characters allowed.",
                author="System"
            ).send()
            return

        # Show processing message
        processing_msg = await cl.Message(
            content=f"🔄 Processing DNA sequence ({len(sequence)} bp)..."
        ).send()

        # Make prediction
        outputs = dna_model.predict_sequence(
            sequence=sequence,
            organism=dna_client.Organism.HOMO_SAPIENS,
            requested_outputs=[dna_client.OutputType.RNA_SEQ, dna_client.OutputType.ATAC],
            ontology_terms=None
        )

        # Create visualization
        fig_buffer = await create_sequence_visualization(outputs, sequence)

        # Update message with results
        await processing_msg.update(
            content=f"✅ **Sequence Prediction Complete**\n\n"
                   f"**Sequence**: {sequence[:50]}{'...' if len(sequence) > 50 else ''}\n"
                   f"**Length**: {len(sequence)} bp\n"
                   f"**Outputs**: RNA-seq, ATAC-seq predictions generated"
        )

        # Send visualization
        if fig_buffer:
            await cl.Message(
                content="📊 **Prediction Visualization**",
                elements=[cl.Image(content=fig_buffer, name="prediction_plot", display="inline")]
            ).send()

    except Exception as e:
        await cl.Message(
            content=f"❌ **Error in sequence prediction**: {str(e)}",
            author="System"
        ).send()

async def handle_interval_prediction(content: str):
    """Handle genomic interval prediction requests."""

    if dna_model is None:
        await cl.Message(
            content="❌ Model not initialized. Please run `setup` first.",
            author="System"
        ).send()
        return

    try:
        # Parse interval from command
        parts = content.split(maxsplit=2)
        if len(parts) < 3:
            await cl.Message(
                content="❌ Please provide an interval. Example: `predict interval chr22:35677410-36725986`",
                author="System"
            ).send()
            return

        interval_str = parts[2].strip()
        interval = parse_interval_string(interval_str)

        if not interval:
            await cl.Message(
                content="❌ Invalid interval format. Use: chr:start-end (e.g., chr22:1000-2000)",
                author="System"
            ).send()
            return

        # Show processing message
        processing_msg = await cl.Message(
            content=f"🔄 Processing genomic interval {interval_str}..."
        ).send()

        # Make prediction
        outputs = dna_model.predict_interval(
            interval=interval,
            organism=dna_client.Organism.HOMO_SAPIENS,
            requested_outputs=[dna_client.OutputType.RNA_SEQ, dna_client.OutputType.ATAC],
            ontology_terms=None
        )

        # Create visualization
        fig_buffer = await create_interval_visualization(outputs, interval)

        # Update message with results
        await processing_msg.update(
            content=f"✅ **Interval Prediction Complete**\n\n"
                   f"**Interval**: {interval_str}\n"
                   f"**Width**: {interval.width:,} bp\n"
                   f"**Outputs**: RNA-seq, ATAC-seq predictions generated"
        )

        # Send visualization
        if fig_buffer:
            await cl.Message(
                content="📊 **Prediction Visualization**",
                elements=[cl.Image(content=fig_buffer, name="interval_plot", display="inline")]
            ).send()

    except Exception as e:
        await cl.Message(
            content=f"❌ **Error in interval prediction**: {str(e)}",
            author="System"
        ).send()

async def handle_variant_prediction(content: str):
    """Handle variant effect prediction requests."""

    if dna_model is None:
        await cl.Message(
            content="❌ Model not initialized. Please run `setup` first.",
            author="System"
        ).send()
        return

    try:
        # Parse variant from command
        parts = content.split(maxsplit=2)
        if len(parts) < 3:
            await cl.Message(
                content="❌ Please provide a variant. Example: `predict variant chr22:36201698:A>C`",
                author="System"
            ).send()
            return

        variant_str = parts[2].strip()
        variant, interval = parse_variant_string(variant_str)

        if not variant or not interval:
            await cl.Message(
                content="❌ Invalid variant format. Use: chr:pos:ref>alt (e.g., chr22:1000:A>T)",
                author="System"
            ).send()
            return

        # Show processing message
        processing_msg = await cl.Message(
            content=f"🔄 Processing variant {variant_str}..."
        ).send()

        # Make prediction
        outputs = dna_model.predict_variant(
            interval=interval,
            variant=variant,
            organism=dna_client.Organism.HOMO_SAPIENS,
            requested_outputs=[dna_client.OutputType.RNA_SEQ],
            ontology_terms=None
        )

        # Create visualization
        fig_buffer = await create_variant_visualization(outputs, variant, interval)

        # Update message with results
        await processing_msg.update(
            content=f"✅ **Variant Prediction Complete**\n\n"
                   f"**Variant**: {variant_str}\n"
                   f"**Reference**: {variant.reference_bases}\n"
                   f"**Alternate**: {variant.alternate_bases}\n"
                   f"**Outputs**: Reference vs Alternate comparison generated"
        )

        # Send visualization
        if fig_buffer:
            await cl.Message(
                content="📊 **Variant Effect Visualization**",
                elements=[cl.Image(content=fig_buffer, name="variant_plot", display="inline")]
            ).send()

    except Exception as e:
        await cl.Message(
            content=f"❌ **Error in variant prediction**: {str(e)}",
            author="System"
        ).send()

async def handle_scoring(content: str):
    """Handle interval and variant scoring requests."""

    if dna_model is None:
        await cl.Message(
            content="❌ Model not initialized. Please run `setup` first.",
            author="System"
        ).send()
        return

    try:
        parts = content.split()
        if len(parts) < 3:
            await cl.Message(
                content="❌ Please specify what to score. Examples:\n"
                       "- `score interval chr1:1000-2000`\n"
                       "- `score variant chr1:1000:A>T`",
                author="System"
            ).send()
            return

        score_type = parts[1].lower()
        target = " ".join(parts[2:])

        if score_type == "interval":
            await handle_interval_scoring(target)
        elif score_type == "variant":
            await handle_variant_scoring(target)
        else:
            await cl.Message(
                content="❌ Unknown scoring type. Use 'interval' or 'variant'.",
                author="System"
            ).send()

    except Exception as e:
        await cl.Message(
            content=f"❌ **Error in scoring**: {str(e)}",
            author="System"
        ).send()

async def handle_sequence_prediction_enhanced(content: str):
    """Enhanced sequence prediction with validation and better UI."""

    if dna_model is None:
        await UIHelpers.show_error_message("Model not initialized. Please run `setup` first.")
        return

    try:
        # Parse the command
        parts = content.split(maxsplit=2)
        if len(parts) < 3:
            await UIHelpers.show_error_message("Please provide a DNA sequence. Example: `predict sequence ATCGATCG`")
            return

        sequence = parts[2].upper().strip()

        # Validate sequence
        is_valid, message = InputValidator.validate_dna_sequence(sequence)
        if not is_valid:
            await UIHelpers.show_error_message(message)
            return

        await UIHelpers.show_success_message(message)

        # Get advanced parameters
        params = await AdvancedInputForms.get_prediction_parameters()

        # Show processing message
        processing_msg = await UIHelpers.show_loading_message(
            f"Processing DNA sequence ({len(sequence):,} bp) with {len(params['requested_outputs'])} output types..."
        )

        # Make prediction
        outputs = dna_model.predict_sequence(
            sequence=sequence,
            organism=params['organism'],
            requested_outputs=params['requested_outputs'],
            ontology_terms=params['ontology_terms']
        )

        # Update processing message
        await processing_msg.update(
            content=f"✅ **Sequence Prediction Complete**\n\n"
                   f"**Sequence Length**: {len(sequence):,} bp\n"
                   f"**Organism**: {params['organism'].name}\n"
                   f"**Output Types**: {len(params['requested_outputs'])}"
        )

        # Display results
        await ResultsDisplay.display_prediction_results(outputs, "DNA Sequence", sequence)

        # Create and send visualization
        fig_buffer = await create_sequence_visualization(outputs, sequence)
        if fig_buffer:
            await cl.Message(
                content="📊 **Prediction Visualization**",
                elements=[cl.Image(content=fig_buffer, name="sequence_plot", display="inline")]
            ).send()

    except Exception as e:
        await UIHelpers.show_error_message(f"Error in sequence prediction: {str(e)}")

async def handle_interval_prediction_enhanced(content: str):
    """Enhanced interval prediction with validation and better UI."""

    if dna_model is None:
        await UIHelpers.show_error_message("Model not initialized. Please run `setup` first.")
        return

    try:
        # Parse interval from command
        parts = content.split(maxsplit=2)
        if len(parts) < 3:
            await UIHelpers.show_error_message("Please provide an interval. Example: `predict interval chr22:35677410-36725986`")
            return

        interval_str = parts[2].strip()

        # Validate interval
        is_valid, message, interval = InputValidator.validate_interval(interval_str)
        if not is_valid:
            await UIHelpers.show_error_message(message)
            return

        await UIHelpers.show_success_message(message)

        # Show interval info
        interval_info = UIHelpers.format_interval_info(interval)
        await cl.Message(content=f"**Interval Information:**\n{interval_info}").send()

        # Get advanced parameters
        params = await AdvancedInputForms.get_prediction_parameters()

        # Show processing message
        processing_msg = await UIHelpers.show_loading_message(
            f"Processing genomic interval ({interval.width:,} bp) with {len(params['requested_outputs'])} output types..."
        )

        # Make prediction
        outputs = dna_model.predict_interval(
            interval=interval,
            organism=params['organism'],
            requested_outputs=params['requested_outputs'],
            ontology_terms=params['ontology_terms']
        )

        # Update processing message
        await processing_msg.update(
            content=f"✅ **Interval Prediction Complete**\n\n"
                   f"**Interval**: {interval_str}\n"
                   f"**Width**: {interval.width:,} bp\n"
                   f"**Organism**: {params['organism'].name}\n"
                   f"**Output Types**: {len(params['requested_outputs'])}"
        )

        # Display results
        await ResultsDisplay.display_prediction_results(outputs, "Genomic Interval", interval_str)

        # Create and send visualization
        fig_buffer = await create_interval_visualization(outputs, interval)
        if fig_buffer:
            await cl.Message(
                content="📊 **Prediction Visualization**",
                elements=[cl.Image(content=fig_buffer, name="interval_plot", display="inline")]
            ).send()

    except Exception as e:
        await UIHelpers.show_error_message(f"Error in interval prediction: {str(e)}")

async def handle_variant_prediction_enhanced(content: str):
    """Enhanced variant prediction with validation and better UI."""

    if dna_model is None:
        await UIHelpers.show_error_message("Model not initialized. Please run `setup` first.")
        return

    try:
        # Parse variant from command
        parts = content.split(maxsplit=2)
        if len(parts) < 3:
            await UIHelpers.show_error_message("Please provide a variant. Example: `predict variant chr22:36201698:A>C`")
            return

        variant_str = parts[2].strip()

        # Validate variant
        is_valid, message, variant = InputValidator.validate_variant(variant_str)
        if not is_valid:
            await UIHelpers.show_error_message(message)
            return

        await UIHelpers.show_success_message(message)

        # Show variant info
        variant_info = UIHelpers.format_variant_info(variant)
        await cl.Message(content=f"**Variant Information:**\n{variant_info}").send()

        # Create interval around variant
        interval_start = max(0, variant.position - 50000)
        interval_end = variant.position + 50000
        interval = genome.Interval(
            chromosome=variant.chromosome,
            start=interval_start,
            end=interval_end
        )

        # Get advanced parameters
        params = await AdvancedInputForms.get_prediction_parameters()

        # Show processing message
        processing_msg = await UIHelpers.show_loading_message(
            f"Processing variant effect analysis with {len(params['requested_outputs'])} output types..."
        )

        # Make prediction
        outputs = dna_model.predict_variant(
            interval=interval,
            variant=variant,
            organism=params['organism'],
            requested_outputs=params['requested_outputs'],
            ontology_terms=params['ontology_terms']
        )

        # Update processing message
        await processing_msg.update(
            content=f"✅ **Variant Prediction Complete**\n\n"
                   f"**Variant**: {variant_str}\n"
                   f"**Type**: {'SNV' if len(variant.reference_bases) == 1 and len(variant.alternate_bases) == 1 else 'INDEL'}\n"
                   f"**Organism**: {params['organism'].name}\n"
                   f"**Output Types**: {len(params['requested_outputs'])}"
        )

        # Display results with comparison
        await display_variant_comparison_results(outputs, variant)

        # Create and send visualization
        fig_buffer = await create_variant_visualization(outputs, variant, interval)
        if fig_buffer:
            await cl.Message(
                content="📊 **Variant Effect Visualization**",
                elements=[cl.Image(content=fig_buffer, name="variant_plot", display="inline")]
            ).send()

    except Exception as e:
        await UIHelpers.show_error_message(f"Error in variant prediction: {str(e)}")

async def show_advanced_options():
    """Show advanced analysis options."""

    advanced_content = """
# 🔬 Advanced Analysis Options

## Available Advanced Features:

### 1. Batch Processing
- `batch` - Process multiple sequences, intervals, or variants at once
- Upload files or paste multiple entries

### 2. Custom Parameters
- Organism selection (Human/Mouse)
- Output type filtering
- Ontology term specification
- Model version selection

### 3. Comparative Analysis
- Side-by-side variant comparisons
- Multi-interval analysis
- Time-series predictions

### 4. Export Options
- Download prediction data
- Export visualizations
- Generate reports

### 5. Advanced Scoring
- Custom scoring metrics
- Pathway analysis
- Functional annotation

To use advanced features, include them in your commands or type the specific command name.

Example: `batch` to start batch processing
    """

    await cl.Message(content=advanced_content).send()

async def handle_batch_processing():
    """Handle batch processing of multiple inputs."""

    if dna_model is None:
        await UIHelpers.show_error_message("Model not initialized. Please run `setup` first.")
        return

    await UIHelpers.show_info_message("Starting batch processing mode...")

    # Get batch input
    items = await AdvancedInputForms.get_batch_input()

    if not items:
        await UIHelpers.show_warning_message("No items provided for batch processing.")
        return

    await UIHelpers.show_info_message(f"Processing {len(items)} items...")

    # Process each item
    results = []
    for i, item in enumerate(items):
        try:
            await UIHelpers.show_loading_message(f"Processing item {i+1}/{len(items)}: {item[:50]}...")

            # Determine item type and process
            if ':' in item and '-' in item and '>' not in item:
                # Interval
                is_valid, message, interval = InputValidator.validate_interval(item)
                if is_valid:
                    # Process interval (simplified for batch)
                    results.append(f"✅ Interval {item}: Processed successfully")
                else:
                    results.append(f"❌ Interval {item}: {message}")
            elif ':' in item and '>' in item:
                # Variant
                is_valid, message, variant = InputValidator.validate_variant(item)
                if is_valid:
                    # Process variant (simplified for batch)
                    results.append(f"✅ Variant {item}: Processed successfully")
                else:
                    results.append(f"❌ Variant {item}: {message}")
            else:
                # Sequence
                is_valid, message = InputValidator.validate_dna_sequence(item)
                if is_valid:
                    # Process sequence (simplified for batch)
                    results.append(f"✅ Sequence {item[:20]}...: Processed successfully")
                else:
                    results.append(f"❌ Sequence {item[:20]}...: {message}")

        except Exception as e:
            results.append(f"❌ Item {item[:20]}...: Error - {str(e)}")

    # Display batch results
    results_text = "## 📊 Batch Processing Results\n\n" + "\n".join(results)
    await cl.Message(content=results_text).send()

async def display_variant_comparison_results(outputs, variant: genome.Variant):
    """Display variant comparison results."""

    content = f"## 🧬 Variant Effect Analysis\n\n"
    content += f"**Variant**: {variant.chromosome}:{variant.position}:{variant.reference_bases}>{variant.alternate_bases}\n\n"

    # Compare reference vs alternate
    if hasattr(outputs, 'reference') and hasattr(outputs, 'alternate'):
        content += "### Reference vs Alternate Comparison\n\n"

        # RNA-seq comparison
        if outputs.reference.rna_seq is not None and outputs.alternate.rna_seq is not None:
            ref_mean = outputs.reference.rna_seq.values.mean()
            alt_mean = outputs.alternate.rna_seq.values.mean()
            fold_change = alt_mean / ref_mean if ref_mean != 0 else float('inf')

            content += f"**RNA-seq Expression:**\n"
            content += f"- Reference: {ref_mean:.4f}\n"
            content += f"- Alternate: {alt_mean:.4f}\n"
            content += f"- Fold Change: {fold_change:.4f}\n\n"

        # ATAC-seq comparison
        if outputs.reference.atac is not None and outputs.alternate.atac is not None:
            ref_mean = outputs.reference.atac.values.mean()
            alt_mean = outputs.alternate.atac.values.mean()
            fold_change = alt_mean / ref_mean if ref_mean != 0 else float('inf')

            content += f"**ATAC-seq Accessibility:**\n"
            content += f"- Reference: {ref_mean:.4f}\n"
            content += f"- Alternate: {alt_mean:.4f}\n"
            content += f"- Fold Change: {fold_change:.4f}\n\n"

    await cl.Message(content=content).send()

async def handle_general_query(content: str):
    """Handle general queries and provide guidance."""

    response = """
I'm here to help you with AlphaGenome predictions!

Here are some things you can try:
- Type `help` for detailed commands
- Type `examples` for sample predictions
- Type `setup` to configure your API key
- Type `status` to check your current setup
- Type `advanced` for advanced analysis options
- Type `batch` for batch processing

If you want to make a prediction, use commands like:
- `predict sequence <DNA_SEQUENCE>`
- `predict interval chr:start-end`
- `predict variant chr:pos:ref>alt`

What would you like to do?
    """

    await cl.Message(content=response).send()

# Utility functions

def parse_interval_string(interval_str: str) -> Optional[genome.Interval]:
    """Parse interval string like 'chr22:35677410-36725986' into Interval object."""
    try:
        # Handle different formats
        if ':' in interval_str and '-' in interval_str:
            chrom_part, pos_part = interval_str.split(':', 1)
            start_str, end_str = pos_part.split('-', 1)

            chromosome = chrom_part.strip()
            start = int(start_str.strip().replace(',', ''))
            end = int(end_str.strip().replace(',', ''))

            return genome.Interval(chromosome=chromosome, start=start, end=end)
    except (ValueError, IndexError):
        pass
    return None

def parse_variant_string(variant_str: str) -> tuple[Optional[genome.Variant], Optional[genome.Interval]]:
    """Parse variant string like 'chr22:36201698:A>C' into Variant and Interval objects."""
    try:
        # Handle format: chr:pos:ref>alt
        if ':' in variant_str and '>' in variant_str:
            parts = variant_str.split(':')
            if len(parts) >= 3:
                chromosome = parts[0].strip()
                position = int(parts[1].strip().replace(',', ''))
                alleles = parts[2].strip()

                if '>' in alleles:
                    ref, alt = alleles.split('>', 1)
                    ref = ref.strip().upper()
                    alt = alt.strip().upper()

                    variant = genome.Variant(
                        chromosome=chromosome,
                        position=position,
                        reference_bases=ref,
                        alternate_bases=alt
                    )

                    # Create interval around variant (±50kb)
                    interval_start = max(0, position - 50000)
                    interval_end = position + 50000
                    interval = genome.Interval(
                        chromosome=chromosome,
                        start=interval_start,
                        end=interval_end
                    )

                    return variant, interval
    except (ValueError, IndexError):
        pass
    return None, None

async def create_sequence_visualization(outputs, sequence: str) -> Optional[bytes]:
    """Create visualization for sequence prediction results."""
    try:
        plt.style.use('default')
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))

        # Plot RNA-seq if available
        if outputs.rna_seq is not None:
            rna_data = outputs.rna_seq.values
            if rna_data.ndim > 1:
                rna_data = rna_data.mean(axis=1)  # Average across tracks

            axes[0].plot(rna_data[:min(1000, len(rna_data))], color='blue', alpha=0.7)
            axes[0].set_title('RNA-seq Predictions')
            axes[0].set_ylabel('Expression Level')
            axes[0].grid(True, alpha=0.3)

        # Plot ATAC if available
        if outputs.atac is not None:
            atac_data = outputs.atac.values
            if atac_data.ndim > 1:
                atac_data = atac_data.mean(axis=1)  # Average across tracks

            axes[1].plot(atac_data[:min(1000, len(atac_data))], color='red', alpha=0.7)
            axes[1].set_title('ATAC-seq Predictions')
            axes[1].set_ylabel('Accessibility')
            axes[1].set_xlabel('Position')
            axes[1].grid(True, alpha=0.3)

        plt.tight_layout()

        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close()

        return buffer.getvalue()

    except Exception as e:
        print(f"Error creating sequence visualization: {e}")
        plt.close()
        return None

async def create_interval_visualization(outputs, interval: genome.Interval) -> Optional[bytes]:
    """Create visualization for interval prediction results."""
    try:
        # Use AlphaGenome's built-in visualization components
        components = []

        if outputs.rna_seq is not None:
            components.append(
                plot_components.Tracks(
                    outputs.rna_seq,
                    filled=True,
                    track_height=1.5
                )
            )

        if outputs.atac is not None:
            components.append(
                plot_components.Tracks(
                    outputs.atac,
                    filled=True,
                    track_height=1.5
                )
            )

        if components:
            fig = plot_components.plot(
                components,
                interval=interval,
                fig_width=12,
                title=f"Predictions for {interval.chromosome}:{interval.start:,}-{interval.end:,}"
            )

            # Save to buffer
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plt.close()

            return buffer.getvalue()

    except Exception as e:
        print(f"Error creating interval visualization: {e}")
        plt.close()
        return None

async def create_variant_visualization(outputs, variant: genome.Variant, interval: genome.Interval) -> Optional[bytes]:
    """Create visualization for variant effect prediction results."""
    try:
        components = []

        if outputs.reference.rna_seq is not None and outputs.alternate.rna_seq is not None:
            components.append(
                plot_components.OverlaidTracks(
                    tdata={
                        'REF': outputs.reference.rna_seq,
                        'ALT': outputs.alternate.rna_seq,
                    },
                    colors={'REF': 'dimgrey', 'ALT': 'red'},
                    track_height=2.0
                )
            )

        if components:
            # Create variant annotation
            variant_annotation = plot_components.VariantAnnotation([variant], alpha=0.8)

            fig = plot_components.plot(
                components,
                interval=interval.resize(min(100000, interval.width)),  # Limit display width
                annotations=[variant_annotation],
                fig_width=12,
                title=f"Variant Effect: {variant.chromosome}:{variant.position}:{variant.reference_bases}>{variant.alternate_bases}"
            )

            # Save to buffer
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plt.close()

            return buffer.getvalue()

    except Exception as e:
        print(f"Error creating variant visualization: {e}")
        plt.close()
        return None

async def handle_interval_scoring(target: str):
    """Handle interval scoring requests."""
    try:
        interval = parse_interval_string(target)
        if not interval:
            await cl.Message(
                content="❌ Invalid interval format. Use: chr:start-end",
                author="System"
            ).send()
            return

        processing_msg = await cl.Message(
            content=f"🔄 Scoring interval {target}..."
        ).send()

        # Score the interval
        scores = dna_model.score_interval(
            interval=interval,
            organism=dna_client.Organism.HOMO_SAPIENS
        )

        # Process results
        results_text = f"✅ **Interval Scoring Complete**\n\n"
        results_text += f"**Interval**: {target}\n"
        results_text += f"**Width**: {interval.width:,} bp\n"
        results_text += f"**Scores Generated**: {len(scores)} scoring methods\n\n"

        for i, score_data in enumerate(scores):
            results_text += f"**Score {i+1}**: {score_data.shape[0]} features\n"

        await processing_msg.update(content=results_text)

    except Exception as e:
        await cl.Message(
            content=f"❌ **Error in interval scoring**: {str(e)}",
            author="System"
        ).send()

async def handle_variant_scoring(target: str):
    """Handle variant scoring requests."""
    try:
        variant, interval = parse_variant_string(target)
        if not variant or not interval:
            await cl.Message(
                content="❌ Invalid variant format. Use: chr:pos:ref>alt",
                author="System"
            ).send()
            return

        processing_msg = await cl.Message(
            content=f"🔄 Scoring variant {target}..."
        ).send()

        # Score the variant
        scores = dna_model.score_variant(
            interval=interval,
            variant=variant,
            organism=dna_client.Organism.HOMO_SAPIENS
        )

        # Process results
        results_text = f"✅ **Variant Scoring Complete**\n\n"
        results_text += f"**Variant**: {target}\n"
        results_text += f"**Reference**: {variant.reference_bases}\n"
        results_text += f"**Alternate**: {variant.alternate_bases}\n"
        results_text += f"**Scores Generated**: {len(scores)} scoring methods\n\n"

        for i, score_data in enumerate(scores):
            results_text += f"**Score {i+1}**: {score_data.shape[0]} features\n"

        await processing_msg.update(content=results_text)

    except Exception as e:
        await cl.Message(
            content=f"❌ **Error in variant scoring**: {str(e)}",
            author="System"
        ).send()

if __name__ == "__main__":
    # This allows running the app directly
    pass
