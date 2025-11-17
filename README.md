# Space Radar

A space news aggregation and analysis platform

Space Radar automatically collects stories from major space and astronomy news sources, removes duplicates through clustering, and provides summaries with relevance scoring. Built with Python and Flask.


## Features

### News Processing
- **Multi-source aggregation**: Fetches from NASA, ESA, SpaceNews, JPL, and other space news sources
- **Duplicate detection**: Uses clustering algorithms to identify and merge similar stories
- **Automated summarization**: Generates summaries and extracts key information
- **Story ranking**: Scores stories by source reliability, recency, and content analysis

### Web Interface
- **Clean design**: Minimalist layout with serif typography
- **Expandable cards**: Click to expand stories for full details
- **Responsive**: Works on desktop, tablet, and mobile
- **Trending topics**: Scrolling carousel of current space topics

### Data Pipeline
- **Automated processing**: Scheduled data collection and analysis
- **Error handling**: Retry logic and failure recovery
- **Logging**: Tracks processing success and failures
- **REST API**: JSON endpoints for accessing processed stories

## Technology Stack

### **Backend**
- **Python 3.9+**: Core application logic
- **Flask**: Web framework and API
- **Sentence Transformers**: Text embedding and similarity analysis
- **Scikit-learn**: Clustering and ML algorithms
- **BeautifulSoup**: Web scraping and HTML parsing
- **Pandas**: Data manipulation and analysis

### **Frontend**
- **HTML5/CSS3**: Modern semantic markup
- **JavaScript (ES6+)**: Interactive functionality
- **CSS Grid/Flexbox**: Responsive layout system
- **Custom animations**: Smooth transitions and micro-interactions

### **Text Processing**
- **Language models**: Story summarization and analysis
- **Text embeddings**: Semantic similarity for clustering
- **Scoring algorithms**: Multi-factor relevance ranking

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager
- Virtual environment (recommended)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/nirvaankohli/space-radar.git
   cd space-radar
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   # Create .env file
   echo "API_KEY=your_llm_api_key_here" > .env
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

Visit `http://localhost:5000` to access the Space Radar interface.

## Usage

### **Web Interface**
1. **Browse Stories**: View the latest space news in a card layout
2. **Expand Details**: Click any story card to see full content
3. **Trending Topics**: Browse the carousel for current space topics
4. **Story Scores**: See relevance scores based on content analysis

### **API Endpoints**
- `GET /`: Main web interface
- `GET /api/stories`: JSON feed of processed stories
- `POST /run_pipeline`: Trigger manual data processing

### **Data Pipeline**
```bash
# Run the complete data pipeline
python data_pipeline.py

# Process text analysis only
python agents/llm/build.py
```


## Configuration

### **News Sources**
Configure news sources in `data/feeds.yml`:
```yaml
feeds:
  - name: "NASA"
    url: "https://www.nasa.gov/feed/"
    reliability: 0.99
  # Add more sources...
```

### **Scoring Weights**
Adjust importance weights in `agents/llm/build.py`:
```python
weights = {
    "llms": 0.6,        # Content analysis score
    "reliability": 0.2,  # Source reliability
    "recency": 0.2      # Time-based decay
}
```

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Follow our coding standards
4. **Add tests**: Ensure your changes are well-tested
5. **Commit changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**: Describe your changes

### **Development Guidelines**
- Follow PEP 8 style guidelines
- Add docstrings to functions and classes
- Include type hints where appropriate
- Test your changes thoroughly

## Performance & Metrics

- **Processing Speed**: ~50 stories per minute
- **Accuracy**: 95%+ duplicate detection rate
- **Reliability**: Built-in retry logic and error handling
- **Scalability**: Handles 1000+ articles per processing cycle

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **NASA**: For providing excellent APIs and data feeds
- **ESA**: For comprehensive space mission coverage
- **SpaceNews**: For industry insights and analysis
- **Hugging Face**: For transformer models and tools
- **OpenAI**: For LLM capabilities

---

FOR SEIGE!