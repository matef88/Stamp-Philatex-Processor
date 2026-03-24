"""
Stamp Philatex Processor - Main Processing Engine
Detects, aligns, and crops stamps from images using YOLOv8 segmentation.

Enhanced features:
- AMD GPU support via DirectML
- iPhone HEIC format support
- Black background optimization
- Confidence scoring
- Parallel batch processing
- eBay-optimized output
"""

import cv2
import numpy as np
import argparse
import os
import sys
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Import YOLO
from ultralytics import YOLO
from tqdm import tqdm

# Local imports
try:
    from utils import (
        load_config, setup_logging, ensure_dirs, get_project_root,
        get_image_files, convert_heic_to_jpg, batch_convert_heic_to_jpg, get_device,
        ProgressTracker, format_duration
    )
    from duplicate_detector import DuplicateDetector
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from scripts.utils import (
        load_config, setup_logging, ensure_dirs, get_project_root,
        get_image_files, convert_heic_to_jpg, batch_convert_heic_to_jpg, get_device,
        ProgressTracker, format_duration
    )
    from duplicate_detector import DuplicateDetector, DuplicateMatch
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from scripts.utils import (
        load_config, setup_logging, ensure_dirs, get_project_root,
        get_image_files, convert_heic_to_jpg, batch_convert_heic_to_jpg, get_device,
        ProgressTracker, format_duration
    )
    from scripts.duplicate_detector import DuplicateDetector, DuplicateMatch


@dataclass
class ProcessingResult:
    """Result of processing a single image."""
    input_path: Path
    output_path: Optional[Path]
    success: bool
    confidence: float
    num_detections: int
    processing_time: float
    error_message: Optional[str] = None
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    skipped: bool = False


