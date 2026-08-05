# TinyLlama Instruction Tuning with LoRA

> Parameter-efficient fine-tuning of **TinyLlama-1.1B-Chat** using **Low-Rank Adaptation (LoRA)** and **Supervised Fine-Tuning (SFT)** on the **Databricks Dolly-15K** instruction dataset.

This project demonstrates how a **1.1B parameter language model** can be adapted for improved instruction following while training only **0.1023%** of its parameters on a **single Tesla T4 GPU**.

---

# Overview

Full fine-tuning of large language models requires updating billions of parameters, making training computationally expensive.

This project instead uses **LoRA (Low-Rank Adaptation)** to freeze the original TinyLlama weights and inject small trainable low-rank matrices into selected attention layers.

The complete workflow includes:

- Baseline evaluation of TinyLlama
- Dolly-15K dataset preparation
- Chat-template formatting
- LoRA adapter configuration
- Supervised Fine-Tuning (SFT) using TRL
- Training loss monitoring
- Saving LoRA adapters
- Base vs. fine-tuned model evaluation

---

# Model & Dataset

## Base Model

**TinyLlama/TinyLlama-1.1B-Chat-v1.0**

## Dataset

**databricks/databricks-dolly-15k**

A shuffled subset of **1,000 instruction-response examples** was used for training.

Each Dolly example was converted into conversational format:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "..."
    },
    {
      "role": "assistant",
      "content": "..."
    }
  ]
}
```

Whenever an example contained additional context, it was appended to the user instruction before training.

---

# LoRA Configuration

| Parameter | Value |
|-----------|------:|
| Rank (r) | 8 |
| Alpha | 16 |
| Dropout | 0.05 |
| Target Modules | `q_proj`, `v_proj` |
| Bias | None |
| Task | Causal Language Modeling |

LoRA adapters were injected into the **query** and **value projection** layers of TinyLlama's attention mechanism.

---

# Parameter Efficiency

| Metric | Result |
|---------|-------:|
| Total Parameters | 1,101,174,784 |
| Trainable Parameters | 1,126,400 |
| Trainable Percentage | **0.1023%** |
| LoRA Adapter Size | **7.77 MB** |

More than **99.8%** of the original model parameters remained frozen during training.

---

# Training Configuration

| Hyperparameter | Value |
|---------------|------:|
| Training Samples | 1,000 |
| Epochs | 1 |
| Batch Size | 4 |
| Gradient Accumulation | 4 |
| Effective Batch Size | 16 |
| Learning Rate | 2e-4 |
| Maximum Sequence Length | 512 |
| LR Scheduler | Cosine |
| Warmup Ratio | 0.03 |
| Weight Decay | 0.01 |
| Gradient Checkpointing | Enabled |

Training was performed using **Hugging Face TRL's `SFTTrainer`** with **PEFT/LoRA** integration.

---

# Training Results

Training completed in **63 optimization steps** for one epoch.

### Training Loss

| Step | Loss |
|------|-----:|
| 10 | ~2.11 |
| 20 | ~1.88 |
| 30 | ~1.77 |
| 40 | ~1.74 |
| 50 | ~1.78 |
| 60 | ~1.73 |

**Final Training Loss:** **~1.83**

The overall downward trend indicates that the LoRA parameters successfully learned from the instruction-response dataset.

---

# Evaluation

The **base** and **fine-tuned** models were evaluated using prompts covering:

- Simple concept explanation
- Professional email generation
- Structured list generation
- Python programming knowledge

### Observed Improvements

The fine-tuned model produced:

- More concise responses
- Better adherence to requested formats
- Improved response structure
- Better handling of prompts requesting a specific number of items

Since the experiment uses only **1,000 examples** and **one training epoch**, it primarily demonstrates **parameter-efficient adaptation** rather than full domain specialization.

---

# Tech Stack

- Python
- PyTorch
- Hugging Face Transformers
- Hugging Face PEFT
- Hugging Face TRL
- Hugging Face Datasets
- LoRA
- TinyLlama
- Databricks Dolly-15K
- CUDA
- Google Colab
- NVIDIA Tesla T4

---

# Running the Project

## 1. Install Dependencies

```bash
pip install -U transformers trl peft datasets accelerate torch
```

---

## 2. Run the Notebook

Open **`LORA_Assignment.ipynb`** and execute the cells sequentially.

```
Load TinyLlama
      │
      ▼
Evaluate Base Model
      │
      ▼
Prepare Dolly-15K Dataset
      │
      ▼
Inject LoRA Adapters
      │
      ▼
Run Supervised Fine-Tuning
      │
      ▼
Save LoRA Adapter
      │
      ▼
Evaluate Fine-Tuned Model
```

A CUDA-capable GPU is recommended. The project was trained using a **Tesla T4**.

---

# Project Structure

```
tinyllama-lora-instruction-tuning/
│
├── LORA_Assignment.ipynb
├── README.md
└── assets/                 # Optional figures/results
```

---

# Key Takeaway

This project demonstrates that useful LLM adaptation does **not** require full-model fine-tuning.

By leveraging **LoRA**, TinyLlama was successfully adapted while updating only **0.1023%** of its parameters, producing a reusable adapter of only **7.77 MB**.

This highlights the effectiveness of **parameter-efficient fine-tuning (PEFT)** for adapting large language models with limited computational resources.

---

# Future Improvements

Possible extensions include:

- Train on the full Dolly-15K dataset
- Experiment with different LoRA ranks (`r`)
- Fine-tune additional attention modules
- Compare multiple training epochs
- Evaluate on standardized instruction-following benchmarks
- Merge LoRA adapters into the base model for standalone inference
- Compare LoRA with other PEFT techniques (QLoRA, AdaLoRA, IA³)

---

# References

- TinyLlama
- Hugging Face Transformers
- Hugging Face PEFT
- Hugging Face TRL
- Databricks Dolly-15K
- LoRA: Low-Rank Adaptation of Large Language Models


---

# Author

**Koushik Jayanthi**

Software Engineer | AI & Machine Learning | Java Backend Developer

**LinkedIn**: https://www.linkedin.com/in/koushik-jayanthi-2b86b5153/

**GitHub**: https://github.com/Koushik999999