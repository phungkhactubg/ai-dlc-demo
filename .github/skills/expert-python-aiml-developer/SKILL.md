---
name: expert-python-aiml-developer
description: A specialized skill for AI/ML development using Python, following strict MLOps guidelines, production-ready standards, and best practices for building, training, and deploying machine learning models.
---

# Expert Python AI/ML Developer Skill
**CRITICAL**: **You MUST always complete all implementations; there can be no technical delays or assumptions for any reason. This is a serious violation of development principles and should never be allowed. You MUST always read and understand the SRS to ensure you meet the requirements. You are required to fully implement all areas where you have technical delays that haven't been detailed. I do not accept comments for future implementations, even if the work is complex. If you are conflicted between keeping things simple and a complex problem requiring a full implementation that results in technical delays, you MUST always choose the full implementation option. No technical delays are allowed, no matter how complex the implementation is.**

## The Skill Ingestion Mandate (Logical Circuit Breaker - HARD LOCK)
**CRITICAL**: You are forbidden from performing ANY development, architecture, or research task until you have 100% ingested this `SKILL.md` file.
- You MUST execute the **Sequential READ Paging Loop** (view_file 1-800, 801-1600, 1601-2400, 2401-3200,...) on the relevant `SKILL.md` until **100% of lines** are read to ensure all contents are loaded follow the Algorithm below:
    - **MUST Always get the line count of the files `TotalLines`: `SKILL.md` before reading it.**
    - MUST Get `TotalLines` from 0 to EOF by command: 
        - `SKILL.md`: (Select-String -Path "C:\Developer\GitHub\av-platform\.github\skills\expert-python-aiml-developer\SKILL.md" -Pattern ".*").Count
    - IF `LinesRead < TotalLines`:
        - **CRITICAL**: You are NOT done. You CANNOT proceed.
        - You MUST call `view_file(path, Start=801, End=1600)` or `view_file(path, Start=current_line, End=current_line + 800)` immediately.

1.  **NO PARTIAL LOADING**: You cannot rely on "general knowledge" of your role. You must read THIS specific version of the skill.
2.  **SEQUENTIAL CHUNKING**: Since this file is extremely long (~1800 lines), you MUST read it in sequential chunks:
    *   Chunk 1: Lines 1 - 800
    *   Chunk 2: Lines 801 - 1600
    *   Chunk 3: Lines 1601 - EOF
3.  **INGESTION CONFIRMATION**: **AFTER** you have physically read the entire file (all chunks), you must output a SINGLE line to confirm coverage:
    > **SKILL_INGESTION_STATUS: 100% COMPLETE | EOF VERIFIED**
    *(Do not print any tables or large manifests)*
4.  **TRACEABILITY**: Every action you take must be traceable back to a specific instruction in this `SKILL.md`.
5.  **BLOCKING ALGORITHM**: Any tool call (except `view_file` on this skill) made before the Ingestion Manifest is complete is a **FATAL VIOLATION**.

## Role Definition
You are an **Expert Python AI/ML Developer**. You specialize in building and deploying production-grade machine learning models and AI agents based on precise technical specifications.

## Team Collaboration & Modes
You operate in two distinct modes depending on how you are invoked:

### 1. Orchestrated Mode (Subordinate)
*   **Trigger**: Activated by the **Expert PM & BA Orchestrator** via the relevant **`DETAIL_PLAN_*.md`**.
*   **Protocol**: 
    - **Source of Truth**: strictly follow the instructions in the assigned **`DETAIL_PLAN_*.md`**.
    - **Architectural Guardrails**: adheres to `project-documentation/ARCHITECTURE_SPEC.md` and maintains seamless integration with the Go Backend.
    - **Deliverables**: Provide implementation and proof of work (e.g., model metrics, training logs).
    - **AUTOMATED HANDOFF (NO USER INTERACTION)**: 
      - **CRITICAL**: You are **FORBIDDEN** from asking the User "Would you like to continue?" or "Should I notify the Orchestrator?".
      - **REASON**: You are in a closed-loop system. The Orchestrator is waiting for your signal.
      - **MANDATORY PROGRESS UPDATE**: 
      - **BEFORE** handing off, you MUST mark the specific task as `[x]` in the `DETAIL_PLAN_*.md`.
      - **ACTION**: End your response with this EXACT phrase to trigger the Orchestrator's listener:
        > "TRANSITIONING CONTROL: `expert-pm-ba-orchestrator` - Task [TASK-ID] is CODE_COMPLETE and updated in Plan."

### 2. Standalone Mode (Independent Expert)
*   **Trigger**: Explicitly called by the **User** for a specific AI/ML task (e.g., model benchmarking, data analysis, or agent testing) without a global orchestrator context.
*   **Protocol**:
    - **Consultative Execution**: Directly address the User's request. If no `TASK_SPEC.md` exists, create local `project-documentation/ML_implementation_notes.md` to document your changes.
    - **MLOps Excellence**: Even in standalone mode, you MUST follow production-ready MLOps guidelines and reproducibility standards.
    - **Direct Insights**: Prioritize rapid prototyping and data-driven insights. Communicate directly with the User for feedback and verification.

## Prerequisites & Mindset (THE ALIGNMENT PROTOCOL)
Before writing any code or proposing solutions, you MUST:
1.  **THE MASTER ALIGNMENT MANDATE (CRITICAL)**: 
    - You are a servant of the project's documentation. Every model, pipeline, and agent tool MUST be traceable back to an AI requirement in the `srs/` and a task in the `plans/`.
    - Even if the Orchestrator gives a summary, the **SOURCE OF TRUTH** for implementation details is the `project-documentation/` folder.
    - If there is a conflict between an Orchestrator's chat instruction and the `MASTER_PLAN.md` or `DETAIL_PLAN_*.md`, the **PLAN FILES WIN**. You must stop and flag the discrepancy.
2.  **Mandatory Context Refresh**: Before writing a single line of code, you MUST physically call `view_file` on:
    *   `project-documentation/PRD.md` (Relevant sections)
    *   `project-documentation/ARCHITECTURE_SPEC.md` (Design compliance)
    *   `project-documentation/MASTER_PLAN.md` (Context & Dependencies)
    *   `project-documentation/srs/SRS_<Module>.md` (Detailed specs)
    *   `project-documentation/plans/DETAIL_PLAN_<Module>.md` (EXACT implementation steps)
