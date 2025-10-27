# SERSBench

> **SERSBench** is a lightweight benchmarking toolkit from the SERS Laboratory for generating, compiling, partitioning, and analyzing quantum circuits. It brings together **[BQSKit](https://bqskit.readthedocs.io/)** and **[Qiskit](https://docs.quantum.ibm.com/)** utilities so you can:
>
> - create representative quantum circuits (Clifford, SU2, Quantum Volume, BV, multi‑control, Floquet/DTC)
> - compile/optimize them with configurable partitioning pipelines
> - measure depth / 2‑qubit count / distance metrics across partitions
> - fetch IBM Quantum backend calibration snapshots and analyze gate‑error trends

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![BQSKit](https://img.shields.io/badge/BQSKit-1.2.0-6f42c1)
![Qiskit](https://img.shields.io/badge/Qiskit-1.3.2-512bd4)

---

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [IBM Backend & Gate‑Error Analysis](#ibm-backend--gate-error-analysis)
- [Predetermined Workflows](#predetermined-workflows)
- [Project Layout](#project-layout)
- [Configuration & Notes](#configuration--notes)
- [Contributing](#contributing)
- [License](#license)
- [Cite / Acknowledgements](#cite--acknowledgements)

---

## Features

- **Circuit generation** via `sersbench.create_circuits` (BQSKit & Qiskit backends)
  - Random Clifford (optionally “optimized” variants), SU2 layers, Quantum Volume, BV (all‑ones), multi‑control, and Floquet/DTC unitaries
  - Optional QASM export for each generated circuit
- **Compilation / optimization** via `sersbench.bqskit.optimizeBQSkit`
  - Partitioners: Quick / Scan (3‑qubit blocks) with tunable passes
  - JSON metrics export (depth, large‑gate counts, success thresholds, etc.)
- **Partition analytics** via `sersbench.partitions`
  - Per‑partition **CNOT (large gate) counts** and **depth**
  - Distribution distances (KL‑divergence, χ²) and **comparison CSVs**
  - Optional **pie‑chart** visualizations
- **Backend utilities** via `sersbench.backend`
  - Pull **IBM Quantum** calibration snapshots for a backend and date range
  - Compute and plot **ECR** (two‑qubit) gate error trends, drill into specific pairs

> Pinned versions: see `pyproject.toml` for exact dependencies (BQSKit 1.2.0, Qiskit 1.3.2, qiskit-ibm-runtime 0.36.1, NumPy, pandas, matplotlib).

---

## Installation

### From source (recommended for development)

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/sersbench.git
cd sersbench
python -m venv .venv && source .venv/bin/activate    # on Windows: .venv\Scripts\activate
pip install -U pip
pip install -e .
```

### Direct install from GitHub (once public)

```bash
pip install git+https://github.com/YOUR_GITHUB_USERNAME/sersbench.git
# or, if you use SSH
pip install git+ssh://git@github.com/YOUR_GITHUB_USERNAME/sersbench.git
```

> **Python**: While `pyproject.toml` declares `>=3.7`, we recommend **Python 3.10+** to match modern Qiskit/BQSKit wheels.

---

## Quickstart

Below are typical end‑to‑end snippets. All paths can be files **or** directories of `.qasm` files.

### 1) Generate circuits (Qiskit or BQSKit) and save to QASM

```python
from sersbench.create_circuits import (
    construct_qiskit_clifford_circuit,
    construct_qiskit_bv_all_ones,
    construct_bqskit_QV,
)

# Create a single Qiskit Clifford circuit and write QASM
qc, name = construct_qiskit_clifford_circuit(num_qubits=5, save_path="circuits")

# Create a BV (all-ones) circuit
qc2, name2 = construct_qiskit_bv_all_ones(num_qubits=6, save_path="circuits")

# Create a BQSKit Quantum Volume-style circuit
qc3, name3 = construct_bqskit_QV(num_qubits=5, save_path="circuits")
```

### 2) Compile / optimize with BQSKit

```python
from sersbench.bqskit import optimizeBQSkit

# Optimize every QASM file under ./circuits, write compiled QASM + JSON metrics
optimizeBQSkit(
    qc="circuits",
    save_path="compiled",
    json_path="compiled/metrics.json",
    replace_filter="always",              # 'always' | 'less-than' | 'less-than-multi'
    success_threshold=1e-8,
    partitioner=0,                        # 0: QuickPartitioner, 1: ScanPartitioner
    pass_type=0,                          # choose a predefined pass pipeline
)
```

### 3) Analyze partitions & distances

```python
from sersbench.partitions import (
    partition_data,
    generate_comparison_stats,
    create_distance_piecharts,
)

# Per-partition depth and large (CNOT) gate counts
dfs = partition_data("compiled", csv_save_path="analysis", png_save_path="analysis")

# Cross-circuit comparison CSVs (KL/χ², etc.)
stats = generate_comparison_stats("compiled", save_path="analysis")

# Optional pie charts of distance distributions
create_distance_piecharts("compiled", save_path="analysis")
```

---

## IBM Backend & Gate‑Error Analysis

> These utilities expect calibration JSON snapshots saved locally (e.g., under `./data`). You can **fetch and cache** them with `get_current_backend`, then run the error analytics.

### Fetch calibration snapshots

```python
from datetime import datetime, timedelta
from sersbench.backend import get_current_backend

calibs = get_current_backend(
    token="<YOUR_IBM_QUANTUM_TOKEN>",
    instance="ibm-q/open/main",           # or your hub/group/project instance
    backend_name="ibm_brisbane",
    save_path="data/brisbane",            # JSON files will be written here
    start_date=datetime(2025, 10, 1),
    end_date=datetime(2025, 10, 26),
)
```

> You can create/get an IBM Quantum API token from your account settings. The `instance` typically looks like `ibm-q/open/main` or your specific hub/group/project.

### Compute and visualize gate‑error trends

```python
from sersbench.backend import (
    get_avg_ecr_gate_error,
    get_available_qubit_pairs,
    plot_avg_ecr_error,
    plot_specific_gate_error,
)

# Average ECR error across calibrations
avg = get_avg_ecr_gate_error(data_dir="data/brisbane")

# Discover available two-qubit pairs in your dataset
pairs = get_available_qubit_pairs(data_dir="data/brisbane")

# Plot average ECR error trend (returns an image object/bytes; see docs for how you prefer to save/show)
img = plot_avg_ecr_error(data_dir="data/brisbane")

# Plot time series for a specific pair, e.g., qubits (3, 4)
img2 = plot_specific_gate_error(pair=(3, 4), data_dir="data/brisbane")
```

---

## Predetermined Workflows

For convenience, you can generate a set of circuits and compile them with consistent settings using a single call:

```python
from sersbench.predetermined import predeterminedCompilation

predeterminedCompilation(
    save_path="compiled",
    json_path="compiled/summary.json",
    generate_circuits=True,   # also create representative circuits before compilation
    success_threshold=1e-8,
    replace_filter="always",
    partitioner=0,
)
```

---

## Project Layout

```
sersbench/
├── sersbench/
│   ├── backend/                # IBM backend retrieval + gate-error analytics
│   ├── bqskit/                 # BQSKit compilation wrapper(s)
│   ├── create_circuits/        # Circuit generators (Qiskit + BQSKit)
│   ├── partitions/             # Partition stats, distance metrics, plots
│   └── _internal/              # Shared helpers (prob dists, serialization, etc.)
├── pyproject.toml              # Pinned deps & build metadata
└── README.md
```

---

## Configuration & Notes

- **Operating system paths:** modules normalize Windows vs POSIX paths internally.
- **QASM I/O:** most generators accept `save_path`; compiled circuits and analytics accept directory inputs for batch processing.
- **Distances:** KL‑divergence and χ² utilities expect padded probability distributions (`_padded_prob_dist`) and support CSV export.
- **Logging & errors:** backend retrieval functions return structured error records if a request fails (token/instance/backoff issues).
- **Performance:** BQSKit pipelines can be compute‑heavy; start with small circuits when testing your config.

---

## Contributing

We welcome issues and PRs! A good starting point:

1. **Fork** the repo and create a feature branch:
   ```bash
   git checkout -b feat/my-improvement
   ```
2. **Install dev deps** (optional linters/tests if added later) and run examples in `examples/` (coming soon).
3. **Open a PR** with:
   - a clear description of the behavior change
   - minimal reproducer or unit tests (if applicable)
   - docs/README updates for new user‑facing APIs

> Style: use type hints, docstrings with concise parameter/return docs, and prefer small, composable helpers in `_internal`.

---

## License

This project is licensed under the **MIT License**. See the license text in `pyproject.toml` and include a `LICENSE` file in the public repo.

---

## Cite / Acknowledgements

**Authors & Contributors**  Aarya Balakrishnan, Isbel M. Guerrero, Yasmell Carrasco, Everett Eng, Christian Clancy Rasmussen,

If you use this toolkit in academic work, please cite the repository and include an acknowledgement to the *SERS Laboratory*. A minimal BibTeX entry (update the URL/commit when the repo is public):

```bibtex
@software{sersbench,
  title        = {SERSBench: A benchmarking toolkit for quantum circuit generation, compilation, and partition analysis},
  author       = {Eng, Everett and Rasmussen, Christian Clancy and Balakrishnan, Aarya and Guerrero, Isbel M. and Carrasco, Yasmell},
  year         = {2025},
  url          = {https://github.com/YOUR_GITHUB_USERNAME/sersbench},
  license      = {MIT}
}
```

---

### Questions?

Please open a GitHub issue or start a discussion in the repository.
