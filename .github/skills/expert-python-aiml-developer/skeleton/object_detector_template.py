"""
Object Detection model template.

This template demonstrates best practices for:
- Using YOLO for object detection
- Proper bounding box handling
- Non-Maximum Suppression (NMS)
- Visualization utilities
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """Bounding box representation.
    
    Coordinates are in [x1, y1, x2, y2] format (top-left and bottom-right corners).
    """
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str = ""
    
    @property
    def width(self) -> float:
        """Box width."""
        return self.x2 - self.x1
    
    @property
    def height(self) -> float:
        """Box height."""
        return self.y2 - self.y1
    
    @property
    def area(self) -> float:
        """Box area."""
        return self.width * self.height
    
    @property
    def center(self) -> Tuple[float, float]:
        """Box center (cx, cy)."""
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
    
    def to_xyxy(self) -> List[float]:
        """Convert to [x1, y1, x2, y2] format."""
        return [self.x1, self.y1, self.x2, self.y2]
    
    def to_xywh(self) -> List[float]:
        """Convert to [x, y, width, height] format."""
        return [self.x1, self.y1, self.width, self.height]
    
    def to_cxcywh(self) -> List[float]:
        """Convert to [center_x, center_y, width, height] format."""
        cx, cy = self.center
        return [cx, cy, self.width, self.height]


@dataclass
class DetectionResult:
    """Detection result for a single image."""
    boxes: List[BoundingBox] = field(default_factory=list)
    image_width: int = 0
    image_height: int = 0
    inference_time_ms: float = 0.0
    
    def __len__(self) -> int:
        return len(self.boxes)
    
    def filter_by_confidence(self, threshold: float) -> "DetectionResult":
        """Filter detections by confidence threshold."""
        filtered_boxes = [b for b in self.boxes if b.confidence >= threshold]
        return DetectionResult(
            boxes=filtered_boxes,
            image_width=self.image_width,
            image_height=self.image_height,
        )
    
    def filter_by_class(self, class_ids: List[int]) -> "DetectionResult":
        """Filter detections by class IDs."""
        filtered_boxes = [b for b in self.boxes if b.class_id in class_ids]
        return DetectionResult(
            boxes=filtered_boxes,
            image_width=self.image_width,
            image_height=self.image_height,
        )


@dataclass
class DetectorConfig:
    """Configuration for object detector."""
    
    model_path: str = "yolov8n.pt"
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    max_detections: int = 100
    device: str = "cuda"
    half_precision: bool = False


class ObjectDetector:
    """Production-ready object detector using Ultralytics YOLO.
    
    This detector provides:
    - Configurable confidence/IOU thresholds
    - Batch inference support
    - Class filtering
    - Visualization utilities
    
    Args:
        config: Detector configuration.
        
    Example:
        >>> detector = ObjectDetector(DetectorConfig())
        >>> image = cv2.imread("image.jpg")
        >>> result = detector.detect(image)
        >>> for box in result.boxes:
        ...     print(f"{box.class_name}: {box.confidence:.2f}")
    """
    
    def __init__(self, config: DetectorConfig) -> None:
        self.config = config
        self._model = None
        self._class_names: Dict[int, str] = {}
    
    def load_model(self) -> None:
        """Load the YOLO model."""
        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError(
                "ultralytics is required. Install with: pip install ultralytics"
            )
        
        logger.info(f"Loading model from {self.config.model_path}")
        self._model = YOLO(self.config.model_path)
        
        # Get class names
        self._class_names = self._model.names
        
        # Apply half precision if requested
        if self.config.half_precision:
            self._model.half()
        
        logger.info(
            f"Model loaded with {len(self._class_names)} classes"
        )
    
    @property
    def class_names(self) -> Dict[int, str]:
        """Get class ID to name mapping."""
        return self._class_names
    
    def detect(
        self,
        image: np.ndarray,
        classes: Optional[List[int]] = None,
    ) -> DetectionResult:
        """Run object detection on a single image.
        
        Args:
            image: Input image in RGB format (H, W, C).
            classes: Optional list of class IDs to filter.
        
        Returns:
            DetectionResult with detected boxes.
        
        Raises:
            RuntimeError: If model is not loaded.
        """
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        import time
        start_time = time.perf_counter()
        
        # Run inference
        results = self._model.predict(
            image,
            conf=self.config.confidence_threshold,
            iou=self.config.iou_threshold,
            max_det=self.config.max_detections,
            device=self.config.device,
            classes=classes,
            verbose=False,
        )
        
        inference_time = (time.perf_counter() - start_time) * 1000
        
        # Parse results
        boxes = []
        for result in results:
            for i, box in enumerate(result.boxes):
                xyxy = box.xyxy[0].cpu().numpy()
                boxes.append(BoundingBox(
                    x1=float(xyxy[0]),
                    y1=float(xyxy[1]),
                    x2=float(xyxy[2]),
                    y2=float(xyxy[3]),
                    confidence=float(box.conf[0].cpu()),
                    class_id=int(box.cls[0].cpu()),
                    class_name=self._class_names.get(int(box.cls[0].cpu()), ""),
                ))
        
        return DetectionResult(
            boxes=boxes,
            image_width=image.shape[1],
            image_height=image.shape[0],
            inference_time_ms=inference_time,
        )
    
    def detect_batch(
        self,
        images: List[np.ndarray],
        classes: Optional[List[int]] = None,
    ) -> List[DetectionResult]:
        """Run detection on multiple images.
        
        Args:
            images: List of images in RGB format.
            classes: Optional list of class IDs to filter.
        
        Returns:
            List of DetectionResult objects.
        """
        results = []
        for image in images:
            result = self.detect(image, classes)
            results.append(result)
        return results


def compute_iou(box1: BoundingBox, box2: BoundingBox) -> float:
    """Compute Intersection over Union (IoU) between two boxes.
    
    Args:
        box1: First bounding box.
        box2: Second bounding box.
    
    Returns:
        IoU value in range [0, 1].
    """
    # Intersection coordinates
    x1 = max(box1.x1, box2.x1)
    y1 = max(box1.y1, box2.y1)
    x2 = min(box1.x2, box2.x2)
    y2 = min(box1.y2, box2.y2)
    
    # Intersection area
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    
    # Union area
    union = box1.area + box2.area - intersection
    
    return intersection / union if union > 0 else 0.0


def non_max_suppression(
    boxes: List[BoundingBox],
    iou_threshold: float = 0.5,
) -> List[BoundingBox]:
    """Apply Non-Maximum Suppression to filter overlapping boxes.
    
    Args:
        boxes: List of bounding boxes.
        iou_threshold: IoU threshold for suppression.
    
    Returns:
        Filtered list of bounding boxes.
    """
    if len(boxes) == 0:
        return []
    
    # Sort by confidence (descending)
    sorted_boxes = sorted(boxes, key=lambda x: x.confidence, reverse=True)
    
    keep = []
    while sorted_boxes:
        # Keep the box with highest confidence
        current = sorted_boxes.pop(0)
        keep.append(current)
        
        # Remove boxes with high IoU overlap
        sorted_boxes = [
            box for box in sorted_boxes
            if compute_iou(current, box) < iou_threshold
        ]
    
    return keep


def draw_detections(
    image: np.ndarray,
    result: DetectionResult,
    color_map: Optional[Dict[int, Tuple[int, int, int]]] = None,
    thickness: int = 2,
    font_scale: float = 0.6,
) -> np.ndarray:
    """Draw detection boxes on image.
    
    Args:
        image: Input image (will be modified in place).
        result: Detection result to draw.
        color_map: Optional mapping of class_id to BGR color.
        thickness: Box line thickness.
        font_scale: Font scale for labels.
    
    Returns:
        Image with drawn detections.
    """
    try:
        import cv2
    except ImportError:
        raise ImportError("OpenCV is required. Install with: pip install opencv-python")
    
    image = image.copy()
    
    # Default color palette
    default_colors = [
        (255, 0, 0), (0, 255, 0), (0, 0, 255),
        (255, 255, 0), (255, 0, 255), (0, 255, 255),
        (128, 0, 0), (0, 128, 0), (0, 0, 128),
    ]
    
    for box in result.boxes:
        # Get color
        if color_map and box.class_id in color_map:
            color = color_map[box.class_id]
        else:
            color = default_colors[box.class_id % len(default_colors)]
        
        # Draw box
        pt1 = (int(box.x1), int(box.y1))
        pt2 = (int(box.x2), int(box.y2))
        cv2.rectangle(image, pt1, pt2, color, thickness)
        
        # Draw label
        label = f"{box.class_name}: {box.confidence:.2f}"
        label_size, baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )
        
        # Label background
        cv2.rectangle(
            image,
            (pt1[0], pt1[1] - label_size[1] - baseline),
            (pt1[0] + label_size[0], pt1[1]),
            color,
            cv2.FILLED,
        )
        
        # Label text
        cv2.putText(
            image,
            label,
            (pt1[0], pt1[1] - baseline),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            thickness,
        )
    
    return image


# Example usage
if __name__ == "__main__":
    import cv2
    from src.utils.logging import setup_logging
    
    setup_logging(level="INFO")
    
    # Create detector
    config = DetectorConfig(
        model_path="yolov8n.pt",
        confidence_threshold=0.5,
        device="cpu",
    )
    detector = ObjectDetector(config)
    
    # Load model
    detector.load_model()
    
    logger.info("Object detector initialized!")
    logger.info(f"Available classes: {list(detector.class_names.values())[:10]}...")
