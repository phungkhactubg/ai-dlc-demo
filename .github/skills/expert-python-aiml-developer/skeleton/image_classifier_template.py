"""
Image Classification model template.

This template demonstrates best practices for:
- Transfer learning with timm
- Proper image preprocessing
- Training with augmentation
- Inference with proper memory management
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from PIL import Image

logger = logging.getLogger(__name__)

# ImageNet normalization constants
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


@dataclass
class ClassifierConfig:
    """Configuration for image classifier."""
    
    model_name: str = "efficientnet_b0"
    num_classes: int = 10
    image_size: int = 224
    pretrained: bool = True
    dropout: float = 0.2
    freeze_backbone: bool = False
    

class ImageClassifier(nn.Module):
    """Production-ready image classifier using timm.
    
    This classifier provides:
    - Transfer learning from pretrained models
    - Custom classifier head
    - Feature extraction capability
    - Proper initialization
    
    Args:
        config: Classifier configuration.
        
    Example:
        >>> config = ClassifierConfig(num_classes=100)
        >>> model = ImageClassifier(config)
        >>> output = model(torch.randn(1, 3, 224, 224))
    """
    
    def __init__(self, config: ClassifierConfig) -> None:
        super().__init__()
        self.config = config
        
        try:
            import timm
        except ImportError:
            raise ImportError("timm is required. Install with: pip install timm")
        
        # Create backbone
        self.backbone = timm.create_model(
            config.model_name,
            pretrained=config.pretrained,
            num_classes=0,  # Remove classifier head
            drop_rate=config.dropout,
        )
        
        # Get feature dimension
        self.num_features = self.backbone.num_features
        
        # Freeze backbone if requested
        if config.freeze_backbone:
            for param in self.backbone.parameters():
                param.requires_grad = False
            logger.info("Backbone frozen for transfer learning")
        
        # Custom classifier head
        self.classifier = nn.Sequential(
            nn.Dropout(config.dropout),
            nn.Linear(self.num_features, config.num_classes),
        )
        
        # Initialize classifier
        self._init_classifier()
        
        logger.info(
            f"Created {config.model_name} with {config.num_classes} classes, "
            f"features dim: {self.num_features}"
        )
    
    def _init_classifier(self) -> None:
        """Initialize classifier weights."""
        for module in self.classifier.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
    
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
        """Extract features without classification.
        
        Args:
            x: Input tensor of shape (B, C, H, W).
        
        Returns:
            Features of shape (B, num_features).
        """
        return self.backbone(x)
    
    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Get class probabilities.
        
        Args:
            x: Input tensor of shape (B, C, H, W).
        
        Returns:
            Probabilities of shape (B, num_classes).
        """
        logits = self.forward(x)
        return F.softmax(logits, dim=1)
    
    def unfreeze_backbone(self, layers: Optional[int] = None) -> None:
        """Unfreeze backbone layers for fine-tuning.
        
        Args:
            layers: Number of layers to unfreeze from the end.
                   If None, unfreeze all layers.
        """
        params = list(self.backbone.parameters())
        
        if layers is None:
            for param in params:
                param.requires_grad = True
            logger.info("Unfroze all backbone layers")
        else:
            # Unfreeze last N layers
            for param in params[-layers:]:
                param.requires_grad = True
            logger.info(f"Unfroze last {layers} backbone layers")


