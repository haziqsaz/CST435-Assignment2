import os
import argparse
import multiprocessing
import sys
import time
import datetime
import random
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

# Amdahl's Parameter: Assumed Parallel Portion (95%)
PARALLEL_PORTION_THEORETICAL = 0.95 
# ---------------------

def calculate_amdahl_speedup(workers, p):
    """
    Theoretical Speedup = 1 / ((1 - P) + (P / N))
    """
    if workers == 1: return 1.0
    return 1 / ((1 - p) + (p / workers))

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
            f.write("Paradigm,Workers,Time,Actual_Speedup,Theoretical_Speedup,Efficiency\n")
            for r in results:
                f.write(f"{r['mode']},{r['workers']},{r['time']:.4f},{r['speedup']:.2f},{r['amdahl_speedup']:.2f},{r['efficiency']:.2f}\n")
    except Exception as e:
        print(f"Warning: Could not save CSV: {e}")

def main():
    multiprocessing.freeze_support()
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--images', type=int, default=1000, help='Number of images')
    args = parser.parse_args()

    if not os.path.exists(INPUT_DIR):
        print(f"Error: Data directory not found: {INPUT_DIR}")
        return

    import glob
    all_images = glob.glob(os.path.join(INPUT_DIR, "**", "*.jpg"), recursive=True)
    
    if not all_images:
        print(f"No images found in {INPUT_DIR}")
        return

    # Randomize images for fair benchmarking
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
        print(f"Worker processes: {p}\n")

        # Escaped braces for f-string + tqdm compatibility
        pbar = tqdm(total=len(subset_images), 
                    bar_format=f"Multiprocessing Pool ({p} processes): {{percentage:3.0f}}%|{{bar}}| {{n_fmt}}/{{total_fmt}}",
                    ncols=80)
        
        mp_time, workers_used = run_mp.run_multiprocessing_task(
            subset_images, OUTPUT_DIR, p, progress_callback(pbar, "Process")
        )
        pbar.close()

        speedup = seq_time / mp_time
        amdahl_s = calculate_amdahl_speedup(p, PARALLEL_PORTION_THEORETICAL)
        eff = (speedup / p) * 100
        
        print("\nSummary")
        print("-------")
        print(f"Total time: {mp_time:.4f} seconds")
        print(f"Unique workers used: {workers_used}")
        print(f"    Actual Speedup: {speedup:.2f}x")
        print(f"    Theoretical Speedup (Amdahl P=0.95): {amdahl_s:.2f}x")
        print(f"    Efficiency: {eff:.2f}%")
        
        mp_results.append({'p': p, 'time': mp_time, 'speedup': speedup, 'amdahl': amdahl_s, 'eff': eff})
        results_data.append({'mode': 'MP', 'workers': p, 'time': mp_time, 'speedup': speedup, 'amdahl_speedup': amdahl_s, 'efficiency': eff})

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
        print_section_header("Concurrent.Futures Pipeline")
        print(f"Max workers: {w}\n")

        pbar = tqdm(total=len(subset_images), 
                    bar_format=f"Futures ProcessPool ({w} workers): {{percentage:3.0f}}%|{{bar}}| {{n_fmt}}/{{total_fmt}}",
                    ncols=80)

        fut_time = run_fut.run_futures_task(
            subset_images, OUTPUT_DIR, w, progress_callback_fut(pbar, "Future")
        )
        pbar.close()

        speedup = seq_time / fut_time
        amdahl_s = calculate_amdahl_speedup(w, PARALLEL_PORTION_THEORETICAL)
        eff = (speedup / w) * 100
        
        print("\nSummary")
        print("-------")
        print(f"Total time: {fut_time:.4f} seconds")
        print(f"    Actual Speedup: {speedup:.2f}x")
        print(f"    Theoretical Speedup (Amdahl P=0.95): {amdahl_s:.2f}x")
        print(f"    Efficiency: {eff:.2f}%")
        
        fut_results.append({'w': w, 'time': fut_time, 'speedup': speedup, 'amdahl': amdahl_s, 'eff': eff})
        results_data.append({'mode': 'Fut', 'workers': w, 'time': fut_time, 'speedup': speedup, 'amdahl_speedup': amdahl_s, 'efficiency': eff})

    # FINAL REPORT
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    print("\n+" + "-"*78 + "+")
    print(f"|{'BENCHMARK SUMMARY':^78}|")
    print("+" + "-"*78 + "+")
    print(f"|  Timestamp: {timestamp:<63}|")
    print(f"|  Images: {len(subset_images):<66}|")
    print(f"|  Seq Time: {seq_time:.4f}s {'':<61}|")
    
    # Table Header
    print("+" + "-"*15 + "+" + "-"*10 + "+" + "-"*15 + "+" + "-"*18 + "+" + "-"*15 + "+")
    print(f"|{'Mode':^15}|{'CPUs':^10}|{'Time (s)':^15}|{'Speedup (Actual)':^18}|{'Amdahl (Theory)':^15}|")
    print("+" + "-"*15 + "+" + "-"*10 + "+" + "-"*15 + "+" + "-"*18 + "+" + "-"*15 + "+")
    
    # Rows
    for r in mp_results:
        print(f"|{'MultiProc':^15}|{r['p']:^10}|{r['time']:^15.4f}|{r['speedup']:^18.2f}x|{r['amdahl']:^15.2f}x|")
    print("+" + "-"*15 + "+" + "-"*10 + "+" + "-"*15 + "+" + "-"*18 + "+" + "-"*15 + "+")
    
    for r in fut_results:
        print(f"|{'Futures':^15}|{r['w']:^10}|{r['time']:^15.4f}|{r['speedup']:^18.2f}x|{r['amdahl']:^15.2f}x|")
    print("+" + "-"*15 + "+" + "-"*10 + "+" + "-"*15 + "+" + "-"*18 + "+" + "-"*15 + "+")

    save_csv(results_data)
    
    print("\n")
    print_banner("AMDAHL'S LAW ANALYSIS")
    
    # Calculate Observed Parallel Fraction (P) based on 4-core Multiprocessing result
    # Formula derived from Amdahl's: P = (N / (N-1)) * (1 - 1/S)
    best_run = next((r for r in mp_results if r['p'] == 4), None)
    if best_run:
        N = 4
        S = best_run['speedup']
        if S > 1:
            P_observed = (N / (N - 1)) * (1 - (1 / S))
            print(f"Based on your 4-core Multiprocessing run:")
            print(f"  - Observed Speedup (S): {S:.2f}x")
            print(f"  - Estimated Parallel Portion (P): {P_observed:.2f} ({P_observed*100:.1f}%)")
            print(f"  - Serial Portion (1-P): {1-P_observed:.2f} ({(1-P_observed)*100:.1f}%)")
            print(f"    (This represents I/O, process spawning, and other non-parallel overhead)")
        else:
            print("  - Speedup was < 1, indicating overhead outweighed parallel benefits (common with small image counts).")

    print("\n" + "="*70)
    print("DEMO COMPLETE!")
    print("="*70)
    print(f"Results exported to: {RESULTS_CSV}")

if __name__ == "__main__":
    main()
