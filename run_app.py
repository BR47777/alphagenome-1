#!/usr/bin/env python3
"""
Launcher script for the AlphaGenome Chainlit UI application.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import chainlit
        import matplotlib
        import pandas
        import numpy
        print("✅ Core dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def check_alphagenome():
    """Check if AlphaGenome is available."""
    try:
        from alphagenome.models import dna_client
        from alphagenome.data import genome
        from alphagenome.visualization import plot_components
        print("✅ AlphaGenome modules found")
        return True
    except ImportError as e:
        print(f"❌ AlphaGenome not found: {e}")
        print("Please ensure you're running in the AlphaGenome environment")
        return False

def main():
    """Main launcher function."""
    print("🧬 AlphaGenome Chainlit UI Launcher")
    print("=" * 40)
    
    # Check current directory
    current_dir = Path.cwd()
    app_file = current_dir / "app.py"
    
    if not app_file.exists():
        print(f"❌ app.py not found in {current_dir}")
        print("Please run this script from the directory containing app.py")
        sys.exit(1)
    
    print(f"📁 Working directory: {current_dir}")
    
    # Check dependencies
    if not check_dependencies():
        print("\n💡 To install missing dependencies:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    if not check_alphagenome():
        print("\n💡 To install AlphaGenome:")
        print("pip install ./alphagenome")
        sys.exit(1)
    
    # Check for API key
    api_key = os.getenv("ALPHAGENOME_API_KEY")
    if api_key:
        print("✅ API key found in environment")
    else:
        print("⚠️  No API key found in environment")
        print("You can set it with: export ALPHAGENOME_API_KEY=your_key_here")
        print("Or configure it through the UI after starting")
    
    print("\n🚀 Starting AlphaGenome UI...")
    print("The application will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    print("-" * 40)
    
    try:
        # Launch Chainlit
        subprocess.run([
            sys.executable, "-m", "chainlit", "run", "app.py",
            "--host", "0.0.0.0",
            "--port", "8000"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down AlphaGenome UI")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