class ImageDataset(Dataset):
    """Dataset for image classification.
    
    Args:
        image_paths: List of paths to images.
        labels: List of integer labels.
        transform: Transform to apply to images.
    """
    
    def __init__(
        self,
        image_paths: List[Path],
        labels: List[int],
        transform: Optional[Callable] = None,
    ) -> None:
        if len(image_paths) != len(labels):
            raise ValueError(
                f"Mismatch: {len(image_paths)} images vs {len(labels)} labels"
            )
        
        self.image_paths = [Path(p) for p in image_paths]
        self.labels = labels
        self.transform = transform
    
    def __len__(self) -> int:
        return len(self.image_paths)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        """Get a sample.
        
        Args:
            idx: Sample index.
        
        Returns:
            Tuple of (image_tensor, label).
        """
        image_path = self.image_paths[idx]
        label = self.labels[idx]
        
        # Load image
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            raise RuntimeError(f"Failed to load {image_path}: {e}")
        
        # Apply transform
        if self.transform is not None:
            image = self.transform(image)
        
        return image, label
    
    @classmethod
    def from_folder(
        cls,
        root: Path,
        transform: Optional[Callable] = None,
    ) -> Tuple["ImageDataset", Dict[str, int]]:
        """Create dataset from folder structure.
        
        Expected structure:
            root/class_a/image1.jpg
            root/class_a/image2.jpg
            root/class_b/image3.jpg
        
        Args:
            root: Root directory.
            transform: Transform to apply.
        
        Returns:
            Tuple of (dataset, class_to_idx mapping).
        """
        root = Path(root)
        
        # Get class names
        classes = sorted([d.name for d in root.iterdir() if d.is_dir()])
        class_to_idx = {cls_name: i for i, cls_name in enumerate(classes)}
        
        # Collect samples
        image_paths: List[Path] = []
        labels: List[int] = []
        
        valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
        
        for cls_name, cls_idx in class_to_idx.items():
            cls_dir = root / cls_name
            for img_path in cls_dir.iterdir():
                if img_path.suffix.lower() in valid_extensions:
                    image_paths.append(img_path)
                    labels.append(cls_idx)
        
        logger.info(
            f"Found {len(image_paths)} images in {len(classes)} classes"
        )
        
        return cls(image_paths, labels, transform), class_to_idx


def get_transforms(
    image_size: int = 224,
    is_training: bool = True,
) -> Callable:
    """Get image transforms.
    
    Args:
        image_size: Target image size.
        is_training: Whether to include training augmentations.
    
    Returns:
        Composed transform function.
    """
    from torchvision import transforms
    
    if is_training:
        return transforms.Compose([
            transforms.RandomResizedCrop(image_size, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(
                brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1
            ),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ])
    else:
        return transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ])


@torch.inference_mode()
def predict_image(
    model: ImageClassifier,
    image: Image.Image,
    transform: Callable,
    class_names: Optional[List[str]] = None,
    device: str = "cuda",
    top_k: int = 5,
) -> List[Dict[str, any]]:
    """Predict class for a single image.
    
    Args:
        model: Trained classifier model.
        image: PIL Image to classify.
        transform: Transform to apply.
        class_names: Optional list of class names.
        device: Device to run inference on.
        top_k: Number of top predictions to return.
    
    Returns:
        List of dicts with class_id, class_name, and probability.
    """
    model.eval()
    model.to(device)
    
    # Preprocess
    input_tensor = transform(image).unsqueeze(0).to(device)
    
    # Forward pass
    output = model(input_tensor)
    probs = F.softmax(output, dim=1).squeeze(0)
    
    # Get top-k predictions
    top_probs, top_indices = torch.topk(probs, min(top_k, len(probs)))
    
    predictions = []
    for prob, idx in zip(top_probs.cpu().numpy(), top_indices.cpu().numpy()):
        pred = {
            "class_id": int(idx),
            "probability": float(prob),
        }
        if class_names is not None:
            pred["class_name"] = class_names[idx]
        predictions.append(pred)
    
    return predictions


# Example usage
if __name__ == "__main__":
    from src.utils.logging import setup_logging
    from src.utils.reproducibility import set_seed
    
    setup_logging(level="INFO")
    set_seed(42)
    
    # Create model
    config = ClassifierConfig(
        model_name="efficientnet_b0",
        num_classes=10,
        pretrained=True,
    )
    model = ImageClassifier(config)
    
    # Test forward pass
    x = torch.randn(2, 3, 224, 224)
    output = model(x)
    
    logger.info(f"Input shape: {x.shape}")
    logger.info(f"Output shape: {output.shape}")
    logger.info("Model initialized successfully!")
