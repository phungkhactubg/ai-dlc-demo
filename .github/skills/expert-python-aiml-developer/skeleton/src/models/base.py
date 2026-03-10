"""Base model interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import torch
import torch.nn as nn


class BaseModel(ABC, nn.Module):
    """Abstract base class for all models.
    
    All model implementations should inherit from this class
    and implement the required abstract methods.
    """
    
    def __init__(self) -> None:
        super().__init__()
        self._is_trained = False
    
    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.
        
        Args:
            x: Input tensor.
        
        Returns:
            Model output tensor.
        """
        pass
    
    @property
    def is_trained(self) -> bool:
        """Whether the model has been trained."""
        return self._is_trained
    
    def mark_trained(self) -> None:
        """Mark the model as trained."""
        self._is_trained = True
    
    def count_parameters(self) -> int:
        """Count trainable parameters.
        
        Returns:
            Number of trainable parameters.
        """
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
    
    def freeze(self) -> None:
        """Freeze all parameters."""
        for param in self.parameters():
            param.requires_grad = False
    
    def unfreeze(self) -> None:
        """Unfreeze all parameters."""
        for param in self.parameters():
            param.requires_grad = True
    
    def get_config(self) -> Dict[str, Any]:
        """Get model configuration.
        
        Returns:
            Configuration dictionary.
        """
        return {
            "class_name": self.__class__.__name__,
            "num_parameters": self.count_parameters(),
            "is_trained": self.is_trained,
        }
