"""
Production-ready training loop template.

This template demonstrates best practices for:
- Type hints and documentation
- Reproducibility (seeds, checkpointing)
- Error handling
- Structured logging
- Proper memory management
- Early stopping and model selection
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.optim import Optimizer
from torch.optim.lr_scheduler import _LRScheduler
from torch.utils.data import DataLoader

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Configuration for training loop."""
    
    epochs: int = 100
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    gradient_clip: float = 1.0
    early_stopping_patience: int = 10
    checkpoint_dir: Path = Path("checkpoints")
    log_every: int = 100
    eval_every: int = 1
    save_every: int = 5
    device: str = "cuda"
    mixed_precision: bool = True


@dataclass
class TrainingState:
    """Training state for checkpointing."""
    
    epoch: int
    global_step: int
    best_val_loss: float
    patience_counter: int
    history: Dict[str, List[float]]


class EarlyStopper:
    """Early stopping handler.
    
    Stops training when validation loss stops improving.
    
    Args:
        patience: Number of epochs to wait before stopping.
        min_delta: Minimum change to qualify as improvement.
        mode: 'min' for loss, 'max' for metrics like accuracy.
    """
    
    def __init__(
        self,
        patience: int = 10,
        min_delta: float = 0.001,
        mode: str = "min",
    ) -> None:
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.best_value: Optional[float] = None
        self.counter = 0
        self.should_stop = False
    
    def __call__(self, value: float) -> bool:
        """Check if training should stop.
        
        Args:
            value: Current metric value.
        
        Returns:
            True if training should stop.
        """
        if self.best_value is None:
            self.best_value = value
            return False
        
        if self.mode == "min":
            improved = value < self.best_value - self.min_delta
        else:
            improved = value > self.best_value + self.min_delta
        
        if improved:
            self.best_value = value
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.should_stop = True
                logger.info(
                    f"Early stopping triggered after {self.patience} epochs "
                    f"without improvement"
                )
        
        return self.should_stop


