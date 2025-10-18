from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np
from pydantic import BaseModel, Field, PositiveInt, ConfigDict


class SegmentationSettings(BaseModel):
    """
    Configuration for person segmentation.

    Attributes:
        downscale_factor (int): Factor to downscale frames for modeling/segmentation speed.
        min_blob_area (int): Minimum area in pixels (at full resolution) to accept a person blob.
        morph_kernel (int): Kernel size for morphological cleanup operations.
        threshold (int): Threshold used by some segmenters (0-255, adaptive to downscale).
        pca_components (int): Number of PCA components for PCA background model.
        background_frames (int): Number of background frames to learn before gameplay.
    """

    downscale_factor: PositiveInt = Field(default=2, ge=1, le=8)
    min_blob_area: PositiveInt = Field(default=500)
    morph_kernel: PositiveInt = Field(default=5)
    threshold: int = Field(default=30, ge=0, le=255)
    pca_components: PositiveInt = Field(default=5)
    background_frames: PositiveInt = Field(default=30)


class PersonFeatures(BaseModel):
    """
    Extracted features about the detected person.

    Attributes:
        has_person (bool): Whether a person was detected.
        centroid (Tuple[float, float] | None): Centroid in camera pixel coordinates (x, y).
        bbox (Tuple[int, int, int, int] | None): Bounding box (x, y, w, h) in camera pixels.
        mask (np.ndarray | None): Binary mask (uint8 {0,255}) at full resolution.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    has_person: bool
    centroid: Optional[Tuple[float, float]] = None
    bbox: Optional[Tuple[int, int, int, int]] = None
    mask: Optional[np.ndarray] = None


class BasePersonSegmenter:
    """
    Abstract base class for person segmenters.

    Subclasses must implement `segment(frame_bgr)` and return `PersonFeatures`.
    """

    def __init__(self, settings: Optional[SegmentationSettings] = None) -> None:
        self.settings = settings or SegmentationSettings()

    def segment(self, frame_bgr: np.ndarray) -> PersonFeatures:  # pragma: no cover - abstract
        raise NotImplementedError

    # ------------------------ Utility helpers ------------------------
    def _postprocess_mask(self, mask_small: np.ndarray, full_size: Tuple[int, int]) -> np.ndarray:
        """
        Upscale and clean a binary mask to full resolution.

        Args:
            mask_small: uint8 mask at downscaled resolution (0/255).
            full_size: (width, height) of the original frame.

        Returns:
            uint8 full-size mask.
        """
        height, width = full_size[1], full_size[0]
        mask = cv2.resize(mask_small, (width, height), interpolation=cv2.INTER_NEAREST)

        k = int(self.settings.morph_kernel)
        if k % 2 == 0:
            k += 1
        kernel = np.ones((k, k), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        return mask

    def _extract_largest_blob(self, mask: np.ndarray) -> PersonFeatures:
        """
        Extract the largest connected component as the person candidate.

        Args:
            mask: uint8 full-size binary mask {0,255}.

        Returns:
            PersonFeatures with centroid, bbox, and filtered mask.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return PersonFeatures(has_person=False, mask=np.zeros_like(mask))

        largest = max(contours, key=cv2.contourArea)
        area = float(cv2.contourArea(largest))
        if area < float(self.settings.min_blob_area):
            return PersonFeatures(has_person=False, mask=np.zeros_like(mask))

        x, y, w, h = cv2.boundingRect(largest)
        M = cv2.moments(largest)
        if M["m00"] == 0:
            return PersonFeatures(has_person=False, mask=np.zeros_like(mask))
        cx = M["m10"] / M["m00"]
        cy = M["m01"] / M["m00"]

        person_mask = np.zeros_like(mask)
        cv2.drawContours(person_mask, [largest], -1, 255, thickness=cv2.FILLED)
        return PersonFeatures(
            has_person=True,
            centroid=(float(cx), float(cy)),
            bbox=(int(x), int(y), int(w), int(h)),
            mask=person_mask,
        )


