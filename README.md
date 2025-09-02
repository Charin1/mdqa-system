# MDQA-System: Your Personal Document Intelligence Engine

![status](https://img.shields.io/badge/status-in_development-yellow)

⚠️ This project is under active development and is **not production-ready**.

MDQA-System is a powerful, **private**, and intelligent platform that transforms your personal or professional documents into a searchable knowledge base. Upload your PDFs, DOCX files, and text documents, and ask complex questions in natural language to get synthesized, accurate answers based solely on the provided content.

This project is built with a modern, robust stack featuring a FastAPI backend and a React frontend. It leverages a sophisticated, local-first RAG (Retrieval-Augmented Generation) pipeline, ensuring your data remains completely private and secure on your own machine.

![MDQA-System Screenshot](./docs/images/chat.png) 


---

## Table of Contents
- [Features](#features)
- [How It Works: The RAG Pipeline](#how-it-works-the-rag-pipeline)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Setup Instructions](#setup-instructions)
- [Tuning for Performance & Quality](#tuning-for-performance--quality)
- [Project Roadmap: Future Improvements](#project-roadmap-future-improvements)
- [Contributing](#contributing)

---

## Features

*   **Universal Document Support:** Ingest knowledge from `.pdf` (including scanned documents via OCR), `.docx`, `.txt`, and `.md`.
*   **100% Private and Offline:** All data processing and AI inference happens locally. Your documents are never sent to any third-party service.
*   **State-of-the-Art RAG Pipeline:**
    *   **Robust Chunking:** Uses a recursive character splitter to safely and effectively chunk any document, regardless of formatting.
    *   **Top-Tier Embedding:** Employs the powerful `BAAI/bge-m3` model to create nuanced, high-quality vector representations of your text.
    *   **Advanced Hybrid Search:** Combines keyword search (BM25) and semantic search, then fuses the results using Reciprocal Rank Fusion (RRF).
    *   **High-Precision Re-ranking:** Employs a `Cross-Encoder` model to re-rank the initial search results, ensuring only the most relevant context is passed to the LLM for superior accuracy.
    *   **High-Quality Generative Answers:** Powered by the **Meta-Llama-3-8B-Instruct** model, providing synthesized, coherent answers instead of just extracting text.
*   **Universal Hardware Support:** The AI model is loaded via `ctransformers` (llama.cpp), which automatically detects and utilizes the best available hardware (NVIDIA CUDA, Apple Metal GPU, or CPU) on any platform (Windows, macOS, Linux).
*   **Intuitive User Interface:**
    *   A clean, modern, dark-themed UI built with React and Tailwind CSS.
    *   **Persistent Chat Sessions:** Your conversation history is preserved as you navigate the application, thanks to a global state manager (Zustand).
    *   **Interactive Source Highlighting:** Clickable source citations below each answer navigate you to the exact chunk in the original document and highlight it, providing instant verifiability.
    *   **Document Library & Chunk Inspector:** Manage your documents and verify their processing by inspecting the individual text chunks.
*   **System Analytics:** A dashboard to monitor system usage and performance.

## How It Works: The RAG Pipeline

1.  **Ingest:** A document is parsed, and text is extracted (with OCR as a fallback).
2.  **Chunk:** The text is divided into small, overlapping, and highly focused chunks.
3.  **Embed:** Each chunk is converted into a vector using the `bge-m3` model.
4.  **Index:** The chunks and their vectors are stored in a local ChromaDB database.
5.  **Retrieve:** When you ask a question, the system performs a fast hybrid search to find an initial set of ~25 potentially relevant chunks.
6.  **Re-rank:** A Cross-Encoder model carefully reads the query and each of the 25 chunks, re-scoring them for accuracy. The top 5-7 chunks are selected.
7.  **Synthesize:** The question and the highly relevant, re-ranked chunks are formatted into a specific prompt and sent to the **Llama 3** model, which generates a brand new, accurate answer.

## Tech Stack

| Component | Technology |
| :--- | :--- |
| **Backend** | Python, FastAPI, SQLModel |
| **Frontend** | React, TypeScript, Vite, Tailwind CSS, Zustand |
| **Vector Database** | ChromaDB (Embedded) |
| **Metadata Database**| SQLite |
| **Embedding Model** | `BAAI/bge-m3` |
| **Re-ranking Model** | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| **Generation Model** | `Meta-Llama-3-8B-Instruct` (via `ctransformers`) |

## Getting Started

### Prerequisites
*   [Python 3.11+](https://www.python.org/downloads/)
*   [Node.js](https://nodejs.org/) (LTS version)
*   A C++ compiler (required for `ctransformers` installation).
    *   **macOS:** Install Xcode Command Line Tools: `xcode-select --install`
    *   **Ubuntu:** `sudo apt-get install build-essential`
    *   **Windows:** Install Visual Studio with the "Desktop development with C++" workload.

### Setup Instructions

This guide is for running the system locally without Docker.

1.  **Clone the repository and navigate into the `backend` directory.**
2.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
3.  **Install backend dependencies:**
    This may take several minutes, especially `ctransformers`.
    ```bash
    pip install -r requirements.txt
    ```
    *   **For Apple Silicon Macs:** To enable GPU acceleration, you must reinstall `ctransformers` with the Metal flag:
        ```bash
        pip uninstall ctransformers --yes
        CT_METAL=1 pip install ctransformers --no-binary ctransformers
        ```
4.  **Set up your Hugging Face token:**
    *   Create a `.env` file in the `backend` directory: `cp .env.local .env`
    *   Edit `backend/.env` and add your Hugging Face token. This is required to download the Llama 3 tokenizer.
        ```dotenv
        HF_TOKEN=hf_YourHuggingFaceTokenGoesHere
        ```
5.  **Start the backend server (in your first terminal):**
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```
    The first time you ask a question, the system will download the Llama 3 model (~5.5 GB). This is a one-time process.

6.  **Setup and run the frontend (in a new, separate terminal):**
    ```bash
    cd ../frontend
    npm install
    npm run dev
    ```
7.  **Access the application** in your browser at `http://localhost:5173`.

---

## Tuning for Performance & Quality

The quality of a RAG system depends on several key parameters. The current settings provide a strong, high-quality baseline, but can be tuned.

*   **For Demo Purposes:** The current settings (`chunk_size=256`, `Llama-3-8B`, `bge-m3` embedding, and a Cross-Encoder) are optimized for high-quality results on modern consumer hardware.
*   **For Higher Quality:** To improve results further, you could use a larger generation model (like a 70B parameter model, if you have the hardware) or fine-tune the embedding model on your specific document domain.
*   **For Higher Speed:** To improve performance on older hardware, you could switch to a smaller generation model (like `Llama-3-8B` without the `Instruct` tuning, or a smaller `Mistral` model) and a smaller embedding model (like `bge-small-en-v1.5`).

Key files for tuning:
*   `backend/app/core/settings.py`: For `DEFAULT_CHUNK_SIZE` and `DEFAULT_CHUNK_OVERLAP`.
*   `backend/app/rag/retrieve.py`: For the embedding model (`get_embedding_model`) and re-ranking model (`get_reranker_model`).
*   `backend/app/rag/answer.py`: For the generation model (`get_llama_llm`).

## Project Roadmap: Future Improvements

This project is a powerful foundation. Here are some potential next steps:

*   **Pluggable Models:**
    *   **Generation:** Abstract the `answer.py` logic to easily switch between different GGUF models (e.g., `Mistral`, `Qwen`) or even different model loaders (like an Ollama client) via a config setting.
    *   **Embedding:** Allow the embedding model to be configured via the `.env` file.
*   **Advanced RAG Techniques:**
    *   **Query Transformations:** Implement techniques like HyDE (Hypothetical Document Embeddings) to improve retrieval for complex questions by having an LLM rewrite the user's query before searching.
*   **Production & UX:**
    *   **Streaming Responses:** Modify the API to stream the LLM's response token by token for a more interactive, ChatGPT-like feel.
    *   **Web Page Ingestion:** Add the ability to ingest knowledge directly from a URL.
    *   **User Authentication:** Add a login system for multi-user support with private document libraries.

## Contributing

Contributions are welcome! Please feel free to fork the repository, make your changes, and submit a pull request.