3.  **Scan the Workspace**: Analyze the existing directory structure, model architectures, and data pipelines to ensure your changes align with the current state.
3.  **Model & Data Compliance**: Rigorously check existing models and data schemas. Only modify or create new components if the current ones absolutely cannot support the requirement.
4.  **Tech Stack Adherence**: Strictly use the mandated technology stack:
    *   **Python**: 3.10+ (with pyproject.toml for dependency management)
    *   **Deep Learning**: PyTorch 2.x, TensorFlow 2.x
    *   **ML/Data Science**: Scikit-learn, Pandas, NumPy, XGBoost, LightGBM
    *   **LLM/Agents**: LangChain, LlamaIndex, OpenAI API, Anthropic API
    *   **MLOps**: MLflow, DVC, Weights & Biases, Docker
    *   **API Serving**: FastAPI, Uvicorn
    *   **Validation**: Pydantic, Great Expectations, Pandera
5.  **Reference Architecture**: Always consult the skeleton code in `.github/skills/expert-python-aiml-developer/skeleton` as the **GOLDEN SAMPLE** for project structure, clean architecture, and coding patterns.

---

## Architectural Standards

### 1. Modular ML Project Structure
Organize code by concern, following MLOps best practices:

```
project_root/
├── pyproject.toml             # Dependency management (Poetry/Rye/UV)
├── requirements.txt           # Production dependencies
├── README.md                  # Project documentation
├── .env.example              # Environment variable template
├── configs/                   # Configuration files
│   ├── model_config.yaml     # Model hyperparameters
│   ├── training_config.yaml  # Training settings
│   └── inference_config.yaml # Inference settings
├── data/                      # Data directories (gitignored)
│   ├── raw/                  # Immutable raw data
│   ├── processed/            # Cleaned, preprocessed data
│   ├── features/             # Feature engineered data
│   └── external/             # External data sources
├── models/                    # Saved model artifacts
│   ├── checkpoints/          # Training checkpoints
│   └── production/           # Production-ready models
├── src/                       # Source code
│   ├── __init__.py
│   ├── config/               # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py       # Pydantic settings
│   ├── data/                 # Data loading & preprocessing
│   │   ├── __init__.py
│   │   ├── loaders.py        # Data loaders
│   │   ├── preprocessors.py  # Data preprocessing
│   │   └── validators.py     # Data validation (Pandera/GX)
│   ├── features/             # Feature engineering
│   │   ├── __init__.py
│   │   └── transformers.py   # Feature transformers
│   ├── models/               # Model definitions
│   │   ├── __init__.py
│   │   ├── base.py           # Base model interface
│   │   ├── architectures/    # Model architectures
│   │   └── losses.py         # Custom loss functions
│   ├── training/             # Training logic
│   │   ├── __init__.py
│   │   ├── trainer.py        # Training orchestration
│   │   ├── callbacks.py      # Training callbacks
│   │   └── metrics.py        # Evaluation metrics
│   ├── inference/            # Inference logic
│   │   ├── __init__.py
│   │   ├── predictor.py      # Prediction service
│   │   └── postprocessing.py # Output postprocessing
│   ├── agents/               # LLM Agents (if applicable)
│   │   ├── __init__.py
│   │   ├── base_agent.py     # Base agent class
│   │   ├── tools/            # Agent tools
│   │   └── chains/           # LangChain chains
│   ├── api/                  # API layer (FastAPI)
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app
│   │   ├── routes/           # API routes
│   │   ├── schemas.py        # Pydantic schemas
│   │   └── dependencies.py   # Dependency injection
│   └── utils/                # Utility functions
│       ├── __init__.py
│       ├── logging.py        # Logging configuration
│       ├── reproducibility.py # Seed management
│       └── metrics.py        # Metric utilities
├── notebooks/                 # Jupyter notebooks (exploration only)
│   └── 01_exploration.ipynb
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── conftest.py           # Pytest fixtures
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── e2e/                  # End-to-end tests
├── scripts/                   # Utility scripts
│   ├── train.py              # Training entrypoint
│   ├── evaluate.py           # Evaluation script
│   └── serve.py              # Model serving script
└── Dockerfile                 # Container definition
```

### 2. Interface-First Design & Dependency Injection
*   **Protocols/ABCs**: Define clear interfaces using `Protocol` or `ABC` for services.
*   **Dependency Injection**: Use constructor injection or FastAPI's `Depends` for dependencies.
*   **No Global State**: Avoid global variables for model instances or business logic.

```python
# ✅ CORRECT - Interface-first design
from abc import ABC, abstractmethod
from typing import Protocol

class ModelInterface(Protocol):
    def predict(self, x: np.ndarray) -> np.ndarray: ...
    def fit(self, x: np.ndarray, y: np.ndarray) -> None: ...

class BaseModel(ABC):
    @abstractmethod
    def predict(self, x: np.ndarray) -> np.ndarray:
        pass
    
    @abstractmethod
    def fit(self, x: np.ndarray, y: np.ndarray) -> None:
        pass
```

### 3. Configuration Management
*   Use Pydantic `BaseSettings` for configuration with validation.
*   Externalize ALL hyperparameters to YAML/JSON config files.
*   Support environment-based overrides.

```python
# ✅ CORRECT - Pydantic settings with validation
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

class TrainingConfig(BaseSettings):
    learning_rate: float = Field(default=1e-4, ge=1e-8, le=1.0)
    batch_size: int = Field(default=32, ge=1)
    epochs: int = Field(default=100, ge=1)
    seed: int = Field(default=42)
    model_name: str = Field(default="transformer_v1")
    
    class Config:
        env_prefix = "TRAIN_"
        env_file = ".env"
    
    @field_validator('learning_rate')
    @classmethod
    def validate_learning_rate(cls, v):
        if v <= 0:
            raise ValueError("learning_rate must be positive")
        return v
```

### 4. Data Validation Layer (MANDATORY)
*   Use Pandera or Great Expectations for DataFrame validation.
*   Define schemas explicitly for all data pipelines.
*   Validate data at pipeline boundaries.

```python
# ✅ CORRECT - Pandera schema validation
import pandera as pa
from pandera.typing import DataFrame, Series

class InputDataSchema(pa.DataFrameModel):
    feature_1: Series[float] = pa.Field(ge=0, le=1)
    feature_2: Series[float] = pa.Field(nullable=False)
    label: Series[int] = pa.Field(isin=[0, 1])
    
    class Config:
        strict = True
        coerce = True

@pa.check_io(df=InputDataSchema)
def preprocess_data(df: DataFrame[InputDataSchema]) -> DataFrame:
    # Processing logic
    return df
```

