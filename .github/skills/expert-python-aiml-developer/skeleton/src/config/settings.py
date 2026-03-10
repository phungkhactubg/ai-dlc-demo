"""Pydantic Settings configuration for the project."""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Application-level settings."""
    
    app_name: str = Field(default="ml-project")
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class ModelSettings(BaseSettings):
    """Model configuration settings."""
    
    model_name: str = Field(default="efficientnet_b0")
    model_path: Path = Field(default=Path("models/production/model.pt"))
    num_classes: int = Field(default=10, ge=1)
    image_size: int = Field(default=224, ge=32, le=1024)
    pretrained: bool = Field(default=True)
    
    class Config:
        env_prefix = "MODEL_"
        env_file = ".env"


class TrainingSettings(BaseSettings):
    """Training configuration settings."""
    
    seed: int = Field(default=42)
    epochs: int = Field(default=100, ge=1)
    batch_size: int = Field(default=32, ge=1, le=512)
    learning_rate: float = Field(default=1e-4, ge=1e-8, le=1.0)
    weight_decay: float = Field(default=0.01, ge=0.0)
    gradient_clip: float = Field(default=1.0, ge=0.0)
    
    # Early stopping
    early_stopping_patience: int = Field(default=10, ge=1)
    
    # Checkpointing
    checkpoint_dir: Path = Field(default=Path("models/checkpoints"))
    save_every: int = Field(default=5, ge=1)
    
    # Device
    device: str = Field(default="cuda")
    mixed_precision: bool = Field(default=True)
    
    class Config:
        env_prefix = "TRAIN_"
        env_file = ".env"
    
    @field_validator("device")
    @classmethod
    def validate_device(cls, v: str) -> str:
        """Validate device is cuda or cpu."""
        if v not in ("cuda", "cpu", "mps"):
            raise ValueError(f"device must be 'cuda', 'cpu', or 'mps', got '{v}'")
        return v


class InferenceSettings(BaseSettings):
    """Inference configuration settings."""
    
    batch_size: int = Field(default=64, ge=1)
    device: str = Field(default="cuda")
    precision: str = Field(default="fp32")  # fp32, fp16, bf16
    
    # Thresholds
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    
    class Config:
        env_prefix = "INFERENCE_"
        env_file = ".env"


class APISettings(BaseSettings):
    """API server configuration."""
    
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=1, ge=1)
    reload: bool = Field(default=False)
    
    # CORS
    cors_origins: str = Field(default="*")
    
    class Config:
        env_prefix = "API_"
        env_file = ".env"


# Cached settings getters
@lru_cache
def get_app_settings() -> AppSettings:
    """Get cached application settings."""
    return AppSettings()


@lru_cache
def get_model_settings() -> ModelSettings:
    """Get cached model settings."""
    return ModelSettings()


@lru_cache
def get_training_settings() -> TrainingSettings:
    """Get cached training settings."""
    return TrainingSettings()


@lru_cache
def get_inference_settings() -> InferenceSettings:
    """Get cached inference settings."""
    return InferenceSettings()


@lru_cache
def get_api_settings() -> APISettings:
    """Get cached API settings."""
    return APISettings()
