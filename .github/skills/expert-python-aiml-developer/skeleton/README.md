# Skeleton Project Structure

This folder contains a **COMPLETE PROJECT STRUCTURE** that serves as the **GOLDEN STANDARD** for all Python AI/ML projects. It demonstrates the exact folder organization, file structure, and code patterns that should be followed.

## 📁 Project Structure

```
skeleton/
├── pyproject.toml              # Dependency management with all tools configured
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore patterns for ML projects
├── Dockerfile                  # Container definition for deployment
├── README.md                   # This documentation
│
├── configs/                    # Configuration files (YAML)
│   ├── model_config.yaml       # Model hyperparameters
│   ├── training_config.yaml    # Training settings
│   └── inference_config.yaml   # Inference settings
│
├── src/                        # Source code
│   ├── __init__.py
│   ├── config/                 # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py         # Pydantic settings classes
│   ├── data/                   # Data loading & preprocessing
│   │   ├── __init__.py
│   │   ├── loaders.py          # Data loading utilities
│   │   └── preprocessors.py    # Transforms & normalization
│   ├── models/                 # Model definitions
│   │   ├── __init__.py
│   │   ├── base.py             # Base model interface
│   │   └── losses.py           # Custom loss functions
│   ├── api/                    # FastAPI service
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI application
│   │   └── routes/             # API endpoints
│   │       ├── __init__.py
│   │       ├── health.py       # Health check routes
│   │       └── predictions.py  # Prediction routes
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── logging.py          # Logging configuration
│       └── reproducibility.py  # Seed & environment logging
│
├── scripts/                    # CLI scripts
│   ├── train.py                # Training entrypoint
│   └── evaluate.py             # Evaluation script
│
├── tests/                      # Test suite
│   ├── __init__.py
│   └── conftest.py             # Pytest fixtures
│
└── [Template Files]            # Standalone templates for reference
    ├── trainer_template.py         # Training loop template
    ├── predictor_template.py       # Inference service template
    ├── image_classifier_template.py # Image classification
    ├── object_detector_template.py  # Object detection
    └── augmentation_template.py     # Data augmentation
```

## 📋 Key Files Explained

### Configuration (`src/config/settings.py`)
Production-ready Pydantic settings with:
- `AppSettings` - Application-level configuration
- `ModelSettings` - Model hyperparameters
- `TrainingSettings` - Training configuration
- `InferenceSettings` - Inference configuration
- `APISettings` - API server settings
- Cached getters with `@lru_cache`

### Data Loading (`src/data/`)
- **loaders.py**: Image loading, path collection, train/val split
- **preprocessors.py**: Transforms, normalization (ImageNet constants)

### Models (`src/models/`)
- **base.py**: Abstract base model with common methods
- **losses.py**: FocalLoss, LabelSmoothingLoss

### API (`src/api/`)
- **main.py**: FastAPI app with lifespan, CORS, routers
- **routes/health.py**: `/health` and `/ready` endpoints
- **routes/predictions.py**: Prediction endpoint with Pydantic schemas

### Utilities (`src/utils/`)
- **logging.py**: Structured logging setup
- **reproducibility.py**: `set_seed()` and `log_environment()`

## 🚀 Quick Start

### 1. Copy skeleton to your project
```bash
cp -r skeleton/* my_project/
cd my_project
```

### 2. Setup environment
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[dev]"
cp .env.example .env
```

### 3. Train a model
```bash
python scripts/train.py --config configs/training_config.yaml
```

### 4. Start API server
```bash
uvicorn src.api.main:app --reload
```

### 5. Run tests
```bash
pytest tests/ -v
```

## 📦 Standalone Templates

These template files demonstrate specific patterns and can be used as reference:

| Template | Purpose |
|----------|---------|
| `trainer_template.py` | Training loop with mixed precision, checkpointing, early stopping |
| `predictor_template.py` | Thread-safe inference with batch support |
| `image_classifier_template.py` | Image classification with timm |
| `object_detector_template.py` | Object detection with YOLO |
| `augmentation_template.py` | Data augmentation with Albumentations |

## ✅ Best Practices Demonstrated

1. **Type Hints**: All functions have complete type annotations
2. **Docstrings**: Google-style docstrings on all public functions
3. **Error Handling**: Comprehensive exception handling with context
4. **Logging**: Structured logging instead of print statements
5. **Configuration**: Pydantic settings for validated configuration
6. **Reproducibility**: Seed management and environment tracking
7. **Separation of Concerns**: Clear module boundaries
8. **Testability**: Fixtures and test structure ready
