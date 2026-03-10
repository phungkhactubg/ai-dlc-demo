"""Data loading utilities."""
import logging
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def load_image(
    path: Path,
    mode: str = "RGB",
) -> Image.Image:
    """Load image from path.
    
    Args:
        path: Path to image file.
        mode: Image mode (RGB, L, etc.).
    
    Returns:
        PIL Image object.
    
    Raises:
        FileNotFoundError: If image doesn't exist.
        ValueError: If image cannot be loaded.
    """
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    
    try:
        image = Image.open(path).convert(mode)
        return image
    except Exception as e:
        raise ValueError(f"Failed to load image {path}: {e}") from e


def get_image_paths(
    directory: Path,
    extensions: Optional[set] = None,
) -> List[Path]:
    """Get all image paths in a directory.
    
    Args:
        directory: Directory to search.
        extensions: Set of valid extensions. Defaults to common image formats.
    
    Returns:
        List of image paths.
    """
    if extensions is None:
        extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
    
    paths = []
    for ext in extensions:
        paths.extend(directory.glob(f"**/*{ext}"))
        paths.extend(directory.glob(f"**/*{ext.upper()}"))
    
    return sorted(set(paths))


def create_train_val_split(
    paths: List[Path],
    labels: List[int],
    val_ratio: float = 0.2,
    seed: int = 42,
) -> Tuple[List[Path], List[int], List[Path], List[int]]:
    """Split data into train and validation sets.
    
    Args:
        paths: List of file paths.
        labels: List of labels.
        val_ratio: Validation set ratio.
        seed: Random seed for reproducibility.
    
    Returns:
        Tuple of (train_paths, train_labels, val_paths, val_labels).
    """
    np.random.seed(seed)
    indices = np.random.permutation(len(paths))
    
    val_size = int(len(paths) * val_ratio)
    val_indices = indices[:val_size]
    train_indices = indices[val_size:]
    
    train_paths = [paths[i] for i in train_indices]
    train_labels = [labels[i] for i in train_indices]
    val_paths = [paths[i] for i in val_indices]
    val_labels = [labels[i] for i in val_indices]
    
    logger.info(f"Split: {len(train_paths)} train, {len(val_paths)} val")
    
    return train_paths, train_labels, val_paths, val_labels
