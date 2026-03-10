"""Data preprocessing utilities."""
import logging
from typing import Callable, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Standard normalization constants
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def get_transforms(
    image_size: int = 224,
    is_training: bool = True,
    mean: Tuple[float, ...] = IMAGENET_MEAN,
    std: Tuple[float, ...] = IMAGENET_STD,
) -> Callable:
    """Get image transforms.
    
    Args:
        image_size: Target image size.
        is_training: Whether to include training augmentations.
        mean: Normalization mean.
        std: Normalization std.
    
    Returns:
        Composed transform function.
    """
    from torchvision import transforms
    
    if is_training:
        return transforms.Compose([
            transforms.RandomResizedCrop(image_size, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ])
    else:
        return transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ])


def normalize_image(
    image: np.ndarray,
    mean: Tuple[float, ...] = IMAGENET_MEAN,
    std: Tuple[float, ...] = IMAGENET_STD,
) -> np.ndarray:
    """Normalize image array.
    
    Args:
        image: Image array in [0, 1] range, shape (H, W, C).
        mean: Per-channel mean.
        std: Per-channel std.
    
    Returns:
        Normalized image array.
    """
    mean_arr = np.array(mean).reshape(1, 1, -1)
    std_arr = np.array(std).reshape(1, 1, -1)
    return (image - mean_arr) / std_arr


def denormalize_image(
    image: np.ndarray,
    mean: Tuple[float, ...] = IMAGENET_MEAN,
    std: Tuple[float, ...] = IMAGENET_STD,
) -> np.ndarray:
    """Denormalize image array for visualization.
    
    Args:
        image: Normalized image array, shape (H, W, C).
        mean: Per-channel mean.
        std: Per-channel std.
    
    Returns:
        Denormalized image array in [0, 1] range.
    """
    mean_arr = np.array(mean).reshape(1, 1, -1)
    std_arr = np.array(std).reshape(1, 1, -1)
    return np.clip(image * std_arr + mean_arr, 0, 1)