class StampProcessor:
    """
    Main stamp processing engine.
    Handles detection, alignment, cropping, and output generation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the stamp processor.

        Args:
            config: Configuration dictionary. If None, loads from config.yaml
        """
        self.config = config or load_config()
        self.logger = setup_logging(
            "StampProcessor",
            level=self.config.get('logging', {}).get('level', 'INFO'),
            log_file=self.config.get('logging', {}).get('log_file')
        )

        # Initialize paths
        self.project_root = get_project_root()
        self._setup_paths()

        # Initialize model (lazy loading)
        self._model = None

        # Processing statistics
        self.stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'duplicates': 0
        }

        # Initialize duplicate detector
        self.duplicate_detector = DuplicateDetector(self.config)

        # Log environment details
        self.logger.info("="*50)
        self.logger.info(f"StampProcessor Initialized")
        self.logger.info(f"Python: {sys.version}")
        self.logger.info(f"Executable: {sys.executable}")
        self.logger.info(f"Device: {self.config.get('hardware', {}).get('device', 'auto')}")
        self.logger.info("="*50)

    def ensure_model_loaded(self):
        """Ensure model is loaded (safe to call multiple times)."""
        if self._model is None:
            self._load_model()

    def _setup_paths(self) -> None:
        """Setup output directories (paths only, no directory creation)."""
        paths_config = self.config.get('paths', {})

        # Initialize paths but DON'T create directories yet
        # Directories will be created by set_output_from_input() with dynamic paths
        self.output_dir = self.project_root / paths_config.get('output', 'output')
        self.crops_dir = self.output_dir / 'crops'
        self.visuals_dir = self.output_dir / 'visuals'
        self.reports_dir = self.output_dir / 'reports'

        # IMPORTANT: Do NOT call ensure_dirs() here!
        # This prevents creating folders in exe location before dynamic path is set

    def set_output_from_input(self, input_path: Path) -> None:
        """
        Dynamically set output directory based on input path.
        Output will be nested inside the input directory:
        <InputDirectory>/crops
        """
        if input_path.is_file():
            base_dir = input_path.parent
        else:
            base_dir = input_path
        
        self.output_dir = base_dir
        self.crops_dir = self.output_dir / 'crops'
        self.visuals_dir = self.output_dir / 'visuals'
        self.reports_dir = self.output_dir / 'reports'
        
        self.logger.info(f"Dynamic output directory set to: {self.output_dir} (crops in ./crops)")
        ensure_dirs([self.crops_dir, self.visuals_dir, self.reports_dir])

    @property
    def model(self) -> YOLO:
        """Lazy-load the YOLO model."""
        if self._model is None:
            self._load_model()
        return self._model

    def _load_model(self) -> None:
        """Load the YOLOv8 segmentation model."""
        model_path = self.config.get('paths', {}).get('model_weights', 'yolov8n-seg.pt')

        # Use get_resource_path for frozen exe compatibility
        try:
            from utils import get_resource_path, get_device
        except ImportError:
            # Fallback for direct script execution
            from scripts.utils import get_resource_path, get_device

        # Resolve model path using get_resource_path
        # This checks _MEIPASS first (bundled), then project root
        full_model_path = get_resource_path(model_path)
            
        if full_model_path.exists():
            model_name = str(full_model_path)
            self.logger.info(f"Loading custom model: {model_name}")
        else:
            # Fall back to base model
            model_name = 'yolov8n-seg.pt'
            self.logger.warning(f"Custom model not found at {full_model_path}")
            self.logger.info(f"Using base model: {model_name}")

        # Check for DirectML / ONNX optimization
        device_config = self.config.get('hardware', {}).get('device', 'auto')
        detected_device = get_device(device_config)
        
        use_onnx = False
        # If user explicitly wants DirectML or we detected it (privateuseone)
        if detected_device == 'privateuseone' or device_config == 'directml':
            try:
                import onnx
                import onnxruntime
                use_onnx = True
            except ImportError:
                self.logger.warning("DirectML selected but onnx/onnxruntime not found. Using PyTorch fallback.")

        if use_onnx and full_model_path.exists():
            onnx_path = full_model_path.with_suffix('.onnx')
            if not onnx_path.exists():
                self.logger.info("Exporting model to ONNX for DirectML optimization...")
                try:
                    # Load PT model just for export
                    temp_model = YOLO(model_name)
                    # Export - using dynamic=True for flexible batch sizes
                    temp_model.export(format='onnx', dynamic=True) 
                    self.logger.info(f"Exported to {onnx_path}")
                except Exception as e:
                    self.logger.error(f"ONNX export failed: {e}")
                    use_onnx = False
            
            if use_onnx and onnx_path.exists():
                model_name = str(onnx_path)
                self.logger.info(f"Using ONNX runtime model: {model_name}")
                # Set device to CPU so we don't pass DirectML objects to ONNX model predict
                self.device = 'cpu' 
                self._model = YOLO(model_name, task='segment')
                return # Done loading

        self._model = YOLO(model_name, task='segment')

        # Set device
        self.device = detected_device
        
        # Handle DirectML for PyTorch
        if self.device == "privateuseone":
            try:
                import torch_directml
                self.device = torch_directml.device()
                self.logger.info(f"Using DirectML device object: {self.device}")
            except ImportError:
                self.logger.warning("Could not import torch_directml despite it being selected. Falling back to CPU.")
                self.device = 'cpu'
        else:
            self.logger.info(f"Using device: {self.device}")

    def _generate_texture(self, height: int, width: int) -> np.ndarray:
        """
        Generate a green noise texture.

        Args:
            height: Texture height
            width: Texture width

        Returns:
            BGR numpy array with textured background
        """
        bg_config = self.config.get('background', {})
        color = tuple(bg_config.get('color', [51, 112, 68]))
        noise_level = bg_config.get('noise_level', 10)

        # Create base color
        base = np.full((height, width, 3), color, dtype=np.uint8)

        # Add noise
        noise = np.random.normal(0, noise_level, (height, width, 3)).astype(np.int16)
        textured = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        return textured

    def _load_texture(self, height: int, width: int) -> np.ndarray:
        """
        Load or generate background texture.
        
        Args:
            height: Required height
            width: Required width

        Returns:
            BGR numpy array with texture
        """
        bg_config = self.config.get('background', {})
        texture_path = self.project_root / bg_config.get('texture_path', 'assets/green_texture.jpg')

        # Check if color is custom (different from default green)
        # If custom, we prefer generating a new texture with that color
        # rather than loading the static green file.
        current_color = list(bg_config.get('color', [51, 112, 68]))
        default_color = [51, 112, 68]
        
        if current_color != default_color:
            return self._generate_texture(height, width)

        if texture_path.exists():
            texture = cv2.imread(str(texture_path))
            if texture is not None:
                return cv2.resize(texture, (width, height))

        return self._generate_texture(height, width)

    def _preprocess_image(self, img_path: Path) -> Tuple[np.ndarray, Path]:
        """
        Preprocess image (handle HEIC conversion, etc.).

        Args:
            img_path: Path to input image

        Returns:
            Tuple of (image array, actual path used)
        """
        # Handle HEIC conversion (fallback for individual files)
        # Note: Batch preprocessing should handle most HEIC files
        # This is a safety fallback for edge cases
        if img_path.suffix.lower() in ['.heic', '.heif']:
            if self.config.get('input', {}).get('auto_convert_heic', True):
                jpg_path = img_path.with_suffix('.jpg')
                if not jpg_path.exists():
                    self.logger.debug(f"Converting HEIC (fallback): {img_path}")
                    convert_heic_to_jpg(img_path, jpg_path)
                img_path = jpg_path

        # Read image
        try:
            img = cv2.imread(str(img_path))
        except Exception as e:
            raise ValueError(f"Failed to read image file: {e}")

        if img is None:
            raise ValueError(f"Could not decode image (corrupt or unsupported): {img_path}")

        if img is None:
            raise ValueError(f"Could not read image: {img_path}")

        return img, img_path

    def _calculate_rotation(
        self,
        hull: np.ndarray,
        individual_hulls: List[np.ndarray] = None,
        img: np.ndarray = None
    ) -> float:
        """
        Calculate optimal rotation angle to align stamp edges.
        
        Strategy:
        - Strictly uses MinAreaRect (Minimum Area Rectangle) of the outer boundary.
        - Verified to provide robust alignment for stamps.
        
        Args:
            hull: Convex hull points (combined)
            individual_hulls: List of hulls for individual stamps (unused in this strategy but kept for interface)
            img: Source image (unused in this strategy but kept for interface)

        Returns:
            Rotation angle in degrees
        """
        try:
            if hull is None or len(hull) < 3:
                return 0.0

            # Get the rotated rectangle
            rect = cv2.minAreaRect(hull)
            (cx, cy), (width, height), angle = rect

            # Orientation Logic (Verified in debug notebook)
            final_rotation = angle
            
            # Adjust for Portrait vs Landscape
            # OpenCV's MinAreaRect angle is [0, 90) relative to one side.
            # We normalize based on the assumption that the "width" should be the horizontal side.
            if width < height:
                final_rotation -= 90

            # Normalize to [-45, 45] range
            # We assume stamps are not rotated more than 45 degrees
            while final_rotation > 45:
                final_rotation -= 90
            while final_rotation < -45:
                final_rotation += 90

            # Final verified logic: 
            # The MinAreaRect angle (after normalization) is the direct correction needed.
            # Positive angle rotates clockwise, correcting a counter-clockwise tilt.
            best_rotation = final_rotation

            self.logger.debug(f"MinAreaRect: raw={angle:.2f}, dim={width:.0f}x{height:.0f}, result={best_rotation:.2f}°")

            # Limit rotation to configured max
            max_angle = self.config.get('processing', {}).get('max_rotation_angle', 45)
            if abs(best_rotation) > max_angle:
                self.logger.warning(f"Calculated rotation {best_rotation:.2f}° exceeds max {max_angle}°, ignoring.")
                return 0.0

            return best_rotation

        except Exception as e:
            self.logger.error(f"Rotation calculation failed: {e}")
            return 0.0



    def _rotate_image(
        self,
        img: np.ndarray,
        hull: np.ndarray,
        angle: float,
        bg_color: Tuple[int, int, int]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Rotate image and transform hull points.

        Args:
            img: Input image
            hull: Convex hull points
            angle: Rotation angle in degrees
            bg_color: Background color for border fill

        Returns:
            Tuple of (rotated image, transformed hull)
        """
        h, w = img.shape[:2]

        # Get center from hull
        rect = cv2.minAreaRect(hull)
        center = rect[0]

        # Rotation matrix
        M = cv2.getRotationMatrix2D(center, angle, 1.0)

        # Calculate new image size to prevent cropping
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))

        # Adjust translation
        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]

        # Rotate image
        rotated = cv2.warpAffine(
            img, M, (new_w, new_h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=bg_color
        )

        # Transform hull points
        # Use reshape to handle cases with few points reliably
        points = hull.reshape(-1, 2)
        ones = np.ones((len(points), 1))
        points_ones = np.hstack([points, ones])
        transformed = M.dot(points_ones.T).T
        transformed_hull = transformed.astype(np.int32).reshape((-1, 1, 2))

        return rotated, transformed_hull

    def _crop_with_margins(
        self,
        img: np.ndarray,
        hull: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, Tuple[int, int, int, int]]:
        """
        Crop image with context margin.

        Args:
            img: Input image
            hull: Convex hull points

        Returns:
            Tuple of (cropped image, adjusted hull, crop bounds)
        """
        proc_config = self.config.get('processing', {})
        expand_pct = proc_config.get('expand_margin_percent', 0.05)

        # Get bounding box
        x, y, w, h = cv2.boundingRect(hull)

        # Calculate margins
        margin_w = int(w * expand_pct)
        margin_h = int(h * expand_pct)

        # Expand bounds with image limits
        img_h, img_w = img.shape[:2]
        x1 = max(0, x - margin_w)
        y1 = max(0, y - margin_h)
        x2 = min(img_w, x + w + margin_w)
        y2 = min(img_h, y + h + margin_h)

        # Crop
        cropped = img[y1:y2, x1:x2]

        # Adjust hull to crop coordinates
        adjusted_hull = hull.copy()
        adjusted_hull[:, :, 0] -= x1
        adjusted_hull[:, :, 1] -= y1

        return cropped, adjusted_hull, (x1, y1, x2, y2)

    def _add_texture_border(
        self,
        img: np.ndarray,
        hull: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Add textured border around image.

        Args:
            img: Input image
            hull: Hull points (in image coordinates)

        Returns:
            Tuple of (bordered image, adjusted hull)
        """
        proc_config = self.config.get('processing', {})
        texture_pct = proc_config.get('texture_margin_percent', 0.10)

        h, w = img.shape[:2]

        # Calculate border sizes
        border_w = int(w * texture_pct)
        border_h = int(h * texture_pct)

        # Final dimensions
        final_w = w + (border_w * 2)
        final_h = h + (border_h * 2)

        # Create textured background
        background = self._load_texture(final_h, final_w)

        # Place image on background
        background[border_h:border_h+h, border_w:border_w+w] = img

        # Adjust hull coordinates
        adjusted_hull = hull.copy()
        adjusted_hull[:, :, 0] += border_w
        adjusted_hull[:, :, 1] += border_h

        return background, adjusted_hull

    def _normalize_aspect_ratio(
        self,
        img: np.ndarray,
        hull: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Normalize aspect ratio by adding texture padding to short side.

        Args:
            img: Input image (already textured)
            hull: Hull points

        Returns:
            Tuple of (normalized image, adjusted hull)
        """
        proc_config = self.config.get('processing', {})
        if not proc_config.get('normalize_aspect_ratio', True):
            return img, hull

        max_ratio = proc_config.get('max_aspect_ratio', 2.5)
        
        h, w = img.shape[:2]
        
        # Calculate current ratio
        if h == 0 or w == 0:
            return img, hull
            
        current_max = max(h, w)
        current_min = min(h, w)
        current_ratio = current_max / current_min
        
        if current_ratio <= max_ratio:
            return img, hull
            
        self.logger.info(f"Normalizing aspect ratio: {current_ratio:.2f} -> {max_ratio}")
        
        # Calculate new dimensions
        target_min = int(current_max / max_ratio)
        padding_needed = target_min - current_min
        
        if padding_needed <= 0:
            return img, hull
            
        # Distribute padding
        pad_1 = padding_needed // 2
        pad_2 = padding_needed - pad_1
        
        # Determine orientation and create new canvas
        if w > h:
            # Landscape strip, need more height
            new_w = w
            new_h = h + padding_needed
            
            # Offsets for original image
            off_x = 0
            off_y = pad_1
            
        else:
            # Portrait strip, need more width
            new_w = w + padding_needed
            new_h = h
            
            # Offsets for original image
            off_x = pad_1
            off_y = 0
            
        # Create textured background
        # We reuse _load_texture but might need to be careful if it returns specific size 
        # (it does, so this works)
        background = self._load_texture(new_h, new_w)
        
        # Place original image in center
        background[off_y:off_y+h, off_x:off_x+w] = img
        
        # Adjust hull
        adjusted_hull = hull.copy()
        adjusted_hull[:, :, 0] += off_x
        adjusted_hull[:, :, 1] += off_y
        
        return background, adjusted_hull

    def _draw_alignment(self, img: np.ndarray, hull: np.ndarray) -> np.ndarray:
        """
        Draw alignment line on image.

        Args:
            img: Image to draw on
            hull: Hull points

        Returns:
            Image with alignment visualization
        """
        result = img.copy()
        if hull is None or len(hull) == 0:
            return result
            
        try:
            cv2.drawContours(result, [hull], 0, (0, 255, 0), 2)
        except Exception as e:
            self.logger.warning(f"Failed to draw alignment: {e}")
            
        return result

    def _resize_for_ebay(self, img: np.ndarray) -> np.ndarray:
        """
        Resize image for eBay if needed.

        Args:
            img: Input image

        Returns:
            Resized image (or original if within limits)
        """
        proc_config = self.config.get('processing', {})
        max_dim = proc_config.get('ebay_max_dimension', 1600)
        preserve_ratio = proc_config.get('preserve_aspect_ratio', True)

        h, w = img.shape[:2]
        max_current = max(h, w)

        if max_current <= max_dim:
            return img

        if preserve_ratio:
            scale = max_dim / max_current
            new_w = int(w * scale)
            new_h = int(h * scale)
            return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        return img

    def process_single_image(self, img_path: Path, fast_mode: bool = False) -> ProcessingResult:
        """
        Process a single image.

        Args:
            img_path: Path to input image

        Returns:
            ProcessingResult with processing details
        """
        start_time = time.time()

        try:
            # Ensure model is loaded (on the current thread)
            self.ensure_model_loaded()

            # Check if we should skip already processed files
            proc_config = self.config.get('processing', {})
            output_format = proc_config.get('output_format', 'jpg')
            expected_output = self.crops_dir / f"{img_path.stem}_processed.{output_format}"
            
            if proc_config.get('skip_processed', False):
                if expected_output.exists():
                    return ProcessingResult(
                        input_path=img_path,
                        output_path=None,
                        success=True,
                        confidence=0.0,
                        num_detections=0,
                        processing_time=0.0,
                        skipped=True,
                        error_message="Skipped (Already Processed)"
                    )

            # Preprocess
            img, actual_path = self._preprocess_image(img_path)
            h0, w0 = img.shape[:2]

            # Get config values
            proc_config = self.config.get('processing', {})
            bg_color = tuple(self.config.get('background', {}).get('color', [51, 112, 68]))

            # Run detection
            # Run detection with fallback for DirectML stability
            try:
                results = self.model.predict(
                    source=str(actual_path),
                    verbose=False,
                    task='segment',
                    conf=self.config.get('detection', {}).get('confidence_threshold', 0.5),
                    iou=self.config.get('detection', {}).get('iou_threshold', 0.45),
                    device=self.device
                )
            except Exception as e:
                # Check for specific DirectML/Tensor errors
                if "version_counter" in str(e) or "NotImplemented" in str(e) and str(self.device) != 'cpu':
                    self.logger.warning(f"GPU/DirectML Error: {e}")
                    self.logger.warning("Falling back to CPU for this and future images (reloading model).")
                    self.device = 'cpu'
                    if 'hardware' not in self.config: self.config['hardware'] = {}
                    self.config['hardware']['device'] = 'cpu' # Prevent reloading on GPU
                    self._model = None # Force reload on next access
                    # Retry on CPU
                    results = self.model.predict(
                        source=str(actual_path),
                        verbose=False,
                        task='segment',
                        conf=self.config.get('detection', {}).get('confidence_threshold', 0.5),
                        iou=self.config.get('detection', {}).get('iou_threshold', 0.45),
                        device='cpu'
                    )
                else:
                    raise e

            for r in results:
                # Save debug visualization
                if proc_config.get('save_visuals', True) and not fast_mode:
                    debug_img = r.plot()
                    debug_path = self.visuals_dir / f"{img_path.stem}_debug.jpg"
                    cv2.imwrite(str(debug_path), debug_img)

                # Check for detections
                if r.masks is None:
                    return ProcessingResult(
                        input_path=img_path,
                        output_path=None,
                        success=False,
                        confidence=0.0,
                        num_detections=0,
                        processing_time=time.time() - start_time,
                        error_message="No stamps detected"
                    )

                # Get masks and merge
                masks_xy = r.masks.xy
                all_points = []
                confidences = []

                for i, mask in enumerate(masks_xy):
                    if len(mask) > 0:
                        all_points.append(mask)
                        if r.boxes is not None and len(r.boxes.conf) > i:
                            confidences.append(float(r.boxes.conf[i]))

                if not all_points:
                    return ProcessingResult(
                        input_path=img_path,
                        output_path=None,
                        success=False,
                        confidence=0.0,
                        num_detections=0,
                        processing_time=time.time() - start_time,
                        error_message="No valid mask points"
                    )

                # Merge all points into convex hull
                all_concat = np.concatenate(all_points, axis=0)
                hull = cv2.convexHull(all_concat.astype(np.float32))

                avg_confidence = np.mean(confidences) if confidences else 0.5

                # Current working image and hull
                current_img = img
                current_hull = hull

                # Rotation correction
                if proc_config.get('rotation_correction', True):
                    # Convert raw points to hulls for rotation calc
                    individual_hulls = [cv2.convexHull(pts.astype(np.float32)) for pts in all_points]
                    # Pass image for edge-based detection (more accurate for small tilts)
                    rotation_angle = self._calculate_rotation(current_hull, individual_hulls, img=current_img)

                    # Lower threshold to catch small tilts (was 0.5, now 0.3)
                    if abs(rotation_angle) > 0.3:
                        self.logger.info(f"Applying rotation correction: {rotation_angle:.2f}°")
                        current_img, current_hull = self._rotate_image(
                            current_img, current_hull, rotation_angle, bg_color
                        )

                # Crop with context margin
                cropped, crop_hull, _ = self._crop_with_margins(current_img, current_hull)

                if cropped.size == 0:
                    return ProcessingResult(
                        input_path=img_path,
                        output_path=None,
                        success=False,
                        confidence=avg_confidence,
                        num_detections=len(all_points),
                        processing_time=time.time() - start_time,
                        error_message="Empty crop region"
                    )

                bordered, border_hull = self._add_texture_border(cropped, crop_hull)

                # Normalize aspect ratio (if needed)
                bordered, border_hull = self._normalize_aspect_ratio(bordered, border_hull)

                # Draw alignment line (debug feature - off by default, enable in GUI when needed)
                if proc_config.get('show_alignment_line', False):
                    bordered = self._draw_alignment(bordered, border_hull)

                # Resize for eBay
                final_img = self._resize_for_ebay(bordered)

                # Save output
                output_format = proc_config.get('output_format', 'jpg')
                output_quality = proc_config.get('output_quality', 95)
                output_path = self.crops_dir / f"{img_path.stem}_processed.{output_format}"

                if self.config.get('dry_run', False):
                    self.logger.info(f"[DRY RUN] Would save to: {output_path}")
                else:
                    if output_format.lower() in ['jpg', 'jpeg']:
                        cv2.imwrite(str(output_path), final_img,
                                   [cv2.IMWRITE_JPEG_QUALITY, output_quality])
                    else:
                        cv2.imwrite(str(output_path), final_img)

                # Check for duplicates on the FINAL processed image
                is_dup = False
                dup_match = None
                
                if self.config.get('duplicates', {}).get('enabled', True):
                    if self.config.get('dry_run', False):
                         # In dry run, we simulate duplicate check without side effects if needed, 
                         # or just skip DB updates. 
                         # For now, we perform check but skip handling actions that write to disk.
                         is_dup, dup_match = self.duplicate_detector.check_duplicate(final_img, output_path)
                    else:
                        is_dup, dup_match = self.duplicate_detector.check_duplicate(final_img, output_path)
                    
                    if is_dup:
                        action = self.config.get('duplicates', {}).get('duplicate_action', 'flag')
                        
                        if action == 'skip':
                            # Remove the saved file if we skipping
                            if output_path.exists():
                                output_path.unlink()
                            return ProcessingResult(
                                input_path=img_path,
                                output_path=None, # No output for skipped
                                success=True,
                                confidence=avg_confidence,
                                num_detections=len(all_points),
                                processing_time=time.time() - start_time,
                                is_duplicate=True,
                                duplicate_of=str(dup_match.match_path) if dup_match else None
                            )
                        elif action in ['move', 'flag']:
                            # Handle move/flag (requires file to exist)
                            if not self.config.get('dry_run', False):
                                self.duplicate_detector.handle_duplicate(output_path, dup_match)
                            else:
                                self.logger.info(f"[DRY RUN] Would {action} duplicate: {output_path.name}")

                return ProcessingResult(
                    input_path=img_path,
                    output_path=output_path,
                    success=True,
                    confidence=avg_confidence,
                    num_detections=len(all_points),
                    processing_time=time.time() - start_time,
                    is_duplicate=is_dup,
                    duplicate_of=str(dup_match.match_path) if dup_match else None
                )

        except Exception as e:
            self.logger.error(f"Error processing {img_path}: {e}")
            import traceback
            traceback.print_exc()

            return ProcessingResult(
                input_path=img_path,
                output_path=None,
                success=False,
                confidence=0.0,
                num_detections=0,
                processing_time=time.time() - start_time,
                error_message=str(e)
            )

    def process_batch(
        self,
        input_path: Path,
        parallel: bool = False,
        max_workers: int = 4,
        fast_mode: bool = False
    ) -> List[ProcessingResult]:
        """
        Process a batch of images.

        Args:
            input_path: Path to image or directory
            parallel: Whether to use parallel processing
            max_workers: Number of parallel workers

        Returns:
            List of ProcessingResult objects
        """
        input_path = Path(input_path)

        # HEIC Batch Preprocessing
        # Convert all HEIC files to JPG before processing to avoid duplicates
        if self.config.get('input', {}).get('auto_convert_heic', True):
            directory = input_path if input_path.is_dir() else input_path.parent
            delete_heic = self.config.get('input', {}).get('delete_heic_after_convert', False)
            quality = self.config.get('input', {}).get('heic_conversion_quality', 95)

            self.logger.info("Checking for HEIC files to convert...")
            converted, failed = batch_convert_heic_to_jpg(
                directory=directory,
                delete_heic=delete_heic,
                quality=quality,
                logger=self.logger
            )

            if converted:
                self.logger.info(f"Converted {len(converted)} HEIC files to JPG")
                if delete_heic:
                    self.logger.info(f"Deleted {len(converted)} original HEIC files")
            if failed:
                self.logger.warning(f"Failed to convert {len(failed)} HEIC files")

        # Gather images
        # After HEIC conversion, exclude .heic/.heif from file gathering to prevent double-processing
        if input_path.is_file():
            image_files = [input_path]
        else:
            formats = self.config.get('input', {}).get('supported_formats', ['.jpg', '.png'])
            # Exclude HEIC/HEIF from processing since they were converted to JPG in the preprocessing step
            formats = [fmt for fmt in formats if fmt.lower() not in ['.heic', '.heif']]
            image_files = get_image_files(input_path, recursive=False, formats=formats)

        self.logger.info(f"Found {len(image_files)} images to process")

        # Set dynamic output path based on input
        self.set_output_from_input(input_path)

        results = []

        if parallel and len(image_files) > 1:
            # Note: Duplicate detection cache might be less effective in parallel 
            # unless we use a shared manager, but we rely on DB for that.
            # Local batch cache is per-instance, so thread-safe but separate.
            # For strict within-batch parallel detection, we'd need a lock.
            # Reset batch cache
            self.duplicate_detector.start_batch()

            # Parallel processing
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.process_single_image, img, fast_mode): img
                    for img in image_files
                }

                with tqdm(total=len(image_files), desc="Processing") as pbar:
                    for future in as_completed(futures):
                        result = future.result()
                        results.append(result)
                        pbar.update(1)

                        if result.success:
                            self.stats['successful'] += 1
                        else:
                            self.stats['failed'] += 1

                        if result.is_duplicate:
                            self.stats['duplicates'] += 1
                        self.stats['processed'] += 1
        else:
            # Reset batch cache
            self.duplicate_detector.start_batch()

            # Sequential processing
            for img_path in tqdm(image_files, desc="Processing"):
                result = self.process_single_image(img_path, fast_mode)
                results.append(result)

                if result.success:
                    self.stats['successful'] += 1
                else:
                    self.stats['failed'] += 1

                if result.is_duplicate:
                    self.stats['duplicates'] += 1
                self.stats['processed'] += 1

        # End batch (clears cache)
        self.duplicate_detector.end_batch()

        return results

    def get_stats_summary(self) -> str:
        """Get processing statistics summary."""
        return (
            f"Processed: {self.stats['processed']}, "
            f"Successful: {self.stats['successful']}, "
            f"Failed: {self.stats['failed']}, "
            f"Duplicates: {self.stats['duplicates']}"
        )


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Stamp Philatex Processor - Process stamp images"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Input image file or directory"
    )
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Enable parallel processing"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate processing without saving files"
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast mode: skip generating debug visuals for higher speed"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to config file"
    )

    args = parser.parse_args()

    # Create processor
    if args.config:
        config = load_config(args.config)
    else:
        config = load_config()

    # Apply dry run arg
    if hasattr(args, 'dry_run') and args.dry_run:
        config['dry_run'] = True

    processor = StampProcessor(config)

    # Process
    start_time = time.time()
    results = processor.process_batch(
        Path(args.input),
        parallel=args.parallel,
        max_workers=args.workers,
        fast_mode=args.fast
    )

    # Summary
    total_time = time.time() - start_time
    print(f"\n{'='*50}")
    print(f"Processing Complete!")
    print(f"{'='*50}")
    print(processor.get_stats_summary())
    print(f"Total time: {format_duration(total_time)}")
    print(f"Output: {processor.crops_dir}")

    # List any errors
    errors = [r for r in results if not r.success]
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for err in errors[:10]:  # Show first 10
            print(f"  - {err.input_path.name}: {err.error_message}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")


if __name__ == "__main__":
    main()
