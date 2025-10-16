# 🧬 AlphaGenome Interactive UI

A comprehensive web-based interface for Google DeepMind's AlphaGenome genomic prediction model, built with Chainlit.

## 🌟 Features

### Core Functionality
- **DNA Sequence Analysis**: Predict genomic outputs from raw DNA sequences
- **Genomic Interval Prediction**: Analyze specific genomic regions
- **Variant Effect Analysis**: Compare reference vs alternate allele effects
- **Batch Processing**: Handle multiple inputs simultaneously
- **Interactive Visualizations**: Real-time plotting with AlphaGenome's visualization library

### Advanced Features
- **Input Validation**: Comprehensive validation for all genomic inputs
- **Multiple Output Types**: RNA-seq, ATAC-seq, ChIP-seq, contact maps, and more
- **Organism Support**: Human and mouse genome analysis
- **Ontology Filtering**: Filter predictions by specific tissue/cell types
- **Export Capabilities**: Download results and visualizations

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- AlphaGenome API key ([Get yours here](https://deepmind.google.com/science/alphagenome))

### Installation

1. **Clone and install AlphaGenome**:
   ```bash
   git clone https://github.com/google-deepmind/alphagenome.git
   cd alphagenome
   pip install -e .
   ```

2. **Install additional dependencies**:
   ```bash
   pip install chainlit
   ```

3. **Set up your API key**:
   ```bash
   export ALPHAGENOME_API_KEY=your_api_key_here
   ```

4. **Run the application**:
   ```bash
   python run_app.py
   ```

5. **Open your browser** to `http://localhost:8000`

### Alternative Launch Methods

**Direct Chainlit launch**:
```bash
chainlit run app.py --host 0.0.0.0 --port 8000
```

**Test the installation**:
```bash
python test_app.py
```

## 📖 Usage Guide

### Basic Commands

| Command | Description | Example |
|---------|-------------|---------|
| `setup` | Configure API key | `setup` |
| `help` | Show help information | `help` |
| `status` | Check current configuration | `status` |
| `examples` | Show example commands | `examples` |

### Prediction Commands

#### Sequence Prediction
```
predict sequence ATCGATCGATCGATCGATCGATCGATCGATCGATCG
```
- Analyzes DNA sequences up to 1M base pairs
- Supports A, C, G, T, N characters
- Provides multiple genomic output predictions

#### Interval Prediction
```
predict interval chr22:35677410-36725986
```
- Format: `chr:start-end`
- Coordinates are 0-based
- Maximum interval size: 1M base pairs

#### Variant Analysis
```
predict variant chr22:36201698:A>C
```
- Format: `chr:position:reference>alternate`
- Position is 1-based
- Compares reference vs alternate effects

### Advanced Features

#### Batch Processing
```
batch
```
- Process multiple sequences, intervals, or variants
- Paste multiple entries (one per line)
- Automatic input type detection

#### Advanced Options
```
advanced
```
- Custom organism selection
- Output type filtering
- Ontology term specification

## 🎯 Input Formats

### DNA Sequences
- **Valid characters**: A, C, G, T, N
- **Length**: 10 bp to 1,000,000 bp
- **Example**: `ATCGATCGATCGATCGATCG`

### Genomic Intervals
- **Format**: `chromosome:start-end`
- **Coordinates**: 0-based, end-exclusive
- **Size**: 100 bp to 1,000,000 bp
- **Examples**: 
  - `chr22:1000-2000`
  - `chr1:100000-200000`

### Genetic Variants
- **Format**: `chromosome:position:reference>alternate`
- **Position**: 1-based
- **Alleles**: A, C, G, T, N
- **Examples**:
  - `chr22:1000:A>T` (SNV)
  - `chr1:50000:ATG>C` (deletion)
  - `chr3:75000:G>TTT` (insertion)

## 📊 Output Types

AlphaGenome provides predictions for multiple genomic modalities:

| Output Type | Description |
|-------------|-------------|
| **RNA-seq** | Gene expression levels |
| **ATAC-seq** | Chromatin accessibility |
| **DNase-seq** | DNase I hypersensitive sites |
| **CAGE** | Cap analysis of gene expression |
| **ChIP-histone** | Histone modifications |
| **ChIP-TF** | Transcription factor binding |
| **Splice sites** | Splicing predictions |
| **Contact maps** | 3D chromatin organization |
| **ProCAP** | Promoter-centric analysis |

## 🔧 Configuration

### Environment Variables
- `ALPHAGENOME_API_KEY`: Your AlphaGenome API key
- `CHAINLIT_HOST`: Host address (default: 0.0.0.0)
- `CHAINLIT_PORT`: Port number (default: 8000)

### Configuration Files
- `.chainlit/config.toml`: Chainlit configuration
- `chainlit.md`: Welcome page content

## 🧪 Testing

Run the test suite to verify installation:
```bash
python test_app.py
```

The test suite validates:
- ✅ Module imports
- ✅ Input validation
- ✅ AlphaGenome data objects
- ✅ Visualization setup
- ✅ Application structure
- ✅ Core functionality

## 📁 Project Structure

```
alphagenome/
├── app.py                 # Main Chainlit application
├── ui_components.py       # UI components and utilities
├── run_app.py            # Application launcher
├── test_app.py           # Test suite
├── requirements.txt      # Python dependencies
├── chainlit.md          # Welcome page
├── .chainlit/
│   └── config.toml      # Chainlit configuration
└── README_UI.md         # This documentation
```

## 🔍 Troubleshooting

### Common Issues

**Import Error: No module named 'alphagenome'**
```bash
pip install -e .
```

**API Key Not Found**
```bash
export ALPHAGENOME_API_KEY=your_key_here
```

**Port Already in Use**
```bash
chainlit run app.py --port 8001
```

**Visualization Issues**
- Ensure matplotlib backend is set to 'Agg'
- Check that all visualization dependencies are installed

### Getting Help

1. Run `python test_app.py` to diagnose issues
2. Check the Chainlit logs for error messages
3. Verify your API key is valid
4. Ensure all dependencies are installed

## 🤝 Contributing

This UI is built on top of the AlphaGenome package. For issues related to:
- **UI functionality**: Create issues in this repository
- **AlphaGenome model**: Visit the [official AlphaGenome repository](https://github.com/google-deepmind/alphagenome)

## 📄 License

This UI application follows the same license as the AlphaGenome package (Apache 2.0).

## 🙏 Acknowledgments

- **Google DeepMind** for the AlphaGenome model
- **Chainlit** for the excellent UI framework
- **AlphaGenome team** for the comprehensive Python SDK

---

**Ready to explore the genome?** 🧬 Start the application and type `help` to get started!
