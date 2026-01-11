import time
import os
from filters import process_image_pipeline
from tqdm import tqdm

def run_sequential_task(images, output_dir):
    seq_dir = os.path.join(output_dir, "sequential")
    if not os.path.exists(seq_dir):
        os.makedirs(seq_dir)

    start_time = time.time()
    
    # Matches the simple progress bar from user example
    pbar = tqdm(total=len(images), 
                bar_format="  Progress: {n_fmt}/{total_fmt} images ({elapsed}s elapsed)", 
                ncols=70)
    
    for img_path in images:
        process_image_pipeline((img_path, seq_dir))
        pbar.update(1)
        
    pbar.close()
    duration = time.time() - start_time
    return duration