import multiprocessing
import os
import time
import psutil
from filters import process_image_pipeline

def worker_wrapper_mp(args):
    data, index = args
    result = process_image_pipeline(data)
    
    # --- WINDOWS CORE ID CALCULATION ---
    try:
        if hasattr(psutil.Process(), 'cpu_num'):
            core = psutil.Process().cpu_num()
        else:
            raise AttributeError
    except:
        core = os.getpid() % multiprocessing.cpu_count()
    # -----------------------------------

    info = {
        'index': index,
        'pid': os.getpid(),
        'core': core,
        'success': result is not None
    }
    return info

def run_multiprocessing_task(images, output_dir, num_processes, callback_func):
    mp_dir = os.path.join(output_dir, f"multiprocessing_p{num_processes}")
    if not os.path.exists(mp_dir):
        os.makedirs(mp_dir)
        
    tasks = [((img, mp_dir), i+1) for i, img in enumerate(images)]
    
    start_time = time.time()
    unique_pids = set()
    
    with multiprocessing.Pool(processes=num_processes) as pool:
        for result in pool.imap(worker_wrapper_mp, tasks):
            unique_pids.add(result['pid'])
            callback_func(result)
                
    duration = time.time() - start_time
    return duration, len(unique_pids)
