import os
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from app.ai.detectors import (
    get_face_detector,
    get_selfie_segmenter,
    prepare_ai_input_frame,
)
from app.core.constants import FACE_MODEL_PATH, SELFIE_MODEL_PATH, AI_IMAGE_SIZE

def test_get_face_detector_not_exist(mocker):
    """
    Test get_face_detector when the model file does not exist.
    """
    mocker.patch("os.path.exists", return_value=False)
    assert get_face_detector() is None

def test_get_face_detector_exists_cpu_delegate(mocker):
    """
    Test get_face_detector when the model file exists, verifying it uses CPU delegate.
    """
    mocker.patch("os.path.exists", return_value=True)
    
    # Mock python BaseOptions and vision.FaceDetector.create_from_options
    mock_base_options_cls = mocker.patch("mediapipe.tasks.python.BaseOptions")
    mock_face_detector_options_cls = mocker.patch("mediapipe.tasks.python.vision.FaceDetectorOptions")
    mock_create_from_options = mocker.patch("mediapipe.tasks.python.vision.FaceDetector.create_from_options")
    
    detector = get_face_detector()
    
    # Assert that BaseOptions was initialized with the correct model path and CPU delegate
    mock_base_options_cls.assert_called_once()
    kwargs = mock_base_options_cls.call_args[1]
    assert kwargs["model_asset_path"] == FACE_MODEL_PATH
    
    # Check that delegate is CPU
    from mediapipe.tasks.python import BaseOptions
    assert kwargs["delegate"] == BaseOptions.Delegate.CPU
    
    mock_face_detector_options_cls.assert_called_once()
    mock_create_from_options.assert_called_once()

def test_get_selfie_segmenter_not_exist(mocker):
    """
    Test get_selfie_segmenter when the model file does not exist.
    """
    mocker.patch("os.path.exists", return_value=False)
    assert get_selfie_segmenter() is None

def test_get_selfie_segmenter_exists_cpu_delegate(mocker):
    """
    Test get_selfie_segmenter when the model file exists, verifying CPU delegate.
    """
    mocker.patch("os.path.exists", return_value=True)
    
    # Mock base options, options, and create_from_options
    mock_base_options_cls = mocker.patch("mediapipe.tasks.python.BaseOptions")
    mock_segmenter_options_cls = mocker.patch("mediapipe.tasks.python.vision.ImageSegmenterOptions")
    mock_create_from_options = mocker.patch("mediapipe.tasks.python.vision.ImageSegmenter.create_from_options")
    
    segmenter = get_selfie_segmenter()
    
    # Assert BaseOptions configuration
    mock_base_options_cls.assert_called_once()
    kwargs = mock_base_options_cls.call_args[1]
    assert kwargs["model_asset_path"] == SELFIE_MODEL_PATH
    
    from mediapipe.tasks.python import BaseOptions
    assert kwargs["delegate"] == BaseOptions.Delegate.CPU
    
    mock_segmenter_options_cls.assert_called_once()
    mock_create_from_options.assert_called_once()

def test_prepare_ai_input_frame():
    """
    Test resize BGR frame to 320x320, convert to RGB, and return mp.Image with proper scale factors.
    """
    # Create a dummy high-resolution frame (1080x1920x3)
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    # Fill with a specific value so we can verify RGB conversion mock or actual call
    frame[:, :, 0] = 255  # Pure Blue in BGR
    
    mp_image, sx, sy = prepare_ai_input_frame(frame)
    
    # Scale factors: 1920 / 320 = 6.0, 1080 / 320 = 3.375
    assert sx == 1920 / float(AI_IMAGE_SIZE)
    assert sy == 1080 / float(AI_IMAGE_SIZE)
    
    # Verify the output image dimensions are AI_IMAGE_SIZE (320)
    assert mp_image.width == AI_IMAGE_SIZE
    assert mp_image.height == AI_IMAGE_SIZE
    
    # Verify that the color channels got swapped from BGR (255, 0, 0) to RGB (0, 0, 255)
    pixel = mp_image.numpy_view()[0, 0]
    assert pixel[0] == 0    # Red
    assert pixel[1] == 0    # Green
    assert pixel[2] == 255  # Blue
