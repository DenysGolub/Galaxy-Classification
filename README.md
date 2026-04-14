# Galaxy Classification

A deep learning project for classifying galaxy morphologies using convolutional neural networks.

## Project Structure

```
galaxy-classification/
├── galaxy_classification/          # Main package
│   ├── models/                     # Neural network models
│   │   ├── cnn.py                  # GalaxyCNN model
│   │   └── __init__.py
│   ├── data/                       # Data handling
│   │   ├── dataset.py              # Galaxy dataset
│   │   ├── loader.py               # Data loader
│   │   ├── transformed_subset.py   # Data transformations
│   │   └── __init__.py
│   ├── training/                   # Training and evaluation
│   │   ├── train.py                # Training logic
│   │   ├── evaluation.py           # Evaluation metrics
│   │   └── __init__.py
│   ├── database.py                 # Database operations
│   └── __init__.py
├── webapp/                         # Flask web application (refactored)
│   ├── app.py                      # Main Flask app (simplified)
│   ├── routes/                     # Route handlers
│   │   ├── __init__.py
│   │   ├── prediction.py           # Prediction endpoints
│   │   ├── legacy.py               # Legacy data endpoints
│   │   ├── observations.py         # Observation management
│   │   ├── stats.py                # Statistics and feedback
│   │   ├── chat.py                 # Chat functionality
│   │   └── health.py               # Health checks
│   ├── services/                   # Business logic services
│   │   ├── __init__.py
│   │   ├── prediction_service.py   # Prediction logic
│   │   ├── legacy_service.py       # Legacy data fetching
│   │   └── chat_service.py         # Chat AI logic
│   ├── templates/                  # HTML templates
│   └── static/                     # Static assets
├── config/                         # Configuration files
│   └── database_schema.sql         # Database schema
├── scripts/                        # Utility scripts
├── docs/                           # Documentation
├── data/                           # Dataset files
├── models/                         # Trained model weights
├── notebooks/                      # Jupyter notebooks
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Project configuration
└── README.md                       # This file
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd galaxy-classification
```

2. Create a virtual environment:
```bash
python -m venv .galaxy_env
.galaxy_env\Scripts\activate  # Windows
# or
source .galaxy_env/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Web Application

### Web Application

First, activate the virtual environment:
```bash
# Windows
.galaxy_env\Scripts\activate
# Linux/Mac
source .galaxy_env/bin/activate
```

Run the Flask web application:
```bash
# From project root (recommended)
python -m webapp.app

# Or from webapp directory
cd webapp
python app.py

# Or after installation: galaxy-web
```

The web application is now organized into:
- **Routes**: Separate files for different API endpoints
- **Services**: Business logic separated from HTTP handling
- **Main App**: Clean initialization and route registration

### Training

Train the model:
```bash
python -m galaxy_classification.training.train
```

### API

The web app provides REST endpoints for:
- Galaxy classification predictions
- Observation management
- Chat with AI assistant

## Dataset

The project uses the Galaxy10 DECals dataset. Place the dataset file `Galaxy10_DECals.h5` in the `data/` directory.

## Models

Trained model weights are stored in the `models/` directory.

## License

MIT License