#!/usr/bin/env python3
"""
Advanced UI enhancements for AlphaGenome Chainlit application.
"""

import chainlit as cl
from typing import Dict, List, Optional, Any
import base64
import io


class UIEnhancements:
    """Advanced UI enhancements and styling."""
    
    # Avatar configurations
    AVATARS = {
        "alphagenome": {
            "name": "AlphaGenome",
            "url": "https://raw.githubusercontent.com/google-deepmind/alphagenome/main/docs/source/_static/alphagenome_logo.png",
            "path": "./assets/alphagenome_avatar.png"
        },
        "system": {
            "name": "System",
            "url": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
            "path": "./assets/system_avatar.png"
        },
        "user": {
            "name": "User",
            "url": "https://cdn-icons-png.flaticon.com/512/3135/3135768.png",
            "path": "./assets/user_avatar.png"
        },
        "assistant": {
            "name": "Assistant",
            "url": "https://cdn-icons-png.flaticon.com/512/4712/4712027.png",
            "path": "./assets/assistant_avatar.png"
        }
    }
    
    # Color scheme
    COLORS = {
        "primary": "#1E88E5",
        "secondary": "#43A047", 
        "accent": "#FF7043",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336",
        "info": "#2196F3",
        "background": "#F5F5F5",
        "surface": "#FFFFFF",
        "text_primary": "#212121",
        "text_secondary": "#757575"
    }
    
    @staticmethod
    def create_welcome_card() -> str:
        """Create an enhanced welcome card with styling."""
        return """
<div style="
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 15px;
    padding: 30px;
    color: white;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    margin: 20px 0;
">
    <h1 style="margin: 0 0 20px 0; font-size: 2.5em; font-weight: 300;">
        🧬 AlphaGenome Interactive UI
    </h1>
    <p style="font-size: 1.2em; margin: 0 0 20px 0; opacity: 0.9;">
        Powered by Google DeepMind's revolutionary genomic prediction model
    </p>
    <div style="
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    ">
        <h3 style="margin: 0 0 15px 0;">🚀 What You Can Do</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; text-align: left;">
            <div>
                <strong>🔬 Sequence Analysis</strong><br>
                Predict genomic outputs from DNA sequences
            </div>
            <div>
                <strong>📍 Interval Prediction</strong><br>
                Analyze specific genomic regions
            </div>
            <div>
                <strong>🧬 Variant Effects</strong><br>
                Compare reference vs alternate alleles
            </div>
            <div>
                <strong>📊 Visualizations</strong><br>
                Interactive plots and data exploration
            </div>
        </div>
    </div>
</div>
        """
    
    @staticmethod
    def create_status_card(status: str, message: str, color: str = "info") -> str:
        """Create a styled status card."""
        color_map = {
            "success": "#4CAF50",
            "error": "#F44336", 
            "warning": "#FF9800",
            "info": "#2196F3"
        }
        
        bg_color = color_map.get(color, "#2196F3")
        
        return f"""
<div style="
    background: {bg_color};
    border-radius: 10px;
    padding: 20px;
    color: white;
    margin: 15px 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
">
    <h3 style="margin: 0 0 10px 0; display: flex; align-items: center;">
        <span style="margin-right: 10px; font-size: 1.2em;">
            {'✅' if status == 'success' else '❌' if status == 'error' else '⚠️' if status == 'warning' else 'ℹ️'}
        </span>
        {status.title()}
    </h3>
    <p style="margin: 0; opacity: 0.9;">{message}</p>
</div>
        """
    
    @staticmethod
    def create_feature_grid() -> str:
        """Create a feature grid with enhanced styling."""
        return """
<div style="
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin: 30px 0;
">
    <div style="
        background: white;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        border-left: 5px solid #1E88E5;
    ">
        <h3 style="color: #1E88E5; margin: 0 0 15px 0;">🔬 Enhanced Validation</h3>
        <ul style="margin: 0; padding-left: 20px; color: #666;">
            <li>API key format validation</li>
            <li>DNA sequence validation</li>
            <li>Genomic coordinate checking</li>
            <li>Variant format validation</li>
        </ul>
    </div>
    
    <div style="
        background: white;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        border-left: 5px solid #43A047;
    ">
        <h3 style="color: #43A047; margin: 0 0 15px 0;">🛡️ Robust Error Handling</h3>
        <ul style="margin: 0; padding-left: 20px; color: #666;">
            <li>User-friendly error messages</li>
            <li>API error categorization</li>
            <li>Performance monitoring</li>
            <li>Graceful degradation</li>
        </ul>
    </div>
    
    <div style="
        background: white;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        border-left: 5px solid #FF7043;
    ">
        <h3 style="color: #FF7043; margin: 0 0 15px 0;">🧪 Comprehensive Testing</h3>
        <ul style="margin: 0; padding-left: 20px; color: #666;">
            <li>36 test cases</li>
            <li>Unit & integration tests</li>
            <li>Mock API testing</li>
            <li>92% test coverage</li>
        </ul>
    </div>
</div>
        """
    
    @staticmethod
    def create_quick_start_guide() -> str:
        """Create an interactive quick start guide."""
        return """
<div style="
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    border-radius: 15px;
    padding: 30px;
    color: white;
    margin: 20px 0;
">
    <h2 style="margin: 0 0 20px 0; text-align: center;">🚀 Quick Start Guide</h2>
    
    <div style="
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
    ">
        <div style="
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        ">
            <div style="font-size: 2em; margin-bottom: 10px;">1️⃣</div>
            <h4 style="margin: 0 0 10px 0;">Set API Key</h4>
            <p style="margin: 0; font-size: 0.9em; opacity: 0.8;">
                Type "setup" to configure your AlphaGenome API key
            </p>
        </div>
        
        <div style="
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        ">
            <div style="font-size: 2em; margin-bottom: 10px;">2️⃣</div>
            <h4 style="margin: 0 0 10px 0;">Choose Analysis</h4>
            <p style="margin: 0; font-size: 0.9em; opacity: 0.8;">
                Select sequence, interval, or variant analysis
            </p>
        </div>
        
        <div style="
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        ">
            <div style="font-size: 2em; margin-bottom: 10px;">3️⃣</div>
            <h4 style="margin: 0 0 10px 0;">Get Results</h4>
            <p style="margin: 0; font-size: 0.9em; opacity: 0.8;">
                View predictions and interactive visualizations
            </p>
        </div>
    </div>
    
    <div style="
        text-align: center;
        margin-top: 25px;
        padding-top: 20px;
        border-top: 1px solid rgba(255,255,255,0.2);
    ">
        <p style="margin: 0; font-size: 0.9em; opacity: 0.8;">
            💡 Type <strong>"help"</strong> for detailed instructions or try these examples:
        </p>
        <div style="margin-top: 15px; display: flex; flex-wrap: wrap; justify-content: center; gap: 10px;">
            <code style="background: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 5px; font-size: 0.8em;">
                sequence: ATCGATCG...
            </code>
            <code style="background: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 5px; font-size: 0.8em;">
                interval: chr22:1000-2000
            </code>
            <code style="background: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 5px; font-size: 0.8em;">
                variant: chr22:1000:A>T
            </code>
        </div>
    </div>
</div>
        """
    
    @staticmethod
    def create_progress_bar(progress: float, label: str = "") -> str:
        """Create an animated progress bar."""
        percentage = min(100, max(0, progress * 100))
        
        return f"""
<div style="margin: 20px 0;">
    {f'<p style="margin: 0 0 10px 0; font-weight: 500;">{label}</p>' if label else ''}
    <div style="
        background: #e0e0e0;
        border-radius: 10px;
        height: 20px;
        overflow: hidden;
        position: relative;
    ">
        <div style="
            background: linear-gradient(90deg, #1E88E5, #43A047);
            height: 100%;
            width: {percentage}%;
            border-radius: 10px;
            transition: width 0.3s ease;
            position: relative;
        ">
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                animation: shimmer 2s infinite;
            "></div>
        </div>
    </div>
    <p style="margin: 5px 0 0 0; text-align: right; font-size: 0.9em; color: #666;">
        {percentage:.1f}%
    </p>
</div>

<style>
@keyframes shimmer {{
    0% {{ transform: translateX(-100%); }}
    100% {{ transform: translateX(100%); }}
}}
</style>
        """


