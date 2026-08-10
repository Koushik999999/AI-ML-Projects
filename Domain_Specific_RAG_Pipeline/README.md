# 🚀 Domain-Specific RAG Pipeline

An end-to-end **Retrieval-Augmented Generation (RAG)** pipeline for building domain-specific AI applications using dense semantic embeddings, Milvus vector search, and a local Microsoft Phi-3 Mini language model.

The project demonstrates how unstructured domain-specific documents can be transformed into searchable knowledge, retrieved using semantic similarity, and provided as context to an LLM for grounded answer generation.

---

## 🚀 Key Features

* End-to-end Retrieval-Augmented Generation pipeline
* Domain-specific document ingestion
* Configurable text chunking and overlap
* Dense semantic embeddings using BGE
* Vector similarity search using Milvus
* Top-K relevant document retrieval
* Context-aware prompt construction
* Local LLM-based generation using Microsoft Phi-3 Mini
* Normalized embeddings for similarity search
* Modular retrieval and generation components
* Python-based implementation suitable for experimentation and portfolio demonstration

---

## 🧠 Technologies Used

| Component            | Technology                         |
| -------------------- | ---------------------------------- |
| Programming Language | Python                             |
| Embedding Model      | `BAAI/bge-small-en-v1.5`           |
| Embedding Dimension  | 384                                |
| Vector Database      | Milvus                             |
| LLM                  | `microsoft/Phi-3-mini-4k-instruct` |
| LLM Framework        | Hugging Face Transformers          |
| Embedding Framework  | Sentence Transformers              |
| Model Execution      | PyTorch                            |
| Acceleration         | Hugging Face Accelerate            |
| Environment          | Jupyter Notebook / Python 3.10     |

---

# 🔄 RAG Pipeline

The complete pipeline consists of two major stages:

1. **Offline / Indexing Pipeline** – prepares and stores the domain knowledge.
2. **Online / Query Pipeline** – retrieves relevant knowledge and generates an answer.

---

## 1. 📄 Document Ingestion

Domain-specific documents are loaded into the pipeline and prepared for downstream processing.

The objective is to transform unstructured documents into searchable knowledge units.

```text
Documents
    ↓
Text Extraction
    ↓
Cleaning / Normalization
    ↓
Chunking
```

---

## 2. ✂️ Text Chunking

Large documents are divided into smaller overlapping chunks.

Current configuration:

```text
Chunk Size:    1000
Chunk Overlap: 150
```

The overlap helps preserve contextual continuity between neighboring chunks.

Conceptually:

```text
Chunk 1
[------------------------------]

                 overlap

          [------------------------------]
          Chunk 2
```

Chunking is important because embedding entire documents can reduce retrieval precision and may exceed the useful context size of the downstream LLM.

---

## 3. 🧮 Embedding Generation

Each text chunk is converted into a dense vector representation using:

```text
BAAI/bge-small-en-v1.5
```

The model produces:

```text
384-dimensional embeddings
```

Embeddings are generated with normalization enabled:

```python
embedding_model.encode(
    texts,
    normalize_embeddings=True
)
```

Normalized embeddings allow the resulting vectors to be efficiently compared using vector similarity metrics.

---

## 4. 🗄️ Vector Storage

The generated embeddings and their corresponding document metadata are stored in **Milvus**.

Conceptually, each stored record contains:

```text
┌────────────────────────────────────┐
│ ID                                 │
├────────────────────────────────────┤
│ Document / Chunk Text              │
├────────────────────────────────────┤
│ Metadata                           │
├────────────────────────────────────┤
│ 384-dimensional Embedding Vector   │
└────────────────────────────────────┘
```

Milvus provides efficient vector similarity search over the indexed embeddings.

---

## 5. 🔎 Query Processing

When a user asks a question, the query goes through the same embedding model:

```text
User Question
      ↓
BGE Encoder
      ↓
384-dimensional Query Vector
```

The resulting query vector is then compared against the vectors stored in Milvus.

---

## 6. 🎯 Semantic Retrieval