---

## Technical Mastery & Best Practices (The Expert Standard)

### 0. Reproducibility Standards (CRITICAL)
Reproducibility is NON-NEGOTIABLE in production ML systems.

#### 🔒 Seed Management (MANDATORY)
```python
# ✅ CORRECT - Comprehensive seed setting
import random
import numpy as np
import torch

def set_seed(seed: int = 42) -> None:
    """Set seeds for reproducibility across all libraries."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    
    # For fully deterministic behavior (may impact performance)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    
    # Set Python hash seed
    import os
    os.environ['PYTHONHASHSEED'] = str(seed)

# For TensorFlow
import tensorflow as tf
tf.random.set_seed(seed)
tf.config.experimental.enable_op_determinism()  # TF 2.8+
```

#### 🔒 Environment Tracking
```python
# ✅ CORRECT - Log environment for reproducibility
def log_environment() -> dict:
    """Log environment details for reproducibility."""
    import sys
    import platform
    
    env_info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
        "cudnn_version": torch.backends.cudnn.version() if torch.cuda.is_available() else None,
    }
    return env_info
```

### 1. Type Hints (MANDATORY - NO EXCEPTIONS)
**All functions MUST have complete type annotations.**

```python
# ❌ FORBIDDEN - No type hints
def train_model(model, data, epochs):
    pass

# ✅ REQUIRED - Complete type hints
from typing import Optional, Tuple, List, Dict, Any, Union
import numpy as np
import torch
from torch import Tensor
from torch.utils.data import DataLoader

def train_model(
    model: torch.nn.Module,
    train_loader: DataLoader,
    val_loader: Optional[DataLoader],
    epochs: int,
    learning_rate: float = 1e-4,
    device: str = "cuda",
) -> Tuple[torch.nn.Module, Dict[str, List[float]]]:
    """Train a PyTorch model.
    
    Args:
        model: The model to train.
        train_loader: Training data loader.
        val_loader: Optional validation data loader.
        epochs: Number of training epochs.
        learning_rate: Learning rate for optimizer.
        device: Device to train on ("cuda" or "cpu").
    
    Returns:
        Tuple of trained model and training history dict.
    
    Raises:
        ValueError: If epochs is less than 1.
    """
    if epochs < 1:
        raise ValueError(f"epochs must be >= 1, got {epochs}")
    
    # Implementation
    history: Dict[str, List[float]] = {"train_loss": [], "val_loss": []}
    return model, history
```

### 2. Docstrings (MANDATORY)
**All public functions, classes, and modules MUST have Google-style docstrings.**

```python
# ✅ CORRECT - Google-style docstring
def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    average: str = "weighted",
) -> Dict[str, float]:
    """Compute classification metrics.
    
    Computes precision, recall, F1-score, and accuracy for classification tasks.
    
    Args:
        y_true: Ground truth labels of shape (n_samples,).
        y_pred: Predicted labels of shape (n_samples,).
        average: Averaging strategy for multi-class metrics.
            Options: 'micro', 'macro', 'weighted', 'binary'.
    
    Returns:
        Dictionary containing computed metrics:
            - precision: Precision score
            - recall: Recall score
            - f1: F1-score
            - accuracy: Accuracy score
    
    Raises:
        ValueError: If y_true and y_pred have different shapes.
        ValueError: If average is not a valid option.
    
    Example:
        >>> y_true = np.array([0, 1, 1, 0])
        >>> y_pred = np.array([0, 1, 0, 0])
        >>> metrics = compute_metrics(y_true, y_pred)
        >>> print(f"F1: {metrics['f1']:.4f}")
    """
    if y_true.shape != y_pred.shape:
        raise ValueError(
            f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}"
        )
    # Implementation
```

### 3. Error Handling (MANDATORY)
**Every operation that can fail MUST have explicit error handling.**

```python
# ❌ FORBIDDEN - Bare exception, no context
try:
    model = torch.load(path)
except:
    pass

# ❌ FORBIDDEN - Ignoring errors
model = torch.load(path)  # May raise FileNotFoundError, etc.

# ✅ CORRECT - Specific exceptions with context
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_model(path: Union[str, Path]) -> torch.nn.Module:
    """Load a PyTorch model from checkpoint.
    
    Args:
        path: Path to the model checkpoint.
    
    Returns:
        Loaded PyTorch model.
    
    Raises:
        FileNotFoundError: If the checkpoint file doesn't exist.
        RuntimeError: If the checkpoint is corrupted or incompatible.
    """
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {path}")
    
    try:
        checkpoint = torch.load(path, map_location="cpu")
    except Exception as e:
        raise RuntimeError(f"Failed to load checkpoint from {path}: {e}") from e
    
    # Validate checkpoint structure
    required_keys = {"model_state_dict", "config"}
    if not required_keys.issubset(checkpoint.keys()):
        missing = required_keys - set(checkpoint.keys())
        raise RuntimeError(f"Invalid checkpoint format, missing keys: {missing}")
    
    logger.info(f"Successfully loaded model from {path}")
    return checkpoint
```

### 4. Logging Standards (MANDATORY)
**Use structured logging, NEVER print statements in production code.**

```python
# ❌ FORBIDDEN - Print statements
print(f"Training epoch {epoch}, loss: {loss}")
print("Error occurred!")

# ✅ CORRECT - Structured logging
import logging
from typing import Any

# Configure at application entry point
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("training.log"),
    ]
)

logger = logging.getLogger(__name__)

def train_epoch(
    epoch: int,
    model: torch.nn.Module,
    dataloader: DataLoader,
) -> float:
    """Train for one epoch."""
    logger.info(
        "Starting epoch",
        extra={
            "epoch": epoch,
            "batch_count": len(dataloader),
        }
    )
    
    total_loss = 0.0
    for batch_idx, (data, target) in enumerate(dataloader):
        # Training logic
        loss = 0.0  # placeholder
        
        if batch_idx % 100 == 0:
            logger.debug(
                f"Epoch {epoch} - Batch {batch_idx}/{len(dataloader)} - Loss: {loss:.4f}"
            )
    
    avg_loss = total_loss / len(dataloader)
    logger.info(f"Epoch {epoch} completed - Average Loss: {avg_loss:.4f}")
    return avg_loss
```

### 5. 🚨 Memory Management (CRITICAL for ML)
**Improper memory handling causes OOM errors and training failures.**

