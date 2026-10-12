# AI & Machine Learning Projects
### End-to-End AI, Machine Learning, Deep Learning & Generative AI Portfolio

Welcome to my AI & Machine Learning portfolio.

This repository contains a growing collection of **end-to-end AI projects** built to solve real-world business problems using Machine Learning, Deep Learning, and Generative AI. Each project follows a complete development lifecycle—from understanding the business problem and performing Exploratory Data Analysis (EDA) to model development, evaluation, and actionable business recommendations.

> **📌 Repository Status:** This repository is actively maintained and will continue to grow with new AI, Machine Learning, Deep Learning, NLP, Computer Vision, LLM, RAG, and MLOps projects.

---

# Project Portfolio

| Project                                        | Problem Type                         | Domain                     | Techniques                                                                                     | Status |
| ---------------------------------------------- | ------------------------------------ | -------------------------- | ---------------------------------------------------------------------------------------------- | :----: |
| 📢 **Ad Targeting Customer Segmentation**      | Customer Segmentation                | Digital Marketing          | K-Means, Autoencoder, Deep Learning                                                            |    ✅   |
| 🌱 **Carbon Emission Prediction**              | Regression                           | Sustainability             | Linear Regression, Ensemble Models, Feature Engineering                                        |    ✅   |
| 🌍 **Global Development Country Segmentation** | Country Segmentation                 | Public Policy              | PCA, K-Means, Hierarchical Clustering                                                          |    ✅   |
| ▶️ **YouTube Shorts Engagement Prediction**    | Classification                       | Social Media Analytics     | Logistic Regression, Random Forest, KNN, SVM                                                   |    ✅   |
| 🛒 **Ecommerce Customer Analytics**            | Business Analytics                   | E-commerce                 | RFM Analysis, Cohort Analysis, CLV, Statistical Analysis                                       |    ✅   |
| ⭐ **Amazon Product Recommendation System**     | Recommendation System                | E-commerce                 | TF-IDF, Content-Based Filtering, Collaborative Filtering, Hybrid Recommender                   |    ✅   |
| 🤖 **Domain-Specific RAG Pipeline**            | Retrieval-Augmented Generation       | Generative AI              | BGE Embeddings, Milvus, Semantic Search, Hugging Face Transformers, Phi-3 Mini                 |    ✅   |
| 🧠 **MCP SQL Agent**                           | Agentic Text-to-SQL                  | Agentic AI / Generative AI | MCP, ReAct Agent, Tool Calling, GPT-OSS-20B, Groq, SQLite                                      |    ✅   |
| 🔧 **TinyLlama LoRA Instruction Tuning**       | Parameter-Efficient Fine-Tuning      | Generative AI / LLM        | LoRA, PEFT, SFT, TRL, TinyLlama, Dolly-15K                                                     |    ✅   |
| 🩺 **Self-Improving Appointment Agent**        | Agent Evaluation & Self-Improvement  | Agentic AI / Healthcare    | Multi-Turn Tool Use, LLM-as-Judge, Deterministic Checks, Failure-Driven Prompt Patching, Regression Gate, Gemini, Groq |    ✅   |

---

# Featured: Self-Improving Appointment Agent

A multi-turn patient-scheduling agent with tool use, an evaluation harness, and an improvement loop that learns from the agent's own failures:

```text
baseline eval → analyze failures → structured patch → new prompt/tool version → re-eval → regression gate → report
```

**Highlights (real runs, see the project README for full detail):**

- **Baseline v1 scored 0.786** on 14 main scenarios (N=3 runs each).
- The loop proposed **v2 (two prompt rules)**; under a reduced gate the three failing scenarios went **0/9 → 9/9**, and the 3 regression checks that ran passed (N=1).
- **The gate verdict is incomplete**: the run hit the agent's daily free-tier quota before the final checks, so v2 is neither accepted nor rejected. The README documents this and a known risk in v2's escalation wording openly, along with the exact next steps.
- **Two-layer scoring:** deterministic checks against the database and tool trace (what actually got booked or cancelled, identity verification, leaked data, false success claims) plus an LLM judge from a *different model family* than the agent.
- **Code-enforced guardrails** and two-phase writes, resumable runs, disk-cached LLM calls, and offline tests with fake LLMs.

