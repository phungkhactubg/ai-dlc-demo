#!/usr/bin/env python3
"""Training script entrypoint."""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_training_settings
from src.utils import setup_logging, set_seed, log_environment


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Train the model")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/training_config.yaml"),
        help="Path to training config",
    )
    parser.add_argument("--seed", type=int, help="Override config seed")
    parser.add_argument("--epochs", type=int, help="Override config epochs")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    return parser.parse_args()


def main() -> None:
    """Main training function."""
    args = parse_args()
    
    # Setup
    setup_logging(level="DEBUG" if args.debug else "INFO")
    logger = logging.getLogger(__name__)
    
    settings = get_training_settings()
    seed = args.seed if args.seed else settings.seed
    epochs = args.epochs if args.epochs else settings.epochs
    
    set_seed(seed)
    log_environment()
    
    logger.info(f"Starting training for {epochs} epochs...")
    
    # TODO: Implement training loop
    # 1. Load data
    # 2. Create model
    # 3. Train
    # 4. Save checkpoints
    
    logger.info("Training complete!")


if __name__ == "__main__":
    main()