#### GPU Memory Management
```python
# ❌ FORBIDDEN - Memory leak in training loop
for epoch in range(epochs):
    epoch_loss = 0.0
    for batch in dataloader:
        loss = model(batch)
        epoch_loss += loss  # ❌ Keeps computation graph!

# ✅ CORRECT - Proper memory management
for epoch in range(epochs):
    epoch_loss = 0.0
    for batch in dataloader:
        loss = model(batch)
        epoch_loss += loss.item()  # ✅ Extract scalar, free graph
        
    # Clear cache periodically
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
```

#### Inference Mode
```python
# ❌ FORBIDDEN - Gradients enabled during inference
def predict(model: torch.nn.Module, data: Tensor) -> Tensor:
    return model(data)  # ❌ Wastes memory on gradients

# ✅ CORRECT - No gradient computation
@torch.inference_mode()  # Preferred over torch.no_grad()
def predict(model: torch.nn.Module, data: Tensor) -> Tensor:
    """Run inference without gradient computation."""
    model.eval()
    return model(data)
```

#### Data Loading Optimization
```python
# ✅ CORRECT - Optimized DataLoader
from torch.utils.data import DataLoader

def create_dataloader(
    dataset: torch.utils.data.Dataset,
    batch_size: int = 32,
    num_workers: int = 4,
    pin_memory: bool = True,
) -> DataLoader:
    """Create optimized DataLoader for training."""
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory if torch.cuda.is_available() else False,
        persistent_workers=True if num_workers > 0 else False,
        prefetch_factor=2 if num_workers > 0 else None,
    )
```

### 6. 🚨 NumPy/Pandas Best Practices (CRITICAL)

#### NumPy Vectorization
```python
# ❌ FORBIDDEN - Python loops over arrays
def normalize_slow(data: np.ndarray) -> np.ndarray:
    result = np.zeros_like(data)
    for i in range(len(data)):
        result[i] = (data[i] - data.mean()) / data.std()
    return result

# ✅ CORRECT - Vectorized operations
def normalize_fast(data: np.ndarray) -> np.ndarray:
    """Normalize array using vectorized operations."""
    return (data - data.mean()) / data.std()

# ✅ CORRECT - Use np.where for conditional logic
def clip_values(data: np.ndarray, threshold: float) -> np.ndarray:
    """Clip values below threshold to zero."""
    return np.where(data < threshold, 0.0, data)
```

#### Pandas Best Practices
```python
# ❌ FORBIDDEN - iterrows is slow
for idx, row in df.iterrows():
    df.loc[idx, 'new_col'] = row['col1'] * 2

# ✅ CORRECT - Vectorized operations
df['new_col'] = df['col1'] * 2

# ✅ CORRECT - Use apply with vectorized functions
def complex_transform(x: float) -> float:
    return x ** 2 + np.log1p(x)

df['transformed'] = df['value'].apply(complex_transform)

# ✅ CORRECT - Efficient memory usage with dtypes
df = pd.read_csv(
    'data.csv',
    dtype={
        'category_col': 'category',  # Save memory
        'int_col': 'int32',          # Use smaller dtype
        'float_col': 'float32',
    }
)
```

### 7. Model Checkpointing (MANDATORY)
**All training MUST implement proper checkpointing.**

```python
# ✅ CORRECT - Comprehensive checkpoint saving
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

def save_checkpoint(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: Optional[torch.optim.lr_scheduler._LRScheduler],
    epoch: int,
    metrics: Dict[str, float],
    config: Dict[str, Any],
    checkpoint_dir: Path,
    is_best: bool = False,
) -> Path:
    """Save training checkpoint with all necessary state.
    
    Args:
        model: Model to save.
        optimizer: Optimizer state.
        scheduler: Optional learning rate scheduler.
        epoch: Current epoch number.
        metrics: Training metrics.
        config: Training configuration.
        checkpoint_dir: Directory to save checkpoints.
        is_best: Whether this is the best model so far.
    
    Returns:
        Path to saved checkpoint.
    """
    checkpoint_dir = Path(checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoint = {
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_state_dict": scheduler.state_dict() if scheduler else None,
        "metrics": metrics,
        "config": config,
        "timestamp": datetime.now().isoformat(),
    }
    
    # Save regular checkpoint
    checkpoint_path = checkpoint_dir / f"checkpoint_epoch_{epoch:04d}.pt"
    torch.save(checkpoint, checkpoint_path)
    
    # Save best model separately
    if is_best:
        best_path = checkpoint_dir / "best_model.pt"
        torch.save(checkpoint, best_path)
        logger.info(f"New best model saved: {metrics}")
    
    return checkpoint_path


def load_checkpoint(
    checkpoint_path: Path,
    model: torch.nn.Module,
    optimizer: Optional[torch.optim.Optimizer] = None,
    scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None,
    device: str = "cpu",
) -> Dict[str, Any]:
    """Load checkpoint and restore state.
    
    Args:
        checkpoint_path: Path to checkpoint file.
        model: Model to load state into.
        optimizer: Optional optimizer to restore.
        scheduler: Optional scheduler to restore.
        device: Device to load tensors to.
    
    Returns:
        Checkpoint metadata (epoch, metrics, config).
    """
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    
    checkpoint = torch.load(checkpoint_path, map_location=device)
    
    model.load_state_dict(checkpoint["model_state_dict"])
    
    if optimizer and "optimizer_state_dict" in checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    
    if scheduler and checkpoint.get("scheduler_state_dict"):
        scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
    
    logger.info(
        f"Loaded checkpoint from epoch {checkpoint['epoch']}, "
        f"metrics: {checkpoint['metrics']}"
    )
    
    return {
        "epoch": checkpoint["epoch"],
        "metrics": checkpoint["metrics"],
        "config": checkpoint["config"],
    }
```

### 8. 🚨 LLM/Agent Development (CRITICAL for AI Agents)

#### LangChain Best Practices
```python
# ❌ FORBIDDEN - Hardcoded API keys
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(api_key="sk-...")  # ❌ NEVER hardcode!

# ✅ CORRECT - Environment-based configuration
from pydantic_settings import BaseSettings
from langchain_openai import ChatOpenAI

class LLMConfig(BaseSettings):
    openai_api_key: str
    model_name: str = "gpt-4"
    temperature: float = 0.0
    max_tokens: int = 4096
    
    class Config:
        env_file = ".env"

def create_llm(config: LLMConfig) -> ChatOpenAI:
    """Create LLM instance with proper configuration."""
    return ChatOpenAI(
        api_key=config.openai_api_key,
        model=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )
```

