"""Reproducibility utilities for ML experiments."""
import os
import random
import logging
from typing import Dict, Any

import numpy as np

logger = logging.getLogger(__name__)


def set_seed(seed: int = 42, deterministic: bool = True) -> None:
    """Set random seeds for reproducibility.
    
    Sets seeds for Python random, NumPy, and PyTorch (if available).
    
    Args:
        seed: Random seed value.
        deterministic: If True, set CUDA to deterministic mode.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            if deterministic:
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
        logger.info(f"Set PyTorch seed to {seed}")
    except ImportError:
        pass
    
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
        if deterministic:
            tf.config.experimental.enable_op_determinism()
        logger.info(f"Set TensorFlow seed to {seed}")
    except ImportError:
        pass
    
    logger.info(f"Set global random seed to {seed}")


def log_environment() -> Dict[str, Any]:
    """Log environment information for reproducibility.
    
    Returns:
        Dictionary with environment details.
    """
    import sys
    import platform
    
    env_info: Dict[str, Any] = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "numpy_version": np.__version__,
    }
    
    try:
        import torch
        env_info["torch_version"] = torch.__version__
        env_info["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            env_info["cuda_version"] = torch.version.cuda
            env_info["gpu_count"] = torch.cuda.device_count()
            env_info["gpu_name"] = torch.cuda.get_device_name(0)
    except ImportError:
        pass
    
    for key, value in env_info.items():
        logger.info(f"{key}: {value}")
    
    return env_info