📂 [`Self_Improving_Appointment_Agent/`](./Self_Improving_Appointment_Agent) — start with its `README.md`.

---

# Repository Structure

```text
AI-ML-Projects/
│
├── Ad_Targeting_Customer_Segmentation/
│   ├── README.md
│   ├── Notebook
│   └── Reports
│
├── Carbon_Emission_Prediction/
│   ├── README.md
│   ├── Notebook
│   └── Reports
│
├── Global_Development_Country_Segmentation/
│   ├── README.md
│   ├── Notebook
│   └── Reports
│
├── YouTube_Shorts_Engagement_Prediction/
│   ├── README.md
│   ├── Notebook
│   └── Reports
│
├── Ecommerce_Customer_Analytics/
│   ├── README.md
│   ├── Notebook
│   └── Reports
│
├── Amazon_Product_Recommendation_System/
│   ├── README.md
│   ├── Notebook
│   └── Dataset
│
├── Domain_Specific_RAG_Pipeline/
│   ├── README.md
│   └── Domain_Specific_RAG_Pipeline.ipynb
│
├── MCP-SQL-Agent/
│   ├── README.md
│   ├── data/
│   │   └── sample.db
│   ├── scripts/
│   │   └── setup_db.py
│   ├── src/
│   │   ├── agent.py
│   │   ├── mcp_client.py
│   │   └── mcp_server.py
│   ├── tests/
│   ├── pyproject.toml
│   └── uv.lock
│
├── TinyLlama_LoRA_Instruction_Tuning/
│   ├── README.md
│   ├── TinyLlama_LoRA_FineTuning.ipynb
│   └── TinyLlama_LoRA_FineTuning.pdf
│
├── Self_Improving_Appointment_Agent/
│   ├── README.md
│   ├── agent/          # tools (code-enforced guardrails), structured state, tool loop, CLI
│   ├── clinic/         # simulated backend: in-memory SQLite, fixed clock, fault injection
│   ├── evals/          # scenarios, simulated patient, deterministic checks, LLM judge, runner
│   ├── improve/        # failure analysis, validated patches, apply, regression gate, loop
│   ├── prompts/        # versioned system prompt and tool descriptions
│   ├── results/        # per-run JSON, summaries, before/after comparison
│   ├── scripts/        # smoke test
│   ├── tests/          # offline tests (fake LLMs)
│   ├── llm.py          # per-role client: cache, rate limiter, daily budget, retries
│   ├── AI_LOG.md       # decision log (AI vs human)
│   ├── requirements.txt
│   └── .env.example
│
├── .gitignore
└── README.md
```

---

# Core AI/ML Skills Covered

**Machine Learning:** Regression • Classification • Clustering • Recommendation Systems • Feature Engineering

**Deep Learning:** Autoencoders • Neural Networks • PyTorch • TensorFlow

**NLP & Generative AI:** Retrieval-Augmented Generation (RAG) • Dense Embeddings • Semantic Search • Vector Databases • Text-to-SQL • Large Language Models • Instruction Tuning • Supervised Fine-Tuning (SFT)

**RAG & Information Retrieval:** Document Ingestion • Text Chunking • Chunk Overlap • BGE Embeddings • Normalized Embeddings • Vector Similarity Search • Top-K Retrieval • Context Construction • Prompt Engineering • Grounded Generation

**LLM Fine-Tuning:** LoRA • Parameter-Efficient Fine-Tuning (PEFT) • TRL • Supervised Fine-Tuning (SFT) • Attention Projection Targeting • Gradient Checkpointing • Gradient Accumulation • Mixed-Precision Training • Adapter-Based Fine-Tuning

**Agentic AI:** Model Context Protocol (MCP) • ReAct Agents • Tool Calling • MCP Client/Server Architecture • MCP Tools • MCP Resources • MCP Prompts • LLM-Driven Database Interaction • Multi-Turn Tool-Use Agents • Code-Enforced Guardrails • Structured Agent State

**LLM Evaluation & Self-Improvement:** Scenario-Based Agent Evals • Simulated Users • Deterministic End-State Checks • LLM-as-Judge (cross-model-family) • Failure Analysis • Structured Prompt Patching • Overfitting Guards • Regression Gating • Held-Out Evaluation • Quota-Aware, Resumable Experiment Runs