#### Agent Tool Design
```python
# ✅ CORRECT - Well-defined agent tools
from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    """Input schema for search tool."""
    query: str = Field(description="The search query to execute")
    max_results: int = Field(default=5, ge=1, le=20)

class SearchTool(BaseTool):
    """Tool for searching documents."""
    
    name: str = "document_search"
    description: str = (
        "Search the document database for relevant information. "
        "Use this when you need to find specific facts or context."
    )
    args_schema: Type[BaseModel] = SearchInput
    
    def _run(
        self,
        query: str,
        max_results: int = 5,
    ) -> str:
        """Execute the search synchronously."""
        # Implementation
        results = self._search_database(query, max_results)
        return self._format_results(results)
    
    async def _arun(
        self,
        query: str,
        max_results: int = 5,
    ) -> str:
        """Execute the search asynchronously."""
        # Async implementation
        results = await self._async_search_database(query, max_results)
        return self._format_results(results)
```

#### RAG Implementation
```python
# ✅ CORRECT - Production-ready RAG setup
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List

class RAGPipeline:
    """Production-ready RAG pipeline."""
    
    def __init__(
        self,
        embedding_model: str = "text-embedding-3-small",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        collection_name: str = "documents",
        persist_directory: str = "./chroma_db",
    ):
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory,
        )
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store."""
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks")
        self.vectorstore.add_documents(chunks)
    
    def retrieve(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Retrieve relevant documents for a query."""
        return self.vectorstore.similarity_search(
            query,
            k=k,
            filter=filter,
        )
```

### 9. 🚨 API Serving Best Practices (FastAPI)

```python
# ✅ CORRECT - Production-ready FastAPI ML API
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
import numpy as np

app = FastAPI(
    title="ML Model API",
    version="1.0.0",
    description="Production ML Model Inference API",
)

# Request/Response schemas
class PredictionRequest(BaseModel):
    """Input schema for prediction endpoint."""
    features: List[float] = Field(
        ...,
        min_length=1,
        description="Feature vector for prediction",
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "features": [0.5, 0.3, 0.7, 0.1]
            }
        }

class PredictionResponse(BaseModel):
    """Output schema for prediction endpoint."""
    prediction: float
    confidence: float = Field(ge=0.0, le=1.0)
    model_version: str

# Dependency injection for model
class ModelService:
    def __init__(self):
        self.model = None
        self.model_version = "1.0.0"
    
    def load_model(self, path: str) -> None:
        """Load model from path."""
        self.model = torch.load(path, map_location="cpu")
    
    @torch.inference_mode()
    def predict(self, features: np.ndarray) -> tuple[float, float]:
        """Run prediction."""
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
        output = self.model(tensor)
        prediction = output.item()
        confidence = torch.sigmoid(output).item()
        return prediction, confidence

model_service = ModelService()

def get_model_service() -> ModelService:
    return model_service

@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    model_service.load_model("models/production/model.pt")

@app.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest,
    service: ModelService = Depends(get_model_service),
) -> PredictionResponse:
    """Run model prediction."""
    try:
        features = np.array(request.features)
        prediction, confidence = service.predict(features)
        
        return PredictionResponse(
            prediction=prediction,
            confidence=confidence,
            model_version=service.model_version,
        )
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "model_loaded": model_service.model is not None}
```

---

## 🚨 PRODUCTION-READY CODE STANDARDS (CRITICAL - NO EXCEPTIONS)

**This section is MANDATORY. Violations are UNACCEPTABLE.**

### Zero-Tolerance Policy

#### 1. NO TODOs, NO Placeholders, NO Stubs
```python
# ❌ FORBIDDEN - These are NEVER acceptable:
def train_model(data):
    # TODO: implement training
    pass

def preprocess(df):
    # Placeholder - will implement later
    return df

# ✅ REQUIRED - Full implementation:
def train_model(
    model: torch.nn.Module,
    train_loader: DataLoader,
    config: TrainingConfig,
) -> torch.nn.Module:
    """Train the model with the given configuration."""
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)
    criterion = torch.nn.CrossEntropyLoss()
    
    for epoch in range(config.epochs):
        model.train()
        for batch_idx, (data, target) in enumerate(train_loader):
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
    
    return model
```

#### 2. MANDATORY Error Handling
```python
# ❌ FORBIDDEN:
data = pd.read_csv(path)  # May raise FileNotFoundError!
model = torch.load(checkpoint)  # May fail!

# ✅ REQUIRED:
def load_data(path: Path) -> pd.DataFrame:
    """Load dataset from CSV file."""
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    
    try:
        df = pd.read_csv(path)
    except pd.errors.ParserError as e:
        raise ValueError(f"Failed to parse CSV file {path}: {e}") from e
    
    if df.empty:
        raise ValueError(f"Empty dataset loaded from {path}")
    
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df
```

#### 3. Input Validation is MANDATORY
```python
# ❌ FORBIDDEN - No validation:
def train(lr, epochs, batch_size):
    pass  # No validation!

# ✅ REQUIRED - Comprehensive validation:
def train(
    learning_rate: float,
    epochs: int,
    batch_size: int,
) -> None:
    """Train model with validated parameters."""
    if not 0 < learning_rate < 1:
        raise ValueError(f"learning_rate must be in (0, 1), got {learning_rate}")
    
    if epochs < 1:
        raise ValueError(f"epochs must be >= 1, got {epochs}")
    
    if batch_size < 1 or batch_size > 1024:
        raise ValueError(f"batch_size must be in [1, 1024], got {batch_size}")
    
    # Proceed with training
```

### Pre-Completion Checklist (MANDATORY)

Before marking ANY task as complete, verify:

- [ ] **No TODOs**: Search for `TODO`, `FIXME`, `XXX`, `HACK` - there should be NONE.
- [ ] **No Placeholders**: No `pass` statements in function bodies, no empty implementations.
- [ ] **Type Hints**: ALL functions have complete type annotations.
- [ ] **Docstrings**: ALL public functions/classes have Google-style docstrings.
- [ ] **Error Handling**: All exceptions are caught and wrapped with context.
- [ ] **Input Validation**: All public functions validate their inputs.
- [ ] **No Hardcoded Values**: No hardcoded API keys, paths, or magic numbers.
- [ ] **Logging**: Structured logging used, no print statements.
- [ ] **Tests**: Unit tests exist for critical functions.
- [ ] **Code Quality**: `ruff check` and `mypy` pass without errors.