class Trainer:
    """Production-ready trainer for PyTorch models.
    
    This trainer implements:
    - Mixed precision training
    - Gradient clipping
    - Learning rate scheduling
    - Checkpointing and resume
    - Early stopping
    - Proper memory management
    
    Args:
        model: PyTorch model to train.
        optimizer: Optimizer instance.
        criterion: Loss function.
        config: Training configuration.
        scheduler: Optional learning rate scheduler.
        
    Example:
        >>> model = MyModel()
        >>> optimizer = torch.optim.AdamW(model.parameters())
        >>> criterion = nn.CrossEntropyLoss()
        >>> trainer = Trainer(model, optimizer, criterion, config)
        >>> history = trainer.train(train_loader, val_loader)
    """
    
    def __init__(
        self,
        model: nn.Module,
        optimizer: Optimizer,
        criterion: nn.Module,
        config: TrainingConfig,
        scheduler: Optional[_LRScheduler] = None,
    ) -> None:
        self.model = model
        self.optimizer = optimizer
        self.criterion = criterion
        self.config = config
        self.scheduler = scheduler
        
        self.device = torch.device(config.device)
        self.model.to(self.device)
        
        # Mixed precision
        self.scaler = torch.cuda.amp.GradScaler() if config.mixed_precision else None
        
        # Training state
        self.state = TrainingState(
            epoch=0,
            global_step=0,
            best_val_loss=float("inf"),
            patience_counter=0,
            history={"train_loss": [], "val_loss": []},
        )
        
        # Early stopping
        self.early_stopper = EarlyStopper(patience=config.early_stopping_patience)
        
        # Create checkpoint directory
        config.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def train(
        self,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        resume_from: Optional[Path] = None,
    ) -> Dict[str, List[float]]:
        """Train the model.
        
        Args:
            train_loader: Training data loader.
            val_loader: Optional validation data loader.
            resume_from: Optional path to checkpoint to resume from.
        
        Returns:
            Training history dictionary.
        
        Raises:
            RuntimeError: If training fails.
        """
        if resume_from is not None:
            self._load_checkpoint(resume_from)
            logger.info(f"Resumed training from epoch {self.state.epoch}")
        
        logger.info(f"Starting training for {self.config.epochs} epochs")
        logger.info(f"Device: {self.device}")
        logger.info(f"Mixed precision: {self.config.mixed_precision}")
        
        try:
            for epoch in range(self.state.epoch, self.config.epochs):
                self.state.epoch = epoch
                
                # Training epoch
                train_loss = self._train_epoch(train_loader)
                self.state.history["train_loss"].append(train_loss)
                
                # Validation
                if val_loader is not None and epoch % self.config.eval_every == 0:
                    val_loss = self._validate(val_loader)
                    self.state.history["val_loss"].append(val_loss)
                    
                    logger.info(
                        f"Epoch {epoch + 1}/{self.config.epochs} - "
                        f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}"
                    )
                    
                    # Check for best model
                    if val_loss < self.state.best_val_loss:
                        self.state.best_val_loss = val_loss
                        self._save_checkpoint("best_model.pt", is_best=True)
                    
                    # Early stopping
                    if self.early_stopper(val_loss):
                        logger.info("Early stopping triggered")
                        break
                else:
                    logger.info(
                        f"Epoch {epoch + 1}/{self.config.epochs} - "
                        f"Train Loss: {train_loss:.4f}"
                    )
                
                # Learning rate scheduling
                if self.scheduler is not None:
                    self.scheduler.step()
                
                # Periodic checkpoint
                if (epoch + 1) % self.config.save_every == 0:
                    self._save_checkpoint(f"checkpoint_epoch_{epoch + 1:04d}.pt")
            
            logger.info("Training completed!")
            return self.state.history
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            self._save_checkpoint("emergency_checkpoint.pt")
            raise RuntimeError(f"Training failed at epoch {self.state.epoch}: {e}") from e
    
    def _train_epoch(self, dataloader: DataLoader) -> float:
        """Train for one epoch.
        
        Args:
            dataloader: Training data loader.
        
        Returns:
            Average training loss.
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0
        
        for batch_idx, (data, target) in enumerate(dataloader):
            data = data.to(self.device, non_blocking=True)
            target = target.to(self.device, non_blocking=True)
            
            self.optimizer.zero_grad(set_to_none=True)
            
            # Forward pass with mixed precision
            if self.scaler is not None:
                with torch.cuda.amp.autocast():
                    output = self.model(data)
                    loss = self.criterion(output, target)
                
                self.scaler.scale(loss).backward()
                
                # Gradient clipping
                if self.config.gradient_clip > 0:
                    self.scaler.unscale_(self.optimizer)
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(),
                        self.config.gradient_clip,
                    )
                
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                output = self.model(data)
                loss = self.criterion(output, target)
                loss.backward()
                
                if self.config.gradient_clip > 0:
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(),
                        self.config.gradient_clip,
                    )
                
                self.optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
            self.state.global_step += 1
            
            # Logging
            if batch_idx % self.config.log_every == 0:
                logger.debug(
                    f"Batch {batch_idx}/{len(dataloader)} - "
                    f"Loss: {loss.item():.4f}"
                )
        
        return total_loss / num_batches
    
    @torch.inference_mode()
    def _validate(self, dataloader: DataLoader) -> float:
        """Run validation.
        
        Args:
            dataloader: Validation data loader.
        
        Returns:
            Average validation loss.
        """
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        for data, target in dataloader:
            data = data.to(self.device, non_blocking=True)
            target = target.to(self.device, non_blocking=True)
            
            output = self.model(data)
            loss = self.criterion(output, target)
            
            total_loss += loss.item()
            num_batches += 1
        
        return total_loss / num_batches
    
    def _save_checkpoint(self, filename: str, is_best: bool = False) -> None:
        """Save training checkpoint.
        
        Args:
            filename: Checkpoint filename.
            is_best: Whether this is the best model.
        """
        checkpoint = {
            "epoch": self.state.epoch,
            "global_step": self.state.global_step,
            "best_val_loss": self.state.best_val_loss,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": (
                self.scheduler.state_dict() if self.scheduler else None
            ),
            "history": self.state.history,
            "config": self.config.__dict__,
        }
        
        path = self.config.checkpoint_dir / filename
        torch.save(checkpoint, path)
        
        if is_best:
            logger.info(f"New best model saved: Val Loss = {self.state.best_val_loss:.4f}")
        else:
            logger.debug(f"Checkpoint saved: {path}")
    
    def _load_checkpoint(self, path: Path) -> None:
        """Load training checkpoint.
        
        Args:
            path: Path to checkpoint file.
        
        Raises:
            FileNotFoundError: If checkpoint doesn't exist.
        """
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {path}")
        
        checkpoint = torch.load(path, map_location=self.device)
        
        self.state.epoch = checkpoint["epoch"] + 1
        self.state.global_step = checkpoint["global_step"]
        self.state.best_val_loss = checkpoint["best_val_loss"]
        self.state.history = checkpoint["history"]
        
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        
        if self.scheduler and checkpoint["scheduler_state_dict"]:
            self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        
        logger.info(f"Loaded checkpoint from {path}")


# Example usage
if __name__ == "__main__":
    from src.utils.reproducibility import set_seed
    from src.utils.logging import setup_logging
    
    # Setup
    setup_logging(level="INFO")
    set_seed(42)
    
    # Create simple model for demonstration
    model = nn.Sequential(
        nn.Linear(784, 256),
        nn.ReLU(),
        nn.Linear(256, 10),
    )
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()
    config = TrainingConfig(epochs=10, device="cpu")
    
    trainer = Trainer(model, optimizer, criterion, config)
    
    # Would train with: trainer.train(train_loader, val_loader)
    logger.info("Trainer initialized successfully")
