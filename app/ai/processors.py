import cv2
import numpy as np
import os

def apply_pixelate(roi: np.ndarray, strength: int) -> np.ndarray:
    """
    Pixelate a region of interest using down and up resizing with INTER_NEAREST.
    """
    h, w = roi.shape[:2]
    pw = max(1, w // strength)
    ph = max(1, h // strength)
    temp = cv2.resize(roi, (pw, ph), interpolation=cv2.INTER_LINEAR)
    return cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)

def apply_box_blur(roi: np.ndarray, strength: int) -> np.ndarray:
    """
    Apply Box Blur to a region of interest.
    """
    ksize = strength
    if ksize % 2 == 0:
        ksize += 1
    ksize = max(1, ksize)
    return cv2.blur(roi, (ksize, ksize))

def apply_gaussian_blur(roi: np.ndarray, strength: int) -> np.ndarray:
    """
    Apply Gaussian Blur to a region of interest.
    """
    ksize = strength
    if ksize % 2 == 0:
        ksize += 1
    ksize = max(1, ksize)
    return cv2.GaussianBlur(roi, (ksize, ksize), 0)

def apply_solid_color(roi: np.ndarray, color=(0, 0, 0)) -> np.ndarray:
    """
    Fill the region of interest with a solid color (default: black).
    """
    res = np.zeros_like(roi)
    res[:] = color
    return res

def apply_replace_image(roi: np.ndarray, image_path: str) -> np.ndarray:
    """
    Overlay an image onto the region of interest, handling transparency if available.
    """
    if not image_path or not os.path.exists(image_path):
        return roi
        
    replacement_img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if replacement_img is None:
        return roi
        
    h, w = roi.shape[:2]
    resized_replacement = cv2.resize(replacement_img, (w, h))
    
    if resized_replacement.shape[2] == 4:
        alpha_channel = resized_replacement[:, :, 3] / 255.0
        alpha_mask = np.atleast_3d(alpha_channel)
        rgb_replacement = resized_replacement[:, :, :3]
        blended = (rgb_replacement * alpha_mask + roi * (1.0 - alpha_mask)).astype(np.uint8)
        return blended
    else:
        return resized_replacement

def blur_background(frame: np.ndarray, category_mask: np.ndarray, bg_blur_strength: int) -> np.ndarray:
    """
    Blur the background of the frame based on the segmentation category mask.
    """
    height, width = frame.shape[:2]
    
    # Resize mask to frame dimensions if necessary
    if category_mask.shape[:2] != (height, width):
        category_mask = cv2.resize(
            category_mask.astype(np.float32), 
            (width, height), 
            interpolation=cv2.INTER_LINEAR
        )
        
    raw_mask = (category_mask == 0).astype(np.float32)
    smooth_mask = cv2.GaussianBlur(raw_mask, (21, 21), 0)
    fg_mask_3d = np.atleast_3d(smooth_mask)
    
    ksize = int(bg_blur_strength)
    if ksize % 2 == 0:
        ksize += 1
    ksize = max(1, ksize)
    blurred_frame = cv2.GaussianBlur(frame, (ksize, ksize), 0)
    
    processed_frame = (frame * fg_mask_3d + blurred_frame * (1.0 - fg_mask_3d)).astype(np.uint8)
    return processed_frame
