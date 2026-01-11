# Parallel Image Processing Pipeline on GCP
### CST435: Parallel and Cloud Computing - Assignment 2

This project implements a high-performance image processing pipeline designed to benchmark and analyze parallel computing paradigms in Python. The system processes images from the Food-101 dataset by applying a chain of computationally intensive filters (Grayscale, Gaussian Blur, Sobel Edge Detection, Sharpening, and Brightness Adjustment).

To evaluate performance scalability, the pipeline is implemented using three different execution strategies:
1.  **Sequential Execution** (Baseline)
2.  **Multiprocessing** (using `multiprocessing.Pool`)
3.  **Concurrent Futures** (using `ProcessPoolExecutor` and `ThreadPoolExecutor`)

## 👥 Group Members
* **MUHAMMAD HAZIQ BIN SAZALI** - 163646
* **MUHAMMAD ARFAN BIN ZUHAIME** - 161508
* **MUHAMMAD HAZIQ BIN MOHAMAD RODZALI** - 161423
* **TAI JIA HUI** - 164852

---

## 🚀 Features
* **5-Stage Filter Pipeline:** Simulates real-world CPU-bound image manipulation.
* **Multi-Core Utilization:** Leverages all available CPU cores to speed up processing.
* **Performance Analysis:** Automatically generates charts comparing Execution Time, Speedup, and Efficiency.
* **GCP Ready:** Designed to run seamlessly on Google Cloud Platform Compute Engine instances.

---

## 🛠️ Prerequisites

* **Python 3.8+**
* **Pip** (Python Package Manager)

### Required Libraries
The project relies on the following Python packages:
* `numpy` (Matrix operations)
* `matplotlib` (Graph plotting)
* `Pillow` (Image loading/saving)
* `tqdm` (Progress bars)
* `colorama` (Console output coloring)
* `psutil` (System resource monitoring)

---

## 📥 Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/cst435-assignment2.git](https://github.com/YOUR_USERNAME/cst435-assignment2.git)
    cd cst435-assignment2
    ```

2.  **Install Dependencies**
    You can install all required libraries using the following command:
    ```bash
    pip install numpy matplotlib tqdm colorama Pillow psutil
    ```

3.  **Prepare the Dataset**
    The script expects a specific directory structure for the input images.
    1.  Create a folder named `data` and a subfolder `food-101` in the project root.
    2.  Place your `.jpg` images inside `data/food-101`.

    **Directory Structure:**
    ```text
    /project-root
      ├── main.py
      ├── filters.py
      ├── run_seq.py
      ├── run_mp.py
      ├── run_fut.py
      └── data/
          └── food-101/
              ├── image1.jpg
              ├── image2.jpg
              └── ...
    ```

---

## 💻 Usage

To run the full benchmark suite, simply execute `main.py`. The script will automatically detect the number of CPU cores and run tests for Sequential, Multiprocessing, and Concurrent Futures implementations.

### Basic Run
```bash
python main.py
```

### Run with a Specific Number of Images
If you want to test with a smaller subset of images (e.g., for quick debugging), use the `--images` flag:

```bash
python main.py --images 50
```

Default is 1000 images.

### Output
* After execution, the program creates an output/ directory containing:
* Processed Images: A sample of images to verify the filters worked.
* benchmark_results.csv: Raw data of the run.

* Analysis Charts:
* analysis_execution_time.
* pnganalysis_speedup.
* pnganalysis_efficiency.png

---

## 📂 Project Structure
* main.py: The entry point. Handles argument parsing, dataset loading, orchestration of the benchmark runs, and graph generation.
* filters.py: Contains the core image processing logic (Grayscale, Blur, Sobel, etc.) using NumPy and PIL.
* run_seq.py: Implementation of the Sequential (single-threaded)
* runner.run_mp.py: Implementation using the multiprocessing module (bypasses GIL).
* run_fut.py: Implementation using concurrent.futures (Benchmarks both ProcessPool and ThreadPool).

### 📊 Implementation Details
* Image Processing Pipeline (filters.py)Each image undergoes the following transformation chain:
* Grayscale: Weighted conversion ($0.299R + 0.587G + 0.114B$).
* Gaussian Blur: Convolution with a $3 \times 3$ kernel.
* Sobel Edge Detection: Gradient calculation in X and Y directions.
* Sharpening: Kernel-based edge enhancement.
* Brightness: Pixel intensity scaling and clipping.

### Parallel Paradigms
* Multiprocessing (run_mp.py): Uses multiprocessing.Pool with imap. This spawns separate memory spaces for each worker, effectively bypassing the Global Interpreter Lock (GIL) to achieve true parallelism on multi-core CPUs.
* ProcessPoolExecutor (run_fut.py): High-level abstraction for multiprocessing.
* ThreadPoolExecutor (run_fut.py): Included for comparison. Demonstrates the limitations of Python threads for CPU-bound tasks due to the GIL.

---

## 📝 AcknowledgmentsDataset:
* Food-101 (Kaggle)
* Course: CST435 Parallel and Cloud Computing, USM.