Milvus retrieves the most semantically similar document chunks.

Instead of relying only on exact keyword matching, semantic retrieval allows the system to identify documents that are conceptually related to the question.

```text
User Query
     │
     ▼
Query Embedding
     │
     ▼
Vector Similarity Search
     │
     ▼
Top-K Relevant Chunks
```

The retrieved information becomes the context provided to the LLM.

---

## 7. 🧩 Context Construction

The retrieved documents are combined into a single context:

```python
context = "\n\n".join(
    doc["text"] for doc in retrieved_docs
)
```

This creates the knowledge context that will be provided to the language model.

---

## 8. 📝 Prompt Construction

The retrieved context and user question are inserted into a predefined prompt template.

Conceptually:

```text
Context:
-------------------------
Retrieved document 1

Retrieved document 2

Retrieved document 3
-------------------------

Question:
<user question>

Answer:
```

This follows the core RAG principle:

> **Retrieve relevant external knowledge first, then condition the LLM generation on that knowledge.**

---

## 9. 🤖 LLM Generation

The final prompt is passed to:

```text
microsoft/Phi-3-mini-4k-instruct
```

Example generation parameters:

```text
max_new_tokens = 256
temperature    = 0.7
top_p          = 0.9
do_sample      = True
```

The model generates an answer using the retrieved context.

---

# 🧩 Generation Function

The core generation component follows the RAG pattern:

```python
def generate_answer(
    query: str,
    retrieved_docs: List[Dict],
    generator: pipeline,
    max_new_tokens: int = 256
) -> Dict:

    context = "\n\n".join(
        doc["text"] for doc in retrieved_docs
    )

    prompt = PROMPT_TEMPLATE.format(
        context=context,
        question=query
    )

    outputs = generator(
        prompt,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        return_full_text=False
    )

    answer = outputs[0]["generated_text"].strip()

    return {
        "query": query,
        "answer": answer,
        "context": context,
        "retrieved_docs": retrieved_docs
    }
```

The function returns:

```text
query
answer
context
retrieved_docs
```

This makes the complete RAG result inspectable rather than returning only the generated answer.

---

# 🏗️ System Architecture

The project can be viewed as two major pipelines.

## Offline / Indexing Pipeline

```text
Domain Documents
       ↓
Document Parsing
       ↓
Text Cleaning
       ↓
Chunking
       ↓
BGE Embeddings
       ↓
Milvus
       ↓
Vector Index
```

This pipeline prepares the knowledge base.

---

## Online / Query Pipeline

```text
User Query
     ↓
Query Embedding
     ↓
Milvus Similarity Search
     ↓
Top-K Documents
     ↓
Context Construction
     ↓
Prompt Template
     ↓
Phi-3 Mini
     ↓
Generated Answer
```

---

# 📊 Retrieval vs Generation

One of the main design principles of this project is separating **retrieval** from **generation**.

## Retrieval

Responsible for answering:

> **"Which information should the LLM see?"**

Components:

```text
BGE Embeddings
      +
Milvus
      ↓
Relevant Context
```

---

## Generation

Responsible for answering:

> **"How should the retrieved information be used to answer the question?"**

Components:

```text
Retrieved Context
      +
User Question
      ↓
Prompt
      ↓
Phi-3 Mini
      ↓
Answer
```

This separation makes the system modular and allows the embedding model, vector database, retriever, and LLM to be changed independently.

---

# ⚙️ Configuration

Example configuration:

```python
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

LLM_MODEL = "microsoft/Phi-3-mini-4k-instruct"

CHUNK_SIZE = 1000

CHUNK_OVERLAP = 150

MAX_NEW_TOKENS = 256
```
---

# 🧪 Example Workflow

```python
query = "What is the main purpose of this technology?"

retrieved_docs = retrieve_documents(
    query,
    top_k=5
)

result = generate_answer(
    query=query,
    retrieved_docs=retrieved_docs,
    generator=generator
)

print(result["answer"])
```

The final response is generated using information retrieved from the domain-specific knowledge base.

---

