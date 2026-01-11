import os
import argparse
import multiprocessing
import sys
import time
import datetime
import random
import matplotlib.pyplot as plt
import numpy as np
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
CHART_TIME = os.path.join(OUTPUT_DIR, "analysis_execution_time.png")
CHART_SPEEDUP = os.path.join(OUTPUT_DIR, "analysis_speedup.png")
CHART_EFF = os.path.join(OUTPUT_DIR, "analysis_efficiency.png")

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

def generate_charts(results_dict, worker_counts):
    """
    Creates professional Matplotlib charts for your report.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    modes = ['Multiprocessing', 'ProcessPool', 'ThreadPool']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    # 1. Execution Time (Line Chart)
    plt.figure(figsize=(10, 6))
    for idx, mode in enumerate(modes):
        if not results_dict[mode]: continue
        times = [r['time'] for r in results_dict[mode]]
        plt.plot(worker_counts, times, marker='o', linewidth=2, label=mode, color=colors[idx])
    
    plt.title(f"Execution Time vs Workers (Lower is Better)")
    plt.xlabel("Number of Workers")
    plt.ylabel("Time (seconds)")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.savefig(CHART_TIME)
    plt.close()

    # 2. Speedup (Line Chart)
    plt.figure(figsize=(10, 6))
    for idx, mode in enumerate(modes):
        if not results_dict[mode]: continue
        speedups = [r['speedup'] for r in results_dict[mode]]
        plt.plot(worker_counts, speedups, marker='s', linewidth=2, label=mode, color=colors[idx])
    
    # Add Ideal Linear Speedup Line
    plt.plot(worker_counts, worker_counts, 'k--', label="Ideal Linear Speedup")
    
    plt.title(f"Speedup vs Workers (Higher is Better)")
    plt.xlabel("Number of Workers")
    plt.ylabel("Speedup Factor (x)")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.savefig(CHART_SPEEDUP)
    plt.close()

    # 3. Efficiency (Bar Chart)
    plt.figure(figsize=(10, 6))
    x = np.arange(len(worker_counts))
    width = 0.25
    
    for idx, mode in enumerate(modes):
        if not results_dict[mode]: continue
        effs = [r['efficiency'] for r in results_dict[mode]]
        plt.bar(x + (idx * width), effs, width, label=mode, color=colors[idx])

    plt.axhline(y=100, color='k', linestyle='--', alpha=0.5)
    plt.title(f"Efficiency vs Workers")
    plt.xlabel("Number of Workers")
    plt.ylabel("Efficiency (%)")
    plt.xticks(x + width, worker_counts)
    plt.legend(loc='lower left')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig(CHART_EFF)
    plt.close()

def main():
    multiprocessing.freeze_support()
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--images', type=int, default=100, help='Number of images')
    args = parser.parse_args()

    if not os.path.exists(INPUT_DIR):
        print(f"Error: Data directory not found: {INPUT_DIR}")
        return

    import glob
    all_images = glob.glob(os.path.join(INPUT_DIR, "**", "*.jpg"), recursive=True)
    if not all_images:
        print(f"No images found in {INPUT_DIR}")
        return

    random.shuffle(all_images)
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

    # Storage for results
    worker_counts = [1, 2, 4]
    results_db = {
        'Multiprocessing': [],
        'ProcessPool': [],
        'ThreadPool': []
    }

    # Dummy callback for cleaner output
    def progress_handler(pbar):
        def inner(info):
            pbar.update(1)
        return inner

    # ---------------------------------------------------------
    # STEP 1: SEQUENTIAL BASELINE
    # ---------------------------------------------------------
    print_step_header(1, "Sequential Baseline")
    print_section_header("Sequential Pipeline")
    print(f"Images to process: {len(subset_images)}")
    
    seq_time = run_seq.run_sequential_task(subset_images, OUTPUT_DIR)
    
    print("\nSummary")
    print("-------")
    print(f"Total time: {seq_time:.4f} seconds")
    print(f"Average time per image: {seq_time/len(subset_images):.4f} seconds\n")

    # ---------------------------------------------------------
    # STEP 2: MULTIPROCESSING PIPELINE
    # ---------------------------------------------------------
    print_step_header(2, "Multiprocessing Pipeline")
    
    for w in worker_counts:
        print(f"\n>>> Testing with {w} processes...")
        print_section_header("Multiprocessing Pipeline")
        
        pbar = tqdm(total=len(subset_images), ncols=80, 
                   bar_format=f"Multiprocessing Pool ({w}): {{percentage:3.0f}}%|{{bar}}| {{n_fmt}}/{{total_fmt}}")
        
        t_mp, _ = run_mp.run_multiprocessing_task(subset_images, OUTPUT_DIR, w, progress_handler(pbar))
        pbar.close()
        
        s_mp = seq_time / t_mp
        e_mp = (s_mp / w) * 100
        
        print(f"\nSummary (Workers: {w})")
        print(f"-------")
        print(f"Total time: {t_mp:.4f} s")
        print(f"Speedup: {s_mp:.2f}x")
        print(f"Efficiency: {e_mp:.2f}%")
        
        results_db['Multiprocessing'].append({'time': t_mp, 'speedup': s_mp, 'efficiency': e_mp})

    # ---------------------------------------------------------
    # STEP 3: CONCURRENT.FUTURES PIPELINE
    # ---------------------------------------------------------
    print("\n")
    print_step_header(3, "Concurrent.Futures Pipeline")
    
    # Part A: ProcessPool
    print("\n[A] ProcessPoolExecutor (CPU-Bound Optimized)")
    for w in worker_counts:
        print(f">>> Testing with {w} workers...")
        pbar = tqdm(total=len(subset_images), ncols=80, 
                   bar_format=f"ProcessPool ({w}): {{percentage:3.0f}}%|{{bar}}| {{n_fmt}}/{{total_fmt}}")
        
        t_proc = run_fut.run_futures_task(subset_images, OUTPUT_DIR, w, progress_handler(pbar), mode='process')
        pbar.close()
        
        s_proc = seq_time / t_proc
        e_proc = (s_proc / w) * 100
        results_db['ProcessPool'].append({'time': t_proc, 'speedup': s_proc, 'efficiency': e_proc})

    # Part B: ThreadPool
    print("\n[B] ThreadPoolExecutor (I/O-Bound Optimized)")
    for w in worker_counts:
        print(f">>> Testing with {w} threads...")
        pbar = tqdm(total=len(subset_images), ncols=80, 
                   bar_format=f"ThreadPool ({w}): {{percentage:3.0f}}%|{{bar}}| {{n_fmt}}/{{total_fmt}}")
        
        t_thread = run_fut.run_futures_task(subset_images, OUTPUT_DIR, w, progress_handler(pbar), mode='thread')
        pbar.close()
        
        s_thread = seq_time / t_thread
        e_thread = (s_thread / w) * 100
        results_db['ThreadPool'].append({'time': t_thread, 'speedup': s_thread, 'efficiency': e_thread})

    # ---------------------------------------------------------
    # STEP 4: ANALYSIS & CHARTS
    # ---------------------------------------------------------
    print("\nGenerating Analysis Charts...")
    generate_charts(results_db, worker_counts)
    
    print_banner("PERFORMANCE METRICS SUMMARY")
    
    # Print Table
    print(f"{'Paradigm':<20} | {'Workers':<8} | {'Time (s)':<10} | {'Speedup':<10} | {'Efficiency':<10}")
    print("-" * 75)
    
    for mode in ['Multiprocessing', 'ProcessPool', 'ThreadPool']:
        for idx, res in enumerate(results_db[mode]):
            w = worker_counts[idx]
            print(f"{mode:<20} | {w:<8} | {res['time']:<10.4f} | {res['speedup']:<10.2f}x | {res['efficiency']:<10.2f}%")
        print("-" * 75)

    print("\n" + "="*70)
    print("ANALYSIS & INSIGHTS")
    print("="*70)
    
    # Scalability Analysis
    mp_speedup_4 = results_db['Multiprocessing'][-1]['speedup']
    th_speedup_4 = results_db['ThreadPool'][-1]['speedup']
    
    print("1. SCALABILITY:")
    print(f"   - Multiprocessing achieved {mp_speedup_4:.2f}x speedup with 4 workers.")
    
    print(f"   - ThreadPool achieved {th_speedup_4:.2f}x speedup with 4 workers.")
    if mp_speedup_4 > th_speedup_4:
        print("   -> CONCLUSION: Multiprocessing scales better for Image Processing.")
        print("      This confirms the task is CPU-Bound. The GIL (Global Interpreter Lock)")
        print("      prevented Threads from utilizing all cores effectively.")
    else:
        print("   -> CONCLUSION: Threading performed unexpectedly well (possibly due to I/O bottlenecks).")

    # Amdahl's Law Discussion
    print("\n2. AMDAHL'S LAW IMPLICATIONS:")
    max_s = results_db['Multiprocessing'][-1]['speedup']
    n = worker_counts[-1]
    # Calculate observed P
    try:
        observed_p = (n / (n - 1)) * (1 - (1 / max_s))
        if observed_p > 1: observed_p = 0.99 # Cap at 99%
        print(f"   - Observed Parallel Portion (P): {observed_p:.2f} ({observed_p*100:.1f}%)")
        print(f"   - Serial Bottleneck (1-P): {1-observed_p:.2f} ({(1-observed_p)*100:.1f}%)")
        print("     (Bottlenecks include: Disk I/O reading images, Process startup overhead)")
    except:
        print("   - Speedup insufficient to calculate accurate Amdahl P.")

    print("\n3. TRADE-OFFS:")
    print("   - Multiprocessing: High Speedup, High Memory Usage (separate memory space).")
    print("   - Threading: Low Speedup (CPU-bound), Low Memory Usage (shared memory).")

    print(f"\nFull report and charts saved in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()

