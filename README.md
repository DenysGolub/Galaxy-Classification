# Galaxy Classification

A Python-based project for classifying galaxy morphologies from images and interacting with an AI assistant through a Flask web app.

## Features

- Train and run galaxy morphology classifiers
- Classify galaxies from uploaded images or local files
- Store observations and predictions in a local SQLite database
- Use an Ollama-powered assistant for conversational help and database queries

## Project Structure

```text
galaxy-classification/
├── galaxy_classification/      # Core package for data loading, models, and training
├── webapp/                     # Flask application and UI routes
├── config/                     # Configuration files
├── data/                       # Dataset files
├── models/                     # Pretrained model weights
├── docs/                       # Additional documentation
├── notebooks/                  # Jupyter experiments
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project configuration
└── README.md                   # Project documentation
```

## Requirements

- Python 3.10+
- pip
- Ollama installed and running for the assistant chat features
- Optional: CUDA-enabled GPU for faster training

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd galaxy-classification
```

2. Create and activate a virtual environment:

```bash
# Windows (PowerShell)
python -m venv .galaxy_env
.\.galaxy_env\Scripts\Activate.ps1

# Linux / macOS
python -m venv .galaxy_env
source .galaxy_env/bin/activate
```

3. Install Python dependencies:

```bash
pip install -r requirements.txt
```

4. Prepare the dataset and model files:

- Place the dataset file `Galaxy10_DECals.h5` in the `data/` directory.
- Make sure the pretrained weights in `models/` are available. The app expects a compatible `.pth` file such as `models/efficient_net_0.8324.pth` by default.

## Assistant Models (Ollama)

The chat assistant uses Ollama models. These models must be pulled before running the web app:

```bash
ollama pull qwen3:8b
ollama pull sqlcoder:7b
```

If Ollama is not already running, start it with:

```bash
ollama serve
```

To verify that the models are installed:

```bash
ollama list
```

## Running the Web App

Start the Flask app from the project root:

```bash
python -m webapp.app
```

Then open the app in your browser at:

```text
http://127.0.0.1:5000/
```

## Training a Model

Run training with:

```bash
python -m galaxy_classification.training.train
```

## Notes

- The assistant chat feature calls the local Ollama API on port `11434`.
- If the required models are not downloaded, chat requests may fail.
- The web app uses a local SQLite database for storing observations and chat history.

## License

MIT License