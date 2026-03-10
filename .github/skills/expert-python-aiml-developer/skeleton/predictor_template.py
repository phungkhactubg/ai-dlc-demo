"""
Model inference service template.

This template demonstrates best practices for:
- Type-safe inference
- Batch processing
- Error handling
- Memory management
- Thread-safe model loading
"""

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass
class InferenceConfig:
    """Configuration for inference service."""
    
    model_path: Path = Path("models/production/model.pt")
    device: str = "cuda"
    batch_size: int = 32
    precision: str = "fp32"  # fp32, fp16, bf16
    warmup_rounds: int = 3


class PredictionRequest(BaseModel):
    """Input schema for predictions."""
    
    features: List[float] = Field(
        ...,
        min_length=1,
        description="Feature vector for prediction",
    )


class PredictionResponse(BaseModel):
    """Output schema for predictions."""
    
    prediction: float
    confidence: float = Field(ge=0.0, le=1.0)
    class_probabilities: Optional[List[float]] = None
    model_version: str = "1.0.0"


class ModelLoadError(Exception):
    """Raised when model loading fails."""
    pass


class InferenceError(Exception):
    """Raised when inference fails."""
    pass


class Predictor:
    """Thread-safe model predictor service.
    
    This predictor provides:
    - Lazy model loading
    - Thread-safe inference
    - Batch prediction support
    - Proper memory management
    
    Args:
        config: Inference configuration.
        
    Example:
        >>> predictor = Predictor(InferenceConfig())
        >>> predictor.load_model()
        >>> result = predictor.predict(features)
    """
    
    _instance: Optional["Predictor"] = None
    _lock = threading.Lock()
    
    def __init__(self, config: InferenceConfig) -> None:
        self.config = config
        self.model: Optional[nn.Module] = None
        self.device = torch.device(config.device)
        self._model_lock = threading.Lock()
        self._loaded = False
    
    @classmethod
    def get_instance(cls, config: Optional[InferenceConfig] = None) -> "Predictor":
        """Get singleton predictor instance.
        
        Args:
            config: Optional configuration (only used on first call).
        
        Returns:
            Predictor singleton instance.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    if config is None:
                        config = InferenceConfig()
                    cls._instance = cls(config)
        return cls._instance
    
    def load_model(self, force_reload: bool = False) -> None:
        """Load model from checkpoint.
        
        Args:
            force_reload: Force reload even if already loaded.
        
        Raises:
            ModelLoadError: If model loading fails.
        """
        if self._loaded and not force_reload:
            logger.debug("Model already loaded, skipping")
            return
        
        with self._model_lock:
            try:
                logger.info(f"Loading model from {self.config.model_path}")
                
                if not self.config.model_path.exists():
                    raise FileNotFoundError(
                        f"Model checkpoint not found: {self.config.model_path}"
                    )
                
                # Load checkpoint with weights_only for security
                checkpoint = torch.load(
                    self.config.model_path,
                    map_location=self.device,
                    weights_only=True,
                )
                
                # Extract model state
                if isinstance(checkpoint, dict):
                    if "model_state_dict" in checkpoint:
                        state_dict = checkpoint["model_state_dict"]
                    else:
                        state_dict = checkpoint
                else:
                    state_dict = checkpoint
                
                # Initialize model architecture (customize this)
                self.model = self._create_model_architecture()
                self.model.load_state_dict(state_dict)
                self.model.to(self.device)
                self.model.eval()
                
                # Apply precision settings
                self._apply_precision()
                
                # Warmup
                self._warmup()
                
                self._loaded = True
                logger.info("Model loaded successfully")
                
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise ModelLoadError(f"Failed to load model: {e}") from e
    
    def _create_model_architecture(self) -> nn.Module:
        """Create model architecture.
        
        Override this method to define your model architecture.
        
        Returns:
            Model instance.
        """
        # Default: simple MLP for demonstration
        # Replace with your actual model architecture
        return nn.Sequential(
            nn.Linear(10, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )
    
    def _apply_precision(self) -> None:
        """Apply precision settings to model."""
        if self.model is None:
            return
        
        if self.config.precision == "fp16":
            self.model = self.model.half()
            logger.info("Using FP16 precision")
        elif self.config.precision == "bf16" and torch.cuda.is_bf16_supported():
            self.model = self.model.to(torch.bfloat16)
            logger.info("Using BF16 precision")
    
    def _warmup(self) -> None:
        """Warmup model with dummy predictions."""
        if self.model is None or self.config.warmup_rounds <= 0:
            return
        
        logger.debug(f"Running {self.config.warmup_rounds} warmup rounds")
        
        # Determine input size from first layer
        input_size = 10  # Default, adjust based on your model
        for module in self.model.modules():
            if isinstance(module, nn.Linear):
                input_size = module.in_features
                break
        
        dummy_input = torch.zeros(1, input_size, device=self.device)
        
        with torch.inference_mode():
            for _ in range(self.config.warmup_rounds):
                _ = self.model(dummy_input)
        
        logger.debug("Warmup completed")
    
    @torch.inference_mode()
    def predict(
        self,
        features: Union[List[float], np.ndarray, torch.Tensor],
    ) -> PredictionResponse:
        """Run prediction on input features.
        
        Args:
            features: Input feature vector.
        
        Returns:
            Prediction response with result and confidence.
        
        Raises:
            InferenceError: If prediction fails.
            RuntimeError: If model is not loaded.
        """
        if not self._loaded or self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            # Convert input to tensor
            if isinstance(features, list):
                tensor = torch.tensor(features, dtype=torch.float32)
            elif isinstance(features, np.ndarray):
                tensor = torch.from_numpy(features).float()
            else:
                tensor = features.float()
            
            # Ensure batch dimension
            if tensor.dim() == 1:
                tensor = tensor.unsqueeze(0)
            
            # Move to device
            tensor = tensor.to(self.device)
            
            # Run inference
            output = self.model(tensor)
            
            # Process output
            prediction = output.squeeze().item()
            confidence = torch.sigmoid(output).squeeze().item()
            
            return PredictionResponse(
                prediction=prediction,
                confidence=confidence,
                model_version="1.0.0",
            )
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise InferenceError(f"Prediction failed: {e}") from e
    
    @torch.inference_mode()
    def predict_batch(
        self,
        batch: List[List[float]],
    ) -> List[PredictionResponse]:
        """Run batch prediction.
        
        Args:
            batch: List of feature vectors.
        
        Returns:
            List of prediction responses.
        
        Raises:
            InferenceError: If prediction fails.
        """
        if not self._loaded or self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            # Convert to tensor
            tensor = torch.tensor(batch, dtype=torch.float32, device=self.device)
            
            # Run inference
            outputs = self.model(tensor)
            
            # Process outputs
            predictions = outputs.squeeze().cpu().numpy()
            confidences = torch.sigmoid(outputs).squeeze().cpu().numpy()
            
            # Ensure arrays
            if predictions.ndim == 0:
                predictions = np.array([predictions.item()])
                confidences = np.array([confidences.item()])
            
            return [
                PredictionResponse(
                    prediction=float(pred),
                    confidence=float(conf),
                    model_version="1.0.0",
                )
                for pred, conf in zip(predictions, confidences)
            ]
            
        except Exception as e:
            logger.error(f"Batch prediction failed: {e}")
            raise InferenceError(f"Batch prediction failed: {e}") from e
    
    def unload_model(self) -> None:
        """Unload model and free memory."""
        with self._model_lock:
            if self.model is not None:
                del self.model
                self.model = None
                self._loaded = False
                
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                logger.info("Model unloaded")


# FastAPI integration example
def create_prediction_endpoint():
    """Create FastAPI prediction endpoint."""
    from fastapi import APIRouter, HTTPException, Depends
    
    router = APIRouter()
    predictor = Predictor.get_instance()
    
    @router.on_event("startup")
    async def startup():
        predictor.load_model()
    
    @router.post("/predict", response_model=PredictionResponse)
    async def predict(request: PredictionRequest) -> PredictionResponse:
        try:
            return predictor.predict(request.features)
        except InferenceError as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return router


# Example usage
if __name__ == "__main__":
    from src.utils.logging import setup_logging
    
    setup_logging(level="INFO")
    
    # Create predictor
    config = InferenceConfig(device="cpu")
    predictor = Predictor(config)
    
    # Note: This would fail without a real model file
    # predictor.load_model()
    # result = predictor.predict([0.1, 0.2, 0.3, ...])
    
    logger.info("Predictor initialized successfully")
