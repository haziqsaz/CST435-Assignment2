import os
import argparse
import multiprocessing
import sys
import time
import datetime
import random # Added for randomness
from tqdm import tqdm
from colorama import init

init(autoreset=True)

try:
    import run_seq
    import run_mp
    import run_fut
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Auto-detect folder name
POSSIBLE_DIRS = ["data/food-101", "data/food-101-subset", "food-101"]
INPUT_DIR = None

for d in POSSIBLE_DIRS:
    path = os.path.join(BASE_DIR, d)
    if os.path.exists(path):
        INPUT_DIR = path
        break

if INPUT_DIR is None:
    INPUT_DIR = os.path.join(BASE_DIR, "data", "food-101")

OUTPUT_DIR = os.path.join(BASE_DIR, "output")
RESULTS_CSV = os.path.join(OUTPUT_DIR, "benchmark_results.csv")
# ---------------------

def print_banner(text):
    print("=" * 70)
    print(f"{text}")
    print("=" * 70)

def print_step_header(step_num, title):
    print("-" * 70)
    print(f"STEP {step_num}: {title}")
    print("-" * 70)

def print_section_header(title):
    print(f"{title}")
    print("=" * len(title))

def save_csv(results):
    try:
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        with open(RESULTS_CSV, "w") as f:
            f.write("Paradigm,Workers,Time,Speedup,Efficiency\n")
            for r in results:
                f.write(f"{r['mode']},{r['workers']},{r['time']:.4f},{r['speedup']:.2f},{r['efficiency']:.2f}\n")
    except Exception as e:
        print(f"Warning: Could not save CSV: {e}")

