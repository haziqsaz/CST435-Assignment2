# CST435 Assignment 2: Parallel Image Processing System

**Course:** CST435 - Parallel and Cloud Computing  
**University:** Universiti Sains Malaysia (USM)  
**Session:** 2025/2026  

## Project Overview

This project implements a high-performance parallel image processing pipeline designed to deploy and execute on the Google Cloud Platform (GCP). The system applies a series of computational filters to the **Food-101** dataset.

The primary objective is to analyze the performance characteristics (speedup, efficiency, and scalability) of different parallel programming paradigms in Python compared to a sequential baseline.

## Group Members

| No. | Name | Matric No. |
| :--- | :--- | :--- |
| 1 | [Enter Name Here] | [Enter Matric] |
| 2 | [Enter Name Here] | [Enter Matric] |
| 3 | [Enter Name Here] | [Enter Matric] |
| 4 | [Enter Name Here] | [Enter Matric] |

---

## Features

### Image Processing Pipeline
The system implements a custom convolution engine (using `numpy`) to apply the following five filters in sequence:

1.  **Grayscale Conversion:** Converts RGB images to luminance grayscale.
2.  **Gaussian Blur:** Applies a $3\times3$ Gaussian kernel for smoothing.
3.  **Edge Detection:** Uses Sobel filters (Gx and Gy) to detect vertical and horizontal edges.
4.  **Image Sharpening:** Enhances details using a sharpening kernel.
5.  **Brightness Adjustment:** Increases brightness and clips values.

### Parallel Paradigms Implemented
As per the assignment requirements (Option 2: Python), the pipeline is implemented using three distinct execution modes:

1.  **Sequential (Baseline):** Single-threaded execution for performance comparison.
2.  **Multiprocessing (`multiprocessing` module):** Uses a pool of worker processes to bypass the Global Interpreter Lock (GIL), ideal for CPU-bound tasks.
3.  **Concurrent Futures (`concurrent.futures`):**
    * **ProcessPoolExecutor:** High-level interface for process-based parallelism.
    * **ThreadPoolExecutor:** Thread-based parallelism (primarily for analyzing GIL limitations in CPU-bound tasks).

---

## Project Structure

```text
CST435-Assignment2/
├── data/
│   └── food-101/           # Dataset directory (images stored here)
├── output/                 # Generated results (charts, processed images)
├── filters.py              # Core image processing logic (convolution kernels)
├── main.py                 # Main entry point, benchmarking, and charting
├── run_seq.py              # Sequential implementation wrapper
├── run_mp.py               # Multiprocessing implementation wrapper
├── run_fut.py              # Concurrent.futures wrapper (Thread & Process)
└── README.md               # Project documentation

---

## Installation & Setup

### 1. Prerequisites
* Python 3.8+
* Recommended: A virtual environment (`venv` or `conda`)

### 2. Install Dependencies
Install the required Python libraries used in the source code:

```bash
pip install numpy matplotlib tqdm colorama Pillow psutil

## 3. Dataset Setup

This project uses the **Food-101** dataset.

### Steps

1. Download the dataset from Kaggle: *Food-101 Dataset*  
2. Extract the contents.  
3. Ensure the images are located at:

```text
data/food-101/images

## Usage

Run the main script to start the benchmark. The script will automatically detect the CPU core count and run tests using:

- Sequential  
- Multiprocessing  
- Concurrent Futures  

---

### Basic Run

Runs the benchmark on a random subset of 100 images (default):

```bash
python main.py

Custom Image Count

To test scalability with a larger dataset (e.g., 500 images):

python main.py --images 500

Performance Analysis

The main.py script automatically generates a performance report upon completion.

Metrics Calculated

Execution Time
Total time taken to process the batch.

Speedup

𝑆
𝑝
𝑒
𝑒
𝑑
𝑢
𝑝
=
𝑇
𝑖
𝑚
𝑒
𝑠
𝑒
𝑞
𝑢
𝑒
𝑛
𝑡
𝑖
𝑎
𝑙
𝑇
𝑖
𝑚
𝑒
𝑝
𝑎
𝑟
𝑎
𝑙
𝑙
𝑒
𝑙
Speedup=
Time
parallel
	​

Time
sequential
	​

	​


Efficiency

𝐸
𝑓
𝑓
𝑖
𝑐
𝑖
𝑒
𝑛
𝑐
𝑦
=
𝑆
𝑝
𝑒
𝑒
𝑑
𝑢
𝑝
𝑁
𝑢
𝑚
𝑏
𝑒
𝑟
_
𝑜
𝑓
_
𝑊
𝑜
𝑟
𝑘
𝑒
𝑟
𝑠
×
100
%
Efficiency=
Number_of_Workers
Speedup
	​

×100%
Generated Outputs

After execution, check the output/ directory for:

benchmark_results.csv – Raw timing data

analysis_execution_time.png – Line chart comparing execution speeds

analysis_speedup.png – Graph showing scalability vs. ideal linear speedup

analysis_efficiency.png – Bar chart showing resource utilization

Processed Images – Subfolders containing the output images from the pipeline

Observations & Theory
Multiprocessing vs. Threading

In Python, image processing is a CPU-bound task. Due to the Global Interpreter Lock (GIL), standard threading (ThreadPoolExecutor) often provides poor speedup compared to multiprocessing (ProcessPoolExecutor or multiprocessing.Pool), which uses separate memory spaces for each worker.

Amdahl’s Law

The maximum theoretical speedup is limited by the serial portion of the program (e.g., disk I/O when reading/writing images and process startup overhead). The generated logs attempt to estimate the observed parallel portion of the task.

Acknowledgments

Universiti Sains Malaysia (USM)

Food-101 Dataset creators