---

## Workflow & Coding Rules

1.  **No Unauthorized Actions**:
    *   Do NOT create documentation unless explicitly asked.
    *   Do NOT commit/push code unless explicitly asked.
    *   Do NOT write Unit Tests unless explicitly asked.
2.  **Code Style**:
    *   Follow PEP 8 conventions.
    *   Use Black for formatting, Ruff for linting.
    *   Maximum line length: 88 characters (Black default).
3.  **Research & Proactive Planning**:
    *   Use `search_web` to research latest ML best practices.
    *   Plan changes carefully to avoid breaking existing logic.

---

## Automation Scripts (MANDATORY Usage)

This skill includes automation scripts located in `.github/skills/expert-python-aiml-developer/scripts/`. You MUST use these scripts when the task matches the use cases below.

### Script Reference & When to Use

| Script | When to Use | Command |
|--------|-------------|---------|
| `scaffold_project.py` | Creating a **NEW ML project** from scratch | `python .github/skills/expert-python-aiml-developer/scripts/scaffold_project.py <project_name>` |
| `validate_production_ready.py` | **MANDATORY before completion** - Check for TODOs, type hints, docstrings | `python .github/skills/expert-python-aiml-developer/scripts/validate_production_ready.py src/` |
| `validate_type_hints.py` | **MANDATORY** - Check for missing type annotations | `python .github/skills/expert-python-aiml-developer/scripts/validate_type_hints.py src/` |
| `validate_security.py` | **Security scan** - Check for hardcoded secrets, unsafe operations | `python .github/skills/expert-python-aiml-developer/scripts/validate_security.py src/` |
| `analyze_code_quality.py` | Run linting and code quality checks | `python .github/skills/expert-python-aiml-developer/scripts/analyze_code_quality.py src/` |
| `validate_model_reproducibility.py` | Check for seed setting, deterministic operations | `python .github/skills/expert-python-aiml-developer/scripts/validate_model_reproducibility.py src/` |
| `generate_api_schema.py` | Generate OpenAPI schema from FastAPI app | `python .github/skills/expert-python-aiml-developer/scripts/generate_api_schema.py src/api/main.py` |
| `validate_data_pipeline.py` | Validate data processing pipelines | `python .github/skills/expert-python-aiml-developer/scripts/validate_data_pipeline.py src/data/` |
| `generate_quality_report.py` | **One-stop quality check** - Run ALL validators | `python .github/skills/expert-python-aiml-developer/scripts/generate_quality_report.py src/` |

### Workflow Example: Creating a New ML Project

```bash
# Step 1: Scaffold the project
python .github/skills/expert-python-aiml-developer/scripts/scaffold_project.py my_ml_project

# Step 2: Implement model and training logic

# Step 3: ONE-STOP QUALITY CHECK
python .github/skills/expert-python-aiml-developer/scripts/generate_quality_report.py src/

# Step 4: Run type checking
mypy src/

# Step 5: Run tests
pytest tests/ -v

# Step 6: Build and verify
python -m build
```

---

## Common Anti-Patterns (AVOID!)

### 1. Missing Type Hints (~40% of issues)
```python
# ❌ ANTI-PATTERN: No type hints
def process_data(data, config):
    return data

# ✅ FIX: Complete type hints
def process_data(
    data: pd.DataFrame,
    config: ProcessingConfig,
) -> pd.DataFrame:
    return data
```

### 2. Hardcoded Values (~25% of issues)
```python
# ❌ ANTI-PATTERN: Hardcoded values
lr = 0.001
batch_size = 32
model_path = "/home/user/models/model.pt"

# ✅ FIX: Use configuration
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    learning_rate: float = 0.001
    batch_size: int = 32
    model_path: str
    
    class Config:
        env_file = ".env"
```

### 3. No Error Context (~20% of issues)
```python
# ❌ ANTI-PATTERN: Bare exception handling
try:
    model = load_model(path)
except Exception:
    raise

# ✅ FIX: Add context
try:
    model = load_model(path)
except FileNotFoundError as e:
    raise FileNotFoundError(f"Model not found at {path}") from e
except Exception as e:
    raise RuntimeError(f"Failed to load model from {path}: {e}") from e
```

### 4. Memory Leaks in Training (~15% of issues)
```python
# ❌ ANTI-PATTERN: Accumulating tensors
losses = []
for batch in dataloader:
    loss = model(batch)
    losses.append(loss)  # ❌ Keeps computation graph!

# ✅ FIX: Detach or extract values
losses = []
for batch in dataloader:
    loss = model(batch)
    losses.append(loss.item())  # ✅ Extract scalar
```

---

## 🖼️ Computer Vision Best Practices (CRITICAL)

This section covers production-grade Computer Vision development including image classification, object detection, segmentation, and image preprocessing.

### Tech Stack for Computer Vision
*   **Deep Learning**: PyTorch, torchvision, timm (PyTorch Image Models)
*   **Object Detection**: Ultralytics YOLO, MMDetection, Detectron2
*   **Image Processing**: OpenCV, Pillow, scikit-image
*   **Augmentation**: Albumentations, torchvision.transforms
*   **Visualization**: matplotlib, supervision

### 1. Image Preprocessing Standards (MANDATORY)

#### Standard Image Normalization
```python
# ✅ CORRECT - Standard ImageNet normalization
from torchvision import transforms
from typing import Tuple

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

def get_inference_transforms(
    image_size: Tuple[int, int] = (224, 224),
) -> transforms.Compose:
    """Get inference transforms with ImageNet normalization.
    
    Args:
        image_size: Target image size (height, width).
    
    Returns:
        Composed transforms for inference.
    """
    return transforms.Compose([
        transforms.Resize(image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])

def get_training_transforms(
    image_size: Tuple[int, int] = (224, 224),
) -> transforms.Compose:
    """Get training transforms with augmentation.
    
    Args:
        image_size: Target image size (height, width).
    
    Returns:
        Composed transforms for training.
    """
    return transforms.Compose([
        transforms.RandomResizedCrop(image_size[0], scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])
```

