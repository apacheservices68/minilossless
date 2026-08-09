import os
import cv2
import numpy as np
import pytest
from app.ai.processors import (
    apply_pixelate,
    apply_box_blur,
    apply_gaussian_blur,
    apply_solid_color,
    apply_replace_image,
    blur_background,
)

@pytest.fixture
def dummy_frame():
    """
    Returns a dummy BGR frame representing a 1080p video frame with high contrast.
    """
    return np.random.randint(0, 256, (1080, 1920, 3), dtype=np.uint8)

def test_apply_pixelate(dummy_frame):
    """
    Test pixelate algorithm.
    """
    roi = dummy_frame[100:400, 100:400]
    strength = 10
    
    pixelated = apply_pixelate(roi, strength)
    
    assert pixelated.shape == roi.shape
    # Pixelation should preserve shape but reduce high frequency details (quantized blocks)
    # E.g. we can check that pixelated is still a numpy array with same dtype
    assert pixelated.dtype == np.uint8

def test_apply_box_blur(dummy_frame):
    """
    Test Box Blur filter.
    """
    roi = dummy_frame[100:400, 100:400]
    strength = 15
    
    blurred = apply_box_blur(roi, strength)
    
    assert blurred.shape == roi.shape
    assert blurred.dtype == np.uint8
    # The edges of the rectangle in the blurred image should be smoothed compared to the sharp ROI
    assert not np.array_equal(blurred, roi)

def test_apply_gaussian_blur(dummy_frame):
    """
    Test Gaussian Blur filter.
    """
    roi = dummy_frame[100:400, 100:400]
    strength = 15
    
    blurred = apply_gaussian_blur(roi, strength)
    
    assert blurred.shape == roi.shape
    assert blurred.dtype == np.uint8
    assert not np.array_equal(blurred, roi)

def test_apply_solid_color(dummy_frame):
    """
    Test solid color fill.
    """
    roi = dummy_frame[100:400, 100:400]
    color = (123, 45, 67)
    
    solid = apply_solid_color(roi, color=color)
    
    assert solid.shape == roi.shape
    assert np.all(solid[:, :, 0] == 123)
    assert np.all(solid[:, :, 1] == 45)
    assert np.all(solid[:, :, 2] == 67)

def test_apply_replace_image_no_image(dummy_frame):
    """
    Test apply_replace_image when path is empty or does not exist (returns original ROI).
    """
    roi = dummy_frame[100:400, 100:400]
    res = apply_replace_image(roi, "")
    assert np.array_equal(res, roi)
    
    res_not_exists = apply_replace_image(roi, "non_existent_image_path.png")
    assert np.array_equal(res_not_exists, roi)

def test_apply_replace_image_exists_rgba(mocker, dummy_frame):
    """
    Test apply_replace_image with mocked RGBA image (with transparency overlay).
    """
    roi = dummy_frame[100:400, 100:400]
    image_path = "dummy_image.png"
    
    # Mock os.path.exists to True for the image_path
    mocker.patch("os.path.exists", return_value=True)
    
    # Create mock replacement image (RGBA)
    # Height, width of roi is 300x300
    mock_rgba_image = np.ones((300, 300, 4), dtype=np.uint8) * 100
    mock_rgba_image[:, :, 3] = 127 # ~50% transparency alpha channel
    
    mocker.patch("cv2.imread", return_value=mock_rgba_image)
    
    res = apply_replace_image(roi, image_path)
    
    assert res.shape == roi.shape
    assert res.dtype == np.uint8
    # Since alpha is 127/255.0 (~0.5), the result should be blended between roi and mock image
    assert not np.array_equal(res, roi)
    assert not np.array_equal(res, mock_rgba_image[:, :, :3])

def test_blur_background(dummy_frame):
    """
    Test blur_background based on mock segmentation category mask.
    """
    # Category mask is typically 1 for background, 0 for person (or vice versa in MediaPipe)
    # From app/ai/processors.py: raw_mask = (category_mask == 0).astype(np.float32)
    # Category mask with same size as frame or different size (test resizing)
    category_mask = np.zeros((256, 256), dtype=np.uint8)
    # Center is person (0), rest is background (1)
    category_mask[64:192, 64:192] = 0
    category_mask[0:64, :] = 1
    
    bg_blur_strength = 25
    
    processed = blur_background(dummy_frame, category_mask, bg_blur_strength)
    
    assert processed.shape == dummy_frame.shape
    assert processed.dtype == np.uint8
    # Background areas should be blurred, person area (where mask is 0) should remain sharp
    assert not np.array_equal(processed, dummy_frame)
