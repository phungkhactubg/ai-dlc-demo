"""Pytest configuration and fixtures."""
import pytest
import numpy as np


@pytest.fixture
def seed() -> int:
    """Random seed for reproducibility."""
    return 42


@pytest.fixture(autouse=True)
def set_random_seed(seed: int) -> None:
    """Set random seed before each test."""
    import random
    random.seed(seed)
    np.random.seed(seed)
    
    try:
        import torch
        torch.manual_seed(seed)
    except ImportError:
        pass


@pytest.fixture
def sample_image() -> np.ndarray:
    """Sample image array for testing."""
    return np.random.rand(224, 224, 3).astype(np.float32)


@pytest.fixture
def sample_batch() -> np.ndarray:
    """Sample batch of images."""
    return np.random.rand(4, 3, 224, 224).astype(np.float32)