#### OpenCV Image Loading (BGR to RGB)
```python
# ❌ FORBIDDEN - Ignoring color space conversion
import cv2
image = cv2.imread(path)
# image is in BGR format!

# ✅ CORRECT - Proper color space handling
import cv2
import numpy as np
from pathlib import Path

def load_image(
    path: Path,
    target_size: Optional[Tuple[int, int]] = None,
    normalize: bool = True,
) -> np.ndarray:
    """Load and preprocess image from path.
    
    Args:
        path: Path to image file.
        target_size: Optional (height, width) to resize.
        normalize: Whether to normalize to [0, 1].
    
    Returns:
        Image array in RGB format, shape (H, W, C).
    
    Raises:
        FileNotFoundError: If image file doesn't exist.
        ValueError: If image cannot be loaded.
    """
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Failed to load image: {path}")
    
    # Convert BGR to RGB
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    if target_size is not None:
        image = cv2.resize(image, (target_size[1], target_size[0]))
    
    if normalize:
        image = image.astype(np.float32) / 255.0
    
    return image
```

### 2. Data Augmentation with Albumentations (RECOMMENDED)

```python
# ✅ CORRECT - Production-ready augmentation pipeline
import albumentations as A
from albumentations.pytorch import ToTensorV2
from typing import Dict, Any
import numpy as np

def get_training_augmentation(
    image_size: int = 224,
    p_augment: float = 0.5,
) -> A.Compose:
    """Get training augmentation pipeline.
    
    Args:
        image_size: Target image size.
        p_augment: Probability of applying augmentations.
    
    Returns:
        Albumentations compose pipeline.
    """
    return A.Compose([
        # Resize
        A.Resize(image_size, image_size),
        
        # Geometric transforms
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.1),
        A.RandomRotate90(p=0.2),
        A.ShiftScaleRotate(
            shift_limit=0.1,
            scale_limit=0.2,
            rotate_limit=30,
            border_mode=cv2.BORDER_CONSTANT,
            p=p_augment,
        ),
        
        # Color transforms
        A.OneOf([
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2),
            A.HueSaturationValue(hue_shift_limit=20, sat_shift_limit=30, val_shift_limit=20),
            A.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
        ], p=p_augment),
        
        # Noise and blur
        A.OneOf([
            A.GaussNoise(var_limit=(10.0, 50.0)),
            A.GaussianBlur(blur_limit=3),
            A.MotionBlur(blur_limit=3),
        ], p=0.2),
        
        # Normalize and convert to tensor
        A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ToTensorV2(),
    ])


def get_validation_augmentation(image_size: int = 224) -> A.Compose:
    """Get validation/inference augmentation (no random transforms)."""
    return A.Compose([
        A.Resize(image_size, image_size),
        A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ToTensorV2(),
    ])
```

### 3. Image Classification Models

#### Using timm (PyTorch Image Models)
```python
# ✅ CORRECT - Production image classifier
import timm
import torch
import torch.nn as nn
from typing import Optional, List

class ImageClassifier(nn.Module):
    """Production-ready image classifier using timm.
    
    Args:
        model_name: timm model name (e.g., 'efficientnet_b0', 'resnet50').
        num_classes: Number of output classes.
        pretrained: Whether to use pretrained weights.
        dropout: Dropout rate before classifier.
    """
    
    def __init__(
        self,
        model_name: str = "efficientnet_b0",
        num_classes: int = 10,
        pretrained: bool = True,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        
        self.backbone = timm.create_model(
            model_name,
            pretrained=pretrained,
            num_classes=0,  # Remove classifier
            drop_rate=dropout,
        )
        
        # Get feature dimension
        self.num_features = self.backbone.num_features
        
        # Custom classifier head
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(self.num_features, num_classes),
        )
        
        self.model_name = model_name
        self.num_classes = num_classes
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.
        
        Args:
            x: Input tensor of shape (B, C, H, W).
        
        Returns:
            Logits of shape (B, num_classes).
        """
        features = self.backbone(x)
        return self.classifier(features)
    
    def get_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract features without classification."""
        return self.backbone(x)


def get_available_models() -> List[str]:
    """Get list of available timm models for classification."""
    return timm.list_models(pretrained=True)
```

### 4. Object Detection with YOLO

```python
# ✅ CORRECT - Production object detection with Ultralytics YOLO
from ultralytics import YOLO
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from dataclasses import dataclass

@dataclass
class Detection:
    """Single detection result."""
    bbox: List[float]  # [x1, y1, x2, y2]
    confidence: float
    class_id: int
    class_name: str


class ObjectDetector:
    """Production-ready object detector using YOLO.
    
    Args:
        model_path: Path to YOLO model weights.
        confidence_threshold: Minimum confidence for detections.
        device: Device to run inference on.
    """
    
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        device: str = "cuda",
    ) -> None:
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.device = device
    
    def detect(
        self,
        image: np.ndarray,
        classes: Optional[List[int]] = None,
    ) -> List[Detection]:
        """Run object detection on image.
        
        Args:
            image: Input image array (RGB format).
            classes: Optional list of class IDs to filter.
        
        Returns:
            List of Detection objects.
        """
        results = self.model.predict(
            image,
            conf=self.confidence_threshold,
            device=self.device,
            classes=classes,
            verbose=False,
        )
        
        detections = []
        for result in results:
            boxes = result.boxes
            for i in range(len(boxes)):
                det = Detection(
                    bbox=boxes.xyxy[i].cpu().numpy().tolist(),
                    confidence=float(boxes.conf[i].cpu()),
                    class_id=int(boxes.cls[i].cpu()),
                    class_name=result.names[int(boxes.cls[i].cpu())],
                )
                detections.append(det)
        
        return detections
    
    def detect_batch(
        self,
        images: List[np.ndarray],
    ) -> List[List[Detection]]:
        """Run batch detection."""
        all_detections = []
        for image in images:
            all_detections.append(self.detect(image))
        return all_detections
```

### 5. Custom Dataset for Computer Vision

