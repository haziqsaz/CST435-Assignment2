import concurrent.futures
import os
import time
import psutil
import threading
import multiprocessing
from filters import process_image_pipeline

def worker_wrapper_fut(args):
    data, index = args
    result = process_image_pipeline(data)
    
    # --- WINDOWS CORE ID CALCULATION ---
    try:
        if hasattr(psutil.Process(), 'cpu_num'):
            core = psutil.Process().cpu_num()
        else:
            core = threading.get_ident() % multiprocessing.cpu_count()
    except:
        core = 0
    # -----------------------------------

    info = {
        'index': index,
        'pid': os.getpid(),
        'tid': threading.get_ident(),
        'core': core, 
        'success': result is not None
    }
    return info

def run_futures_task(images, output_dir, num_workers, callback_func, mode='process'):
    """
    mode: 'process' = ProcessPoolExecutor (CPU Bound)
    mode: 'thread'  = ThreadPoolExecutor (I/O Bound)
    """
    sub_folder = f"futures_{mode}_w{num_workers}"
    fut_dir = os.path.join(output_dir, sub_folder)
    if not os.path.exists(fut_dir):
        os.makedirs(fut_dir)

    tasks = [((img, fut_dir), i+1) for i, img in enumerate(images)]
    start_time = time.time()
    
    # Select Executor Type
    ExecutorClass = (concurrent.futures.ProcessPoolExecutor 
                     if mode == 'process' 
                     else concurrent.futures.ThreadPoolExecutor)
    
    with ExecutorClass(max_workers=num_workers) as executor:
        futures = [executor.submit(worker_wrapper_fut, t) for t in tasks]
        
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            callback_func(res)
                
    duration = time.time() - start_time
    return duration