**Data Science:** EDA • Statistical Analysis • Business Analytics • Data Preprocessing • Data Visualization

**MLOps & AI Tools:** Scikit-learn • TensorFlow • PyTorch • Hugging Face Transformers • Sentence Transformers • PEFT • TRL • Datasets • Milvus • FastMCP • Groq • Gemini • LangChain • Pandas • NumPy • pytest • uv

---

# Tech Stack

| Category            | Technologies                                                                                          |
| ------------------- | ----------------------------------------------------------------------------------------------------- |
| Programming         | Python                                                                                                |
| Data Analysis       | Pandas, NumPy                                                                                         |
| Machine Learning    | Scikit-Learn                                                                                          |
| Deep Learning       | PyTorch, TensorFlow, Keras                                                                            |
| NLP / LLM           | Hugging Face Transformers, Sentence Transformers, LangChain, TinyLlama, Microsoft Phi-3 Mini, GPT-OSS |
| Embedding Models    | BAAI/bge-small-en-v1.5                                                                                |
| RAG                 | Retrieval-Augmented Generation, Document Chunking, Semantic Retrieval, Context-Aware Prompting        |
| Vector Database     | Milvus                                                                                                |
| Vector Search       | Dense Embeddings, Vector Similarity Search, Top-K Retrieval, Normalized Embeddings                    |
| LLM Fine-Tuning     | LoRA, PEFT, TRL, Supervised Fine-Tuning (SFT)                                                         |
| Agentic AI          | Model Context Protocol (MCP), FastMCP, ReAct, LLM Tool Calling                                        |
| Agent Evaluation    | Custom eval harness, LLM-as-Judge, deterministic checks, regression gate, pytest                      |
| LLM Inference       | Hugging Face Transformers, Groq, Gemini (OpenAI-compatible client)                                    |
| Relational Database | SQLite                                                                                                |
| Visualization       | Matplotlib, Seaborn                                                                                   |
| GPU / Acceleration  | CUDA, PyTorch, Hugging Face Accelerate, Mixed Precision (FP16/BF16)                                   |
| Development         | Jupyter Notebook, Google Colab, VS Code, Git, GitHub, uv                                              |

---

# Project Workflow

The analytics and ML projects follow a structured workflow:

```
Business Problem
        │
        ▼
Data Collection
        │
        ▼
Data Cleaning
        │
        ▼
Exploratory Data Analysis
        │
        ▼
Feature Engineering
        │
        ▼
Model Development
        │
        ▼
Model Evaluation
        │
        ▼
Business Insights
        │
        ▼
Recommendations
```

The agentic and LLM-evaluation projects follow an iterate-and-measure workflow:

```
Define Scenarios & Guardrails
        │
        ▼
Build Agent + Simulated Environment
        │
        ▼
Baseline Evaluation (deterministic checks + judge)
        │
        ▼
Failure Analysis → Structured Patch
        │
        ▼
Re-Evaluation → Regression Gate
        │
        ▼
Report & Limitations
```

---

# Current Focus

I'm currently expanding this repository with projects in:

- Large Language Models (LLMs)
- Agentic AI
- Retrieval-Augmented Generation (Advanced RAG)
- LLM & Agent Evaluation
- Computer Vision
- MLOps
- Deep Learning
- Time Series Forecasting
- Recommendation Systems
- Generative AI Applications

---

# About Me

I'm a **Software Engineer** with experience in **Java Backend Development** and **Artificial Intelligence**, passionate about building intelligent systems that solve real-world business problems.

### Areas of Interest

- Artificial Intelligence
- Machine Learning
- Deep Learning
- Generative AI
- Large Language Models (LLMs)
- Retrieval-Augmented Generation (RAG)
- Natural Language Processing
- MLOps

---

# Connect With Me

- 💼 **LinkedIn:** https://www.linkedin.com/in/koushik-jayanthi-2b86b5153/
- 💻 **GitHub:** https://github.com/Koushik999999
- 📧 **Email:** koushikjayanthi99@gmail.com

---

## ⭐ If you find this repository useful, consider giving it a Star!