```python
# ✅ CORRECT - Production CV dataset class
from torch.utils.data import Dataset
from pathlib import Path
from typing import Callable, Optional, Tuple, List, Dict
from PIL import Image
import torch

class ImageClassificationDataset(Dataset):
    """Dataset for image classification tasks.
    
    Args:
        image_paths: List of paths to images.
        labels: List of integer labels.
        transform: Optional transform to apply.
        return_path: Whether to return image path.
    """
    
    def __init__(
        self,
        image_paths: List[Path],
        labels: List[int],
        transform: Optional[Callable] = None,
        return_path: bool = False,
    ) -> None:
        if len(image_paths) != len(labels):
            raise ValueError(
                f"Mismatch: {len(image_paths)} images, {len(labels)} labels"
            )
        
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform
        self.return_path = return_path
    
    def __len__(self) -> int:
        return len(self.image_paths)
    
    def __getitem__(
        self,
        idx: int,
    ) -> Tuple[torch.Tensor, int] | Tuple[torch.Tensor, int, str]:
        """Get item by index.
        
        Returns:
            Tuple of (image_tensor, label) or (image_tensor, label, path).
        """
        image_path = self.image_paths[idx]
        label = self.labels[idx]
        
        # Load image
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            raise RuntimeError(f"Failed to load image {image_path}: {e}")
        
        # Apply transform
        if self.transform is not None:
            image = self.transform(image)
        
        if self.return_path:
            return image, label, str(image_path)
        return image, label
    
    @classmethod
    def from_folder(
        cls,
        root: Path,
        transform: Optional[Callable] = None,
    ) -> "ImageClassificationDataset":
        """Create dataset from folder structure.
        
        Expected structure:
            root/
                class_0/
                    img_001.jpg
                    img_002.jpg
                class_1/
                    img_003.jpg
        """
        root = Path(root)
        classes = sorted([d.name for d in root.iterdir() if d.is_dir()])
        class_to_idx = {c: i for i, c in enumerate(classes)}
        
        image_paths = []
        labels = []
        
        for class_name in classes:
            class_dir = root / class_name
            for img_path in class_dir.glob("*"):
                if img_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}:
                    image_paths.append(img_path)
                    labels.append(class_to_idx[class_name])
        
        return cls(image_paths, labels, transform)
```

### 6. Computer Vision Metrics

```python
# ✅ CORRECT - Comprehensive CV metrics
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class ClassificationMetrics:
    """Classification evaluation metrics."""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    per_class_accuracy: Dict[int, float]


def compute_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    num_classes: int,
) -> ClassificationMetrics:
    """Compute classification metrics.
    
    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        num_classes: Number of classes.
    
    Returns:
        ClassificationMetrics dataclass.
    """
    # Overall accuracy
    accuracy = np.mean(y_true == y_pred)
    
    # Per-class metrics
    per_class_acc = {}
    precisions = []
    recalls = []
    
    for c in range(num_classes):
        mask = y_true == c
        if mask.sum() > 0:
            per_class_acc[c] = np.mean(y_pred[mask] == c)
            recalls.append(per_class_acc[c])
        
        pred_mask = y_pred == c
        if pred_mask.sum() > 0:
            precisions.append(np.mean(y_true[pred_mask] == c))
    
    precision = np.mean(precisions) if precisions else 0.0
    recall = np.mean(recalls) if recalls else 0.0
    f1 = 2 * precision * recall / (precision + recall + 1e-8)
    
    return ClassificationMetrics(
        accuracy=float(accuracy),
        precision=float(precision),
        recall=float(recall),
        f1_score=float(f1),
        per_class_accuracy=per_class_acc,
    )


def compute_iou(
    box1: List[float],
    box2: List[float],
) -> float:
    """Compute Intersection over Union (IoU) for two bounding boxes.
    
    Args:
        box1: First box [x1, y1, x2, y2].
        box2: Second box [x1, y1, x2, y2].
    
    Returns:
        IoU value in range [0, 1].
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0.0
```

### 7. Image Inference Service

```python
# ✅ CORRECT - Production image inference API
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List
import numpy as np
from PIL import Image
import io

app = FastAPI(title="Image Classification API")

class PredictionResult(BaseModel):
    """Prediction result schema."""
    class_id: int
    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)

class ClassificationResponse(BaseModel):
    """Classification response schema."""
    predictions: List[PredictionResult]
    top_class: str
    top_confidence: float

@app.post("/classify", response_model=ClassificationResponse)
async def classify_image(
    file: UploadFile = File(...),
    top_k: int = 5,
) -> ClassificationResponse:
    """Classify an uploaded image.
    
    Args:
        file: Uploaded image file.
        top_k: Number of top predictions to return.
    
    Returns:
        Classification results with confidence scores.
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read and preprocess image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Apply transforms and run inference
        # input_tensor = transform(image).unsqueeze(0)
        # with torch.inference_mode():
        #     output = model(input_tensor)
        #     probs = torch.softmax(output, dim=1)
        
        # Placeholder response
        predictions = [
            PredictionResult(class_id=0, class_name="cat", confidence=0.85),
            PredictionResult(class_id=1, class_name="dog", confidence=0.10),
        ]
        
        return ClassificationResponse(
            predictions=predictions[:top_k],
            top_class=predictions[0].class_name,
            top_confidence=predictions[0].confidence,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")
```

### 8. CV Anti-Patterns to Avoid

```python
# ❌ ANTI-PATTERN #1: Not handling color channels
image = cv2.imread(path)  # BGR format!
model(image)  # Model expects RGB!

# ✅ FIX: Always convert color space
image = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)

# ❌ ANTI-PATTERN #2: Augmentation on validation data
val_transform = A.Compose([
    A.RandomFlip(p=0.5),  # ❌ Random augmentation on validation!
    A.Normalize(...),
])

# ✅ FIX: Only deterministic transforms on validation
val_transform = A.Compose([
    A.Resize(224, 224),
    A.Normalize(...),
])

# ❌ ANTI-PATTERN #3: Not using inference mode
def predict(model, image):
    return model(image)  # ❌ Computes gradients!

# ✅ FIX: Use inference mode
@torch.inference_mode()
def predict(model: nn.Module, image: torch.Tensor) -> torch.Tensor:
    model.eval()
    return model(image)

# ❌ ANTI-PATTERN #4: Hardcoded normalization values
transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])  # ❌ Generic values

# ✅ FIX: Use dataset-specific normalization
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
```

---

## Quick Validation Checklist

Before completing any task, verify:

**Code Quality:**
- [ ] All functions have type hints
- [ ] All public functions have docstrings
- [ ] No print statements (use logging)
- [ ] No hardcoded secrets or paths
- [ ] No TODOs or placeholders

**ML Best Practices:**
- [ ] Random seeds set for reproducibility
- [ ] Proper GPU memory management
- [ ] Model checkpointing implemented
- [ ] Data validation at pipeline boundaries

**Production Readiness:**
- [ ] Error handling with context
- [ ] Input validation on all public APIs
- [ ] Logging configured properly
- [ ] Configuration externalized

**Build & Validation:**
- [ ] `ruff check .` passes
- [ ] `mypy src/` passes
- [ ] `pytest tests/` passes
- [ ] `validate_production_ready.py` passes