class ThresholdPersonSegmenter(BasePersonSegmenter):
    """
    Simple foreground segmentation by absolute difference from a background frame.

    Provide an initial background frame via `set_background(frame_bgr)`.
    """

    def __init__(self, settings: Optional[SegmentationSettings] = None) -> None:
        super().__init__(settings)
        self._bg_gray: Optional[np.ndarray] = None

    def set_background(self, frame_bgr: np.ndarray) -> None:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        self._bg_gray = gray

    def segment(self, frame_bgr: np.ndarray) -> PersonFeatures:
        if self._bg_gray is None:
            # No background yet: assume no person
            h, w = frame_bgr.shape[:2]
            return PersonFeatures(has_person=False, mask=np.zeros((h, w), dtype=np.uint8))

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        factor = int(self.settings.downscale_factor)
        small = cv2.resize(gray, (gray.shape[1] // factor, gray.shape[0] // factor))
        bg_small = cv2.resize(self._bg_gray, (small.shape[1], small.shape[0]))

        diff = cv2.absdiff(small, bg_small)
        _, mask_small = cv2.threshold(diff, int(self.settings.threshold), 255, cv2.THRESH_BINARY)

        full_mask = self._postprocess_mask(mask_small, (gray.shape[1], gray.shape[0]))
        return self._extract_largest_blob(full_mask)


class BgSubtractorPersonSegmenter(BasePersonSegmenter):
    """
    Foreground segmentation using OpenCV MOG2 background subtractor.
    """

    def __init__(self, settings: Optional[SegmentationSettings] = None) -> None:
        super().__init__(settings)
        self._mog2 = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=25, detectShadows=False)

    def segment(self, frame_bgr: np.ndarray) -> PersonFeatures:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        factor = int(self.settings.downscale_factor)
        small = cv2.resize(gray, (gray.shape[1] // factor, gray.shape[0] // factor))

        fg_small = self._mog2.apply(small)
        # Remove background learning noise in initial frames
        _, fg_small = cv2.threshold(fg_small, 127, 255, cv2.THRESH_BINARY)

        full_mask = self._postprocess_mask(fg_small, (gray.shape[1], gray.shape[0]))
        return self._extract_largest_blob(full_mask)


class PcaBackgroundPersonSegmenter(BasePersonSegmenter):
    """
    PCA-based background modeling. Learns a low-rank background subspace from initial frames.

    Segmentation is done via reconstruction error thresholding.
    """

    def __init__(self, settings: Optional[SegmentationSettings] = None) -> None:
        super().__init__(settings)
        self._mean_small: Optional[np.ndarray] = None  # shape (h*w,)
        self._basis: Optional[np.ndarray] = None  # shape (k, h*w)
        self._small_shape: Optional[Tuple[int, int]] = None  # (h, w)
        self._is_trained: bool = False
        self._buffer: list[np.ndarray] = []

    def observe_background(self, frame_bgr: np.ndarray) -> None:
        """
        Feed a background frame (without person) for model training.
        After `background_frames` observations, the model becomes ready.
        """
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        factor = int(self.settings.downscale_factor)
        small = cv2.resize(gray, (gray.shape[1] // factor, gray.shape[0] // factor))
        self._small_shape = (small.shape[0], small.shape[1])
        self._buffer.append(small.astype(np.float32).reshape(-1))
        if len(self._buffer) >= int(self.settings.background_frames):
            self._train_pca()

    def ready(self) -> bool:
        return self._is_trained

    def _train_pca(self) -> None:
        X = np.stack(self._buffer, axis=0)  # (n, d)
        mean_vec = X.mean(axis=0)
        Xc = X - mean_vec[None, :]
        # Compute top-k right singular vectors for subspace basis
        # Reason: Avoid covariance matrix explosion for large d.
        U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
        k = int(min(self.settings.pca_components, Vt.shape[0]))
        basis = Vt[:k, :]  # (k, d)
        self._mean_small = mean_vec.astype(np.float32)
        self._basis = basis.astype(np.float32)
        self._is_trained = True
        self._buffer.clear()

    def segment(self, frame_bgr: np.ndarray) -> PersonFeatures:
        if not self._is_trained or self._mean_small is None or self._basis is None or self._small_shape is None:
            # Not ready yet
            h, w = frame_bgr.shape[:2]
            return PersonFeatures(has_person=False, mask=np.zeros((h, w), dtype=np.uint8))

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        factor = int(self.settings.downscale_factor)
        small = cv2.resize(gray, (gray.shape[1] // factor, gray.shape[0] // factor))
        vec = small.astype(np.float32).reshape(-1)

        x_c = vec - self._mean_small
        # Project and reconstruct
        coeffs = self._basis @ x_c  # (k,)
        recon = self._basis.T @ coeffs  # (d,)
        resid = np.abs(x_c - recon)
        # Map residuals back to image and threshold
        resid_img = resid.reshape(self._small_shape)
        resid_img = cv2.normalize(resid_img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        _, mask_small = cv2.threshold(resid_img, int(self.settings.threshold), 255, cv2.THRESH_BINARY)

        full_mask = self._postprocess_mask(mask_small, (gray.shape[1], gray.shape[0]))
        return self._extract_largest_blob(full_mask)