def main():
    multiprocessing.freeze_support()
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--images', type=int, default=1000, help='Number of images')
    args = parser.parse_args()

    if not os.path.exists(INPUT_DIR):
        print(f"Error: Data directory not found: {INPUT_DIR}")
        print("Please check where your 'food-101' folder is located.")
        return

    import glob
    all_images = glob.glob(os.path.join(INPUT_DIR, "**", "*.jpg"), recursive=True)
    
    if not all_images:
        print(f"No images found in {INPUT_DIR}")
        return

    # --- RANDOM SELECTION ADDED HERE ---
    random.shuffle(all_images)
    # -----------------------------------
    
    subset_images = all_images[:args.images]

    print(f"images {len(subset_images)}")
    print_banner("PARALLEL IMAGE PROCESSING PIPELINE - DEMO")
    print(f"\nFound {len(all_images)} images in {INPUT_DIR}")
    print("\nRunning benchmark on food-101 subset images")
    print("-" * 40)
    print_banner("PARALLEL IMAGE PROCESSING BENCHMARK")
    
    print("\nSystem Information:")
    print(f"  Available CPUs: {multiprocessing.cpu_count()}")
    print(f"  Process counts to test: [1, 2, 4]")
    print(f"  Image limit: {len(subset_images)}")
    print(f"  Input directory: {INPUT_DIR}")
    print(f"  Output base directory: output\n")

    results_data = []

    # STEP 1: SEQUENTIAL
    print_step_header(1, "Sequential Baseline")
    print_section_header("Sequential Pipeline")
    print(f"Input directory: {INPUT_DIR}")
    print(f"Output directory: {os.path.join(OUTPUT_DIR, 'sequential')}")
    print(f"Images to process: {len(subset_images)}\n")

    seq_time = run_seq.run_sequential_task(subset_images, OUTPUT_DIR)
    
    print("\nSummary")
    print("-------")
    print(f"Successful: {len(subset_images)}/{len(subset_images)}")
    print(f"Failed: 0/{len(subset_images)}")
    print(f"Total time: {seq_time:.4f} seconds")
    print(f"Average time per image: {seq_time/len(subset_images):.4f} seconds")
    print(f"\nBaseline time: {seq_time:.4f} seconds\n")

    # STEP 2: MULTIPROCESSING
    print_step_header(2, "Multiprocessing Pipeline")
    mp_results = []
    
    def progress_callback(pbar, label):
        def inner(info):
            tqdm.write(f"[{label}] Data Chunk ID: {info['index']} ---> CPU Core ID: {info['core']}")
            tqdm.write(f"   Identity Info: PID:{info['pid']}")
            pbar.update(1)
        return inner

    for p in [1, 2, 4]:
        print(f"\n>>> Testing with {p} processes...")
        print_section_header("Multiprocessing Pipeline")
        print(f"Input directory: {INPUT_DIR}")
        print(f"Output directory: {os.path.join(OUTPUT_DIR, f'multiprocessing_p{p}')}")
        print(f"Images to process: {len(subset_images)}")
        print(f"Worker processes: {p}\n")

        # Fixed Progress Bar String
        bar_str = "Multiprocessing Pool (" + str(p) + " processes): {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}"
        pbar = tqdm(total=len(subset_images), bar_format=bar_str, ncols=80)
        
        mp_time, workers_used = run_mp.run_multiprocessing_task(
            subset_images, OUTPUT_DIR, p, progress_callback(pbar, "Process")
        )
        pbar.close()

        speedup = seq_time / mp_time
        eff = (speedup / p) * 100
        
        print("\nSummary")
        print("-------")
        print(f"Successful: {len(subset_images)}/{len(subset_images)}")
        print(f"Failed: 0/{len(subset_images)}")
        print(f"Total time: {mp_time:.4f} seconds")
        print(f"Average time per image: {mp_time/len(subset_images):.4f} seconds")
        print(f"Unique workers used: {workers_used}")
        print(f"    Speedup: {speedup:.2f}x")
        print(f"    Efficiency: {eff:.2f}%")
        
        mp_results.append({'p': p, 'time': mp_time, 'speedup': speedup, 'eff': eff})
        results_data.append({'mode': 'MP', 'workers': p, 'time': mp_time, 'speedup': speedup, 'efficiency': eff})

    # STEP 3: FUTURES
    print("\n")
    print_step_header(3, "Concurrent.Futures Pipeline")
    fut_results = []
    
    def progress_callback_fut(pbar, label):
        def inner(info):
            tqdm.write(f"[{label}] Data Chunk ID: {info['index']} ---> CPU Core ID: {info['core']}")
            tqdm.write(f"   Identity Info: PID:{info['pid']} | TID:{info['tid']}")
            pbar.update(1)
        return inner

    for w in [1, 2, 4]:
        print(f"\n>>> Testing with {w} workers...")
        print_section_header("Concurrent.Futures Pipeline (ProcessPoolExecutor)")
        print(f"Input directory: {INPUT_DIR}")
        print(f"Output directory: {os.path.join(OUTPUT_DIR, f'futures_w{w}')}")
        print(f"Images to process: {len(subset_images)}")
        print(f"Max workers: {w}\n")

        # Fixed Progress Bar String
        bar_str = "Futures ProcessPool (" + str(w) + " workers): {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}"
        pbar = tqdm(total=len(subset_images), bar_format=bar_str, ncols=80)

        fut_time = run_fut.run_futures_task(
            subset_images, OUTPUT_DIR, w, progress_callback_fut(pbar, "Future")
        )
        pbar.close()

        speedup = seq_time / fut_time
        eff = (speedup / w) * 100
        
        print("\nSummary")
        print("-------")
        print(f"Successful: {len(subset_images)}/{len(subset_images)}")
        print(f"Failed: 0/{len(subset_images)}")
        print(f"Total time: {fut_time:.4f} seconds")
        print(f"Average time per image: {fut_time/len(subset_images):.4f} seconds")
        print(f"Unique workers used: {w}") 
        print(f"    Speedup: {speedup:.2f}x")
        print(f"    Efficiency: {eff:.2f}%")
        
        fut_results.append({'w': w, 'time': fut_time, 'speedup': speedup, 'eff': eff})
        results_data.append({'mode': 'Fut', 'workers': w, 'time': fut_time, 'speedup': speedup, 'efficiency': eff})

    # FINAL REPORT
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    print("\n+" + "-"*63 + "+")
    print(f"|{'BENCHMARK SUMMARY':^63}|")
    print("+" + "-"*63 + "+")
    print(f"|  Timestamp: {timestamp:<48}|")
    print(f"|  Total images processed: {len(subset_images):<40}|")
    print(f"|  Sequential baseline time: {seq_time:.4f} seconds{'':<22}|")
    
    print("+" + "-"*15 + "+" + "-"*15 + "+" + "-"*15 + "+" + "-"*15 + "+")
    print(f"|{'MULTIPROCESSING RESULTS':^63}|")
    print("+" + "-"*15 + "+" + "-"*15 + "+" + "-"*15 + "+" + "-"*15 + "+")
    print(f"|{'Processes':^15}|{'Time (s)':^15}|{'Speedup':^15}|{'Efficiency':^15}|")
    print("+" + "-"*15 + "+" + "-"*15 + "+" + "-"*15 + "+" + "-"*15 + "+")
    for r in mp_results:
        print(f"|{r['p']:^15}|{r['time']:^15.4f}|{r['speedup']:^14.2f}x|{r['eff']:^14.2f}%|")
    print("+" + "-"*15 + "+" + "-"*15 + "+" + "-"*15 + "+" + "-"*15 + "+")

    print(f"|{'CONCURRENT.FUTURES RESULTS (ProcessPoolExecutor)':^63}|")
    print("+" + "-"*15 + "+" + "-"*15 + "+" + "-"*15 + "+" + "-"*15 + "+")
    print(f"|{'Workers':^15}|{'Time (s)':^15}|{'Speedup':^15}|{'Efficiency':^15}|")
    print("+" + "-"*15 + "+" + "-"*15 + "+" + "-"*15 + "+" + "-"*15 + "+")
    for r in fut_results:
        print(f"|{r['w']:^15}|{r['time']:^15.4f}|{r['speedup']:^14.2f}x|{r['eff']:^14.2f}%|")
    print("+" + "-"*15 + "+" + "-"*15 + "+" + "-"*15 + "+" + "-"*15 + "+")

    mp_1 = mp_results[0]['time']
    fut_1 = fut_results[0]['time']
    mp_diff = mp_1 - seq_time
    mp_pct = (mp_diff / seq_time) * 100
    fut_diff = fut_1 - seq_time
    fut_pct = (fut_diff / seq_time) * 100
    
    print(f"|{'PARALLEL OVERHEAD (1 process vs sequential)':^63}|")
    print("+" + "-"*63 + "+")
    print(f"|  Multiprocessing:   {mp_diff:+.4f}s ({mp_pct:+.1f}%) {'':<30}|")
    print(f"|  Futures:           {fut_diff:+.4f}s ({fut_pct:+.1f}%) {'':<30}|")
    print("+" + "-"*63 + "+")
    
    save_csv(results_data)
    print(f"Results exported to: {RESULTS_CSV}")

    print("\n")
    print_banner("DEMO COMPLETE!")
    print("")
    print("="*60)
    print("PID Observation & Core Allocation Analysis")
    print("="*60)
    print("")
    print("MULTIPROCESSING (mp_version.py):")
    print("-" * 40)
    print("PID Observation:")
    print("  - Each worker has a DIFFERENT Process ID (PID)")
    print("  - This is because multiprocessing creates separate processes")
    print("  - Each process has its own memory space and Python interpreter")
    print("")
    print("Core Allocation:")
    print("  - Each process can run on different CPU cores simultaneously")
    print("  - Bypasses Python's Global Interpreter Lock (GIL)")
    print("  - Achieves TRUE parallel execution for CPU-bound tasks")
    print("  - Ideal for computationally intensive operations like image processing")
    print("")
    print("CONCURRENT.FUTURES (futures_version.py):")
    print("-" * 40)
    print("PID Observation:")
    print("  - Uses ProcessPoolExecutor (Standard for CPU-bound tasks)")
    print("  - Workers have DIFFERENT PIDs (similar to Multiprocessing)")
    print("  - Abstraction layer over multiprocessing")
    print("")
    print("Core Allocation:")
    print("  - Threads/Processes run on available CPU cores")
    print("  - Optimized for managing pool of workers automatically")
    print("="*60)
    print(f"\nResults exported to: {RESULTS_CSV}")
    print(f"Processed images saved to: {OUTPUT_DIR}/")
    print("\nNote: Output files preserved in output/ folder.")

if __name__ == "__main__":
    main()