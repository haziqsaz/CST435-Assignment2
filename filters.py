import os
import numpy as np
from PIL import Image

def apply_kernel(image, kernel):
    """Helper function to apply a convolution matrix."""
    kernel = np.array(kernel)
    pad = kernel.shape[0] // 2
    # Pad image to handle borders
    padded = np.pad(image, ((pad, pad), (pad, pad)), mode='edge')
    output = np.zeros_like(image)
    
    h, w = image.shape
    kh, kw = kernel.shape
    
    # Simplified convolution loop
    for i in range(h):
        for j in range(w):
            region = padded[i:i+kh, j:j+kw]
            output[i, j] = np.sum(region * kernel)
    return output

def process_image_pipeline(file_info):
    """
    The main worker function.
    Args:
        file_info: A tuple containing (input_path, output_dir)
    Returns:
        filename if successful, None otherwise
    """
    input_path, output_dir = file_info
    
    try:
        filename = os.path.basename(input_path)
        img = Image.open(input_path).convert('RGB')
        img_array = np.array(img)

        # ----------------------------------------
        # 1. Grayscale Conversion (Luminance)
        # ----------------------------------------
        gray = np.dot(img_array[...,:3], [0.299, 0.587, 0.114])

        # ----------------------------------------
        # 2. Gaussian Blur (3x3 Kernel)
        # ----------------------------------------
        blur_kernel = [
            [1/16, 2/16, 1/16],
            [2/16, 4/16, 2/16],
            [1/16, 2/16, 1/16]
        ]
        blurred = apply_kernel(gray, blur_kernel)

        # ----------------------------------------
        # 3. Edge Detection (Sobel)
        # ----------------------------------------
        # Vertical edges
        Gx = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
        # Horizontal edges
        Gy = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
        
        sobel_x = apply_kernel(blurred, Gx)
        sobel_y = apply_kernel(blurred, Gy)
        edges = np.sqrt(sobel_x**2 + sobel_y**2)
        # Normalize
        edges = (edges / np.max(edges)) * 255

        # ----------------------------------------
        # 4. Image Sharpening
        # ----------------------------------------
        sharpen_kernel = [
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ]
        sharpened = apply_kernel(edges, sharpen_kernel)

        # ----------------------------------------
        # 5. Brightness Adjustment
        # ----------------------------------------
        bright = np.clip(sharpened * 1.2, 0, 255)

        # Save Result
        result = Image.fromarray(bright.astype(np.uint8))
        if result.mode != 'L':
            result = result.convert('L')
            
        output_path = os.path.join(output_dir, filename)
        result.save(output_path)
        
        return filename

    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return None