# 🔍 Why RAG?

A standard LLM follows a simple architecture:

```text
Question
   ↓
LLM
   ↓
Answer
```

The answer may be based primarily on the model's pretrained knowledge.

A RAG system instead follows:

```text
Question
   ↓
Retriever
   ↓
Relevant Knowledge
   ↓
LLM
   ↓
Grounded Answer
```

This provides several advantages:

* Access to private or domain-specific information
* Ability to update the knowledge base without retraining the LLM
* Better grounding of generated responses
* Reduced dependence on the LLM's parametric knowledge
* Traceability through retrieved source chunks

---

# ⚠️ Limitations

This implementation is primarily designed as an educational and portfolio project.

Potential limitations include:

* Retrieval quality depends heavily on the chunking strategy.
* Poorly retrieved documents can lead to poor answers.
* The LLM can still generate information that is not explicitly supported by the retrieved context.
* Context-window limits restrict the amount of retrieved information that can be passed to the LLM.
* The current pipeline does not implement a dedicated reranking stage.
* Evaluation metrics such as Recall@K, MRR, faithfulness, and answer relevance can be added for more rigorous evaluation.
* Production deployments would require additional monitoring, caching, security, and scalability considerations.

---

# 🚧 Future Improvements

## Retrieval Improvements

Potential retrieval enhancements include:

* Hybrid search combining keyword and vector retrieval
* Cross-encoder reranking
* Metadata filtering
* Query expansion
* Multi-query retrieval
* Parent-child document retrieval

---

## Generation Improvements

Potential generation enhancements include:

* Structured output
* Citation-aware generation
* Improved prompt engineering
* Hallucination detection
* Answer confidence estimation

---

## 📊 Evaluation

Automated RAG evaluation can be added using metrics such as:

```text
Recall@K
Precision@K
MRR
Context Relevance
Context Recall
Answer Relevance
Faithfulness
```

These metrics can help evaluate both retrieval quality and final answer quality.

---

# 🚀 Productionization

A potential production architecture could look like:

```text
             ┌───────────────┐
             │    API Layer  │
             └───────┬───────┘
                     │
                     ▼
             ┌───────────────┐
             │ RAG Service   │
             └───────┬───────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   ┌──────────────┐      ┌──────────────┐
   │   Retriever  │      │     LLM      │
   └──────┬───────┘      └──────────────┘
          │
          ▼
   ┌──────────────┐
   │    Milvus    │
   └──────────────┘
```

Additional infrastructure could include:

* FastAPI
* Docker
* Redis
* Kubernetes
* Observability
* Batch ingestion pipelines
* GPU inference serving

---

# 🎯 Learning Objectives

This project demonstrates practical understanding of:

* Retrieval-Augmented Generation
* Transformer-based language models
* Dense vector embeddings
* Semantic search
* Vector databases
* Document chunking
* Prompt engineering
* LLM inference
* Hugging Face Transformers
* Sentence Transformers
* Milvus
* PyTorch
* RAG pipeline architecture

---

# 📚 Key Takeaways

The core idea behind this project is:

```text
RAG = Retrieval + Context + Generation
```

The LLM does not need to memorize the entire domain-specific knowledge base.

Instead:

```text
Knowledge Base
      ↓
Vector Database
      ↓
Relevant Information
      ↓
LLM Context
      ↓
Grounded Generation
```

This architecture provides a flexible foundation for building domain-specific AI assistants and knowledge-based LLM applications.

---

# ⭐ Project Summary

This project implements a complete **domain-specific Retrieval-Augmented Generation pipeline** using:

```text
Python
   +
BGE Embeddings
   +
Milvus
   +
Hugging Face Transformers
   +
Microsoft Phi-3 Mini
```

The system demonstrates the complete journey from **document ingestion → chunking → embedding → vector storage → semantic retrieval → context construction → LLM generation**.

It serves as a practical foundation for understanding how modern RAG systems are designed and provides a starting point for extending the project toward production-grade AI applications.

```

You can paste the block directly into your repository's `README.md`.
```
