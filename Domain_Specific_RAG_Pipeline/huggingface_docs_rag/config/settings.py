import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# API Tokens
HF_TOKEN = os.getenv("HF_TOKEN")
OPIK_API_KEY = os.getenv("OPIK_API_KEY")

# Data & Chunking Config
DATASET_NAME = "m-ric/huggingface_doc"
MAX_DOCS = 500
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Vector Store Config
# BASE_DIR is the root of rag_production
# Points to the existing hf_docs_milvus.db located one level up
MILVUS_DB_PATH = os.getenv("MILVUS_DB_PATH", str(BASE_DIR.parent / "hf_docs_milvus.db"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "hf_documentation")
EMBEDDING_DIM = 384

# Model Names
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
LLM_MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

# Prompts
PROMPT_TEMPLATE = """Use the following pieces of information enclosed in <context> tags to provide an answer to the question enclosed in <question> tags.
If the context doesn't contain enough information to answer the question, say "I don't have enough information to answer this question."

<context>
{context}
</context>

<question>
{question}
</question>

Answer:"""