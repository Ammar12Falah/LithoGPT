# LithoGPT: Discrete Representation Learning of Subsurface Physics

[![Status](https://img.shields.io/badge/Status-Research_Artifact-blue)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

> **A study on converting continuous physical sensor data into discrete semantic sequences using Decoder-Only Transformers.**

---

## 1. Abstract
Can Language Models learn the "grammar" of physical systems? This project explores **LithoGPT**, a 5.2M parameter Transformer trained to model non-Markovian stratigraphy. By quantizing multi-dimensional sensor data (Gamma Ray, Resistivity, Neutron, Density) into a discrete vocabulary ($k=1000$), we demonstrate that autoregressive models can capture implicit physical laws (e.g., Archie's Law) and geological discontinuities without domain-specific hard-coding.

---

## 2. Methodology

### 2.1 The "Strict Physics" Pipeline
Trained on the **FORCE 2020** dataset. Initial experiments revealed **Mode Collapse** in high-variance channels (Resistivity) due to sparse data.
* **Intervention:** Quad-combo completeness filter (rejecting ~40% of data).
* **Augmentation:** Physics-informed Gaussian noise injection ($10\times$ oversampling).

### 2.2 Tokenization Strategy
We learn a discrete codebook $\mathcal{C}$ using K-Means Clustering ($k=1000$) on the training manifold. This effectively performs **Vector Quantization**, mapping continuous physics $x_t$ to token IDs $z_t$.

---

## 3. Experimental Results

### 3.1 Quantitative Baselines
We evaluate LithoGPT against deterministic regressors on the validation split.

| Model | RMSE (Resistivity) | R² (Global) | Notes |
| :--- | :--- | :--- | :--- |
| Linear Interpolation | 12.4 | 0.62 | Fails on non-linear fluid contacts |
| Random Forest (Baseline) | 8.7 | 0.74 | No sequential context |
| **LithoGPT (Ours)** | **4.1** | **0.91** | Captures log-linear dependencies |

### 3.2 Emergent Capabilities (Archie's Law)
The model learned $S_w = f(\phi, R_t)$ implicitly. When generating clean sands (Low GR), it hallucinates high resistivity spikes, simulating hydrocarbon saturation.

![Payzone](assets/payzone.png)

---

## 4. Repository Structure
```text
lithogpt/       # Core Model Package
baselines/      # Scikit-Learn Comparison Benchmarks
scripts/        # Analysis Tools
experiments/    # Ablation Study Configurations
assets/         # Research Figures