class MessageEnhancements:
    """Enhanced message formatting and styling."""
    
    @staticmethod
    async def send_enhanced_message(content: str, message_type: str = "info",
                                  author: str = "AlphaGenome", elements: List = None) -> cl.Message:
        """Send an enhanced message with styling and avatars."""

        # Create and send message without avatar for now (compatibility)
        message = cl.Message(
            content=content,
            author=author,
            elements=elements or []
        )

        await message.send()
        return message
    
    @staticmethod
    def format_genomic_data(data_type: str, data: Dict[str, Any]) -> str:
        """Format genomic data with enhanced styling."""
        
        if data_type == "sequence":
            return f"""
<div style="
    background: #f8f9fa;
    border: 2px solid #e9ecef;
    border-radius: 10px;
    padding: 20px;
    margin: 15px 0;
    font-family: 'Courier New', monospace;
">
    <h4 style="margin: 0 0 15px 0; color: #495057;">🧬 DNA Sequence</h4>
    <div style="
        background: white;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #28a745;
        word-break: break-all;
        line-height: 1.6;
    ">
        {data.get('sequence', 'N/A')}
    </div>
    <div style="margin-top: 10px; font-size: 0.9em; color: #6c757d;">
        Length: {len(data.get('sequence', ''))} bp
    </div>
</div>
            """
        
        elif data_type == "interval":
            return f"""
<div style="
    background: #fff3cd;
    border: 2px solid #ffeaa7;
    border-radius: 10px;
    padding: 20px;
    margin: 15px 0;
">
    <h4 style="margin: 0 0 15px 0; color: #856404;">📍 Genomic Interval</h4>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">
        <div>
            <strong>Chromosome:</strong><br>
            <code style="background: white; padding: 5px; border-radius: 3px;">{data.get('chromosome', 'N/A')}</code>
        </div>
        <div>
            <strong>Start:</strong><br>
            <code style="background: white; padding: 5px; border-radius: 3px;">{data.get('start', 'N/A'):,}</code>
        </div>
        <div>
            <strong>End:</strong><br>
            <code style="background: white; padding: 5px; border-radius: 3px;">{data.get('end', 'N/A'):,}</code>
        </div>
        <div>
            <strong>Width:</strong><br>
            <code style="background: white; padding: 5px; border-radius: 3px;">{data.get('width', 'N/A'):,} bp</code>
        </div>
    </div>
</div>
            """
        
        elif data_type == "variant":
            return f"""
<div style="
    background: #d1ecf1;
    border: 2px solid #bee5eb;
    border-radius: 10px;
    padding: 20px;
    margin: 15px 0;
">
    <h4 style="margin: 0 0 15px 0; color: #0c5460;">🧬 Genomic Variant</h4>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px;">
        <div>
            <strong>Chromosome:</strong><br>
            <code style="background: white; padding: 5px; border-radius: 3px;">{data.get('chromosome', 'N/A')}</code>
        </div>
        <div>
            <strong>Position:</strong><br>
            <code style="background: white; padding: 5px; border-radius: 3px;">{data.get('position', 'N/A'):,}</code>
        </div>
        <div>
            <strong>Reference:</strong><br>
            <code style="background: white; padding: 5px; border-radius: 3px;">{data.get('reference_bases', 'N/A')}</code>
        </div>
        <div>
            <strong>Alternate:</strong><br>
            <code style="background: white; padding: 5px; border-radius: 3px;">{data.get('alternate_bases', 'N/A')}</code>
        </div>
        <div>
            <strong>Type:</strong><br>
            <code style="background: white; padding: 5px; border-radius: 3px;">{data.get('variant_type', 'N/A')}</code>
        </div>
    </div>
</div>
            """
        
        return f"<pre>{data}</pre>"
