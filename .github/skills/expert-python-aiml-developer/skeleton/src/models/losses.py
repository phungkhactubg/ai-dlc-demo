"""Custom loss functions."""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class FocalLoss(nn.Module):
    """Focal Loss for imbalanced classification.
    
    Args:
        alpha: Class weight factor.
        gamma: Focusing parameter.
        reduction: Reduction method ('none', 'mean', 'sum').
    """
    
    def __init__(
        self,
        alpha: float = 1.0,
        gamma: float = 2.0,
        reduction: str = "mean",
    ) -> None:
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction
    
    def forward(
        self,
        inputs: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:
        """Compute focal loss.
        
        Args:
            inputs: Logits of shape (N, C).
            targets: Labels of shape (N,).
        
        Returns:
            Focal loss value.
        """
        ce_loss = F.cross_entropy(inputs, targets, reduction="none")
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss
        
        if self.reduction == "mean":
            return focal_loss.mean()
        elif self.reduction == "sum":
            return focal_loss.sum()
        return focal_loss


class LabelSmoothingLoss(nn.Module):
    """Label smoothing loss for regularization.
    
    Args:
        smoothing: Label smoothing factor.
        reduction: Reduction method.
    """
    
    def __init__(
        self,
        smoothing: float = 0.1,
        reduction: str = "mean",
    ) -> None:
        super().__init__()
        self.smoothing = smoothing
        self.reduction = reduction
    
    def forward(
        self,
        inputs: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:
        """Compute label smoothing loss.
        
        Args:
            inputs: Logits of shape (N, C).
            targets: Labels of shape (N,).
        
        Returns:
            Smoothed cross-entropy loss.
        """
        num_classes = inputs.size(-1)
        log_probs = F.log_softmax(inputs, dim=-1)
        
        # Create smoothed labels
        with torch.no_grad():
            true_dist = torch.zeros_like(log_probs)
            true_dist.fill_(self.smoothing / (num_classes - 1))
            true_dist.scatter_(1, targets.unsqueeze(1), 1.0 - self.smoothing)
        
        loss = (-true_dist * log_probs).sum(dim=-1)
        
        if self.reduction == "mean":
            return loss.mean()
        elif self.reduction == "sum":
            return loss.sum()
        return loss
