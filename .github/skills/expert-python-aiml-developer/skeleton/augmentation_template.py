"""
Data Augmentation Pipeline template for Computer Vision.

This template demonstrates best practices for:
- Training vs validation transforms
- Albumentations pipelines
- Custom augmentation strategies
- Reproducible augmentation
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

# Standard normalization constants
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

CIFAR_MEAN = (0.4914, 0.4822, 0.4465)
CIFAR_STD = (0.2470, 0.2435, 0.2616)


class AugmentationLevel(Enum):
    """Augmentation intensity levels."""
    NONE = "none"
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"


@dataclass
class AugmentationConfig:
    """Configuration for augmentation pipeline."""
    
    image_size: int = 224
    level: AugmentationLevel = AugmentationLevel.MEDIUM
    normalize: bool = True
    mean: Tuple[float, ...] = IMAGENET_MEAN
    std: Tuple[float, ...] = IMAGENET_STD
    
    # Geometric transforms
    horizontal_flip_p: float = 0.5
    vertical_flip_p: float = 0.0
    rotation_limit: int = 30
    scale_limit: float = 0.2
    shift_limit: float = 0.1
    
    # Color transforms
    brightness_limit: float = 0.2
    contrast_limit: float = 0.2
    saturation_limit: float = 0.2
    hue_limit: float = 0.1
    
    # Advanced
    mixup_alpha: float = 0.0  # 0 disables mixup
    cutout_p: float = 0.0
    cutout_size: int = 32


def get_torchvision_transforms(
    config: AugmentationConfig,
    is_training: bool = True,
) -> Callable:
    """Get torchvision transforms.
    
    Args:
        config: Augmentation configuration.
        is_training: Whether to include training augmentations.
    
    Returns:
        Composed transform callable.
    """
    from torchvision import transforms
    
    transform_list = []
    
    if is_training:
        # Training transforms with augmentation
        transform_list.extend([
            transforms.RandomResizedCrop(
                config.image_size,
                scale=(1.0 - config.scale_limit, 1.0),
            ),
            transforms.RandomHorizontalFlip(p=config.horizontal_flip_p),
        ])
        
        if config.vertical_flip_p > 0:
            transform_list.append(
                transforms.RandomVerticalFlip(p=config.vertical_flip_p)
            )
        
        if config.rotation_limit > 0:
            transform_list.append(
                transforms.RandomRotation(config.rotation_limit)
            )
        
        if config.level != AugmentationLevel.NONE:
            transform_list.append(
                transforms.ColorJitter(
                    brightness=config.brightness_limit,
                    contrast=config.contrast_limit,
                    saturation=config.saturation_limit,
                    hue=config.hue_limit,
                )
            )
    else:
        # Validation/inference transforms (NO random augmentation!)
        transform_list.extend([
            transforms.Resize((config.image_size, config.image_size)),
        ])
    
    # Common transforms
    transform_list.append(transforms.ToTensor())
    
    if config.normalize:
        transform_list.append(
            transforms.Normalize(mean=config.mean, std=config.std)
        )
    
    return transforms.Compose(transform_list)


def get_albumentations_transforms(
    config: AugmentationConfig,
    is_training: bool = True,
) -> Any:
    """Get Albumentations transforms.
    
    Args:
        config: Augmentation configuration.
        is_training: Whether to include training augmentations.
    
    Returns:
        Albumentations Compose pipeline.
    """
    try:
        import albumentations as A
        from albumentations.pytorch import ToTensorV2
    except ImportError:
        raise ImportError(
            "albumentations is required. Install with: "
            "pip install albumentations"
        )
    
    transform_list = []
    
    # Resize
    transform_list.append(A.Resize(config.image_size, config.image_size))
    
    if is_training:
        # Geometric transforms
        if config.horizontal_flip_p > 0:
            transform_list.append(A.HorizontalFlip(p=config.horizontal_flip_p))
        
        if config.vertical_flip_p > 0:
            transform_list.append(A.VerticalFlip(p=config.vertical_flip_p))
        
        if config.level != AugmentationLevel.NONE:
            transform_list.append(
                A.ShiftScaleRotate(
                    shift_limit=config.shift_limit,
                    scale_limit=config.scale_limit,
                    rotate_limit=config.rotation_limit,
                    border_mode=0,  # cv2.BORDER_CONSTANT
                    p=0.5,
                )
            )
        
        # Color transforms based on level
        if config.level == AugmentationLevel.LIGHT:
            transform_list.append(
                A.RandomBrightnessContrast(
                    brightness_limit=config.brightness_limit * 0.5,
                    contrast_limit=config.contrast_limit * 0.5,
                    p=0.3,
                )
            )
        elif config.level == AugmentationLevel.MEDIUM:
            transform_list.append(
                A.OneOf([
                    A.RandomBrightnessContrast(
                        brightness_limit=config.brightness_limit,
                        contrast_limit=config.contrast_limit,
                    ),
                    A.HueSaturationValue(
                        hue_shift_limit=int(config.hue_limit * 180),
                        sat_shift_limit=int(config.saturation_limit * 100),
                        val_shift_limit=int(config.brightness_limit * 100),
                    ),
                ], p=0.5)
            )
        elif config.level == AugmentationLevel.HEAVY:
            transform_list.extend([
                A.OneOf([
                    A.RandomBrightnessContrast(
                        brightness_limit=config.brightness_limit,
                        contrast_limit=config.contrast_limit,
                    ),
                    A.HueSaturationValue(
                        hue_shift_limit=int(config.hue_limit * 180),
                        sat_shift_limit=int(config.saturation_limit * 100),
                        val_shift_limit=int(config.brightness_limit * 100),
                    ),
                    A.ColorJitter(
                        brightness=config.brightness_limit,
                        contrast=config.contrast_limit,
                        saturation=config.saturation_limit,
                        hue=config.hue_limit,
                    ),
                ], p=0.7),
                A.OneOf([
                    A.GaussNoise(var_limit=(10.0, 50.0)),
                    A.GaussianBlur(blur_limit=3),
                    A.MotionBlur(blur_limit=3),
                ], p=0.3),
            ])
        
        # Cutout/CoarseDropout
        if config.cutout_p > 0:
            transform_list.append(
                A.CoarseDropout(
                    max_holes=4,
                    max_height=config.cutout_size,
                    max_width=config.cutout_size,
                    min_holes=1,
                    min_height=config.cutout_size // 2,
                    min_width=config.cutout_size // 2,
                    fill_value=0,
                    p=config.cutout_p,
                )
            )
    
    # Normalize
    if config.normalize:
        transform_list.append(
            A.Normalize(mean=config.mean, std=config.std)
        )
    
    # Convert to tensor
    transform_list.append(ToTensorV2())
    
    return A.Compose(transform_list)


def mixup(
    images: "torch.Tensor",
    labels: "torch.Tensor",
    alpha: float = 0.2,
) -> Tuple["torch.Tensor", "torch.Tensor", "torch.Tensor", float]:
    """Apply MixUp augmentation.
    
    Args:
        images: Batch of images (B, C, H, W).
        labels: Batch of labels (B,) or (B, num_classes).
        alpha: Beta distribution parameter.
    
    Returns:
        Tuple of (mixed_images, labels_a, labels_b, lambda).
    """
    import torch
    
    if alpha <= 0:
        return images, labels, labels, 1.0
    
    batch_size = images.size(0)
    
    # Sample lambda from beta distribution
    lam = np.random.beta(alpha, alpha)
    
    # Random permutation
    index = torch.randperm(batch_size, device=images.device)
    
    # Mix images
    mixed_images = lam * images + (1 - lam) * images[index]
    
    return mixed_images, labels, labels[index], lam


def cutmix(
    images: "torch.Tensor",
    labels: "torch.Tensor",
    alpha: float = 1.0,
) -> Tuple["torch.Tensor", "torch.Tensor", "torch.Tensor", float]:
    """Apply CutMix augmentation.
    
    Args:
        images: Batch of images (B, C, H, W).
        labels: Batch of labels (B,) or (B, num_classes).
        alpha: Beta distribution parameter.
    
    Returns:
        Tuple of (mixed_images, labels_a, labels_b, lambda).
    """
    import torch
    
    if alpha <= 0:
        return images, labels, labels, 1.0
    
    batch_size = images.size(0)
    h, w = images.size(2), images.size(3)
    
    # Sample lambda from beta distribution
    lam = np.random.beta(alpha, alpha)
    
    # Random permutation
    index = torch.randperm(batch_size, device=images.device)
    
    # Get random box
    cut_ratio = np.sqrt(1.0 - lam)
    cut_h = int(h * cut_ratio)
    cut_w = int(w * cut_ratio)
    
    cx = np.random.randint(w)
    cy = np.random.randint(h)
    
    x1 = np.clip(cx - cut_w // 2, 0, w)
    y1 = np.clip(cy - cut_h // 2, 0, h)
    x2 = np.clip(cx + cut_w // 2, 0, w)
    y2 = np.clip(cy + cut_h // 2, 0, h)
    
    # Apply cutmix
    mixed_images = images.clone()
    mixed_images[:, :, y1:y2, x1:x2] = images[index, :, y1:y2, x1:x2]
    
    # Adjust lambda based on actual box size
    lam = 1 - ((x2 - x1) * (y2 - y1) / (h * w))
    
    return mixed_images, labels, labels[index], lam


def denormalize(
    tensor: "torch.Tensor",
    mean: Tuple[float, ...] = IMAGENET_MEAN,
    std: Tuple[float, ...] = IMAGENET_STD,
) -> "torch.Tensor":
    """Denormalize a tensor for visualization.
    
    Args:
        tensor: Normalized tensor (C, H, W) or (B, C, H, W).
        mean: Normalization mean.
        std: Normalization std.
    
    Returns:
        Denormalized tensor with values in [0, 1].
    """
    import torch
    
    mean_t = torch.tensor(mean, device=tensor.device)
    std_t = torch.tensor(std, device=tensor.device)
    
    if tensor.dim() == 4:
        # Batch: (B, C, H, W)
        mean_t = mean_t.view(1, -1, 1, 1)
        std_t = std_t.view(1, -1, 1, 1)
    else:
        # Single image: (C, H, W)
        mean_t = mean_t.view(-1, 1, 1)
        std_t = std_t.view(-1, 1, 1)
    
    denorm = tensor * std_t + mean_t
    return torch.clamp(denorm, 0, 1)


def tensor_to_numpy(
    tensor: "torch.Tensor",
    denorm: bool = True,
    mean: Tuple[float, ...] = IMAGENET_MEAN,
    std: Tuple[float, ...] = IMAGENET_STD,
) -> np.ndarray:
    """Convert tensor to numpy array for visualization.
    
    Args:
        tensor: Input tensor (C, H, W) or (B, C, H, W).
        denorm: Whether to denormalize.
        mean: Normalization mean.
        std: Normalization std.
    
    Returns:
        Numpy array in (H, W, C) or (B, H, W, C) format with values in [0, 255].
    """
    if denorm:
        tensor = denormalize(tensor, mean, std)
    
    # Move to CPU and convert to numpy
    arr = tensor.cpu().numpy()
    
    # Transpose from (C, H, W) to (H, W, C)
    if arr.ndim == 3:
        arr = np.transpose(arr, (1, 2, 0))
    elif arr.ndim == 4:
        arr = np.transpose(arr, (0, 2, 3, 1))
    
    # Scale to [0, 255]
    arr = (arr * 255).astype(np.uint8)
    
    return arr


# Example usage
if __name__ == "__main__":
    from src.utils.logging import setup_logging
    
    setup_logging(level="INFO")
    
    # Create config
    config = AugmentationConfig(
        image_size=224,
        level=AugmentationLevel.MEDIUM,
    )
    
    # Get transforms
    train_transform = get_albumentations_transforms(config, is_training=True)
    val_transform = get_albumentations_transforms(config, is_training=False)
    
    logger.info("Training transform pipeline created:")
    logger.info(f"  Augmentation level: {config.level.value}")
    logger.info(f"  Image size: {config.image_size}")
    logger.info(f"  Normalize: {config.normalize}")
    
    logger.info("\nValidation transform pipeline created (NO random augmentations)")
