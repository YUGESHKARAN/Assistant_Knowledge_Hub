# Tech Community Assistant (RAG-based AI Assistant)

A production-grade AI assistant built for a technical community learning platform. This repository implements a Retrieval-Augmented Generation (RAG) architecture with two core pipelines:

- Ingestion pipeline: receives posts/content, converts them into vector embeddings using OpenAI's `text-embedding-3-small` model (dimension: 521), and stores the embeddings with metadata in Pinecone.
- Query pipeline: converts user questions into embeddings, performs similarity search against the Pinecone index to retrieve top-k context chunks, then uses the retrieved context + role-specified prompts to generate a structured JSON response from an LLM.

This README documents architecture, environment variables, running locally, API examples, and operational recommendations.

## Table of contents
- [Architecture](#architecture)
- [Repository layout](#repository-layout)
- [Getting started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment variables](#environment-variables)
  - [Install](#install)
  - [Run locally](#run-locally)
- [Pipelines](#pipelines)
  - [Ingestion pipeline](#ingestion-pipeline)
  - [Query pipeline](#query-pipeline)
- [API examples](#api-examples)
- [Embedding & index details](#embedding--index-details)
- [Prompting & response schema](#prompting--response-schema)
- [Production considerations](#production-considerations)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Architecture
- Client -> API (Flask/FastAPI or similar - check `app.py`)  
- Ingestion: `ingestion.py` -> embed text with OpenAI -> store in Pinecone via `pinecone_client.py`  
- Retrieval: `retrieval.py` / `retrieval pipeline` -> embed user query -> similarity search in Pinecone -> assemble top-k chunks -> call LLM with role prompts from `prompt.py` -> JSON response  
- Utilities: configuration, schema, and embedding helpers in `utility/` (see layout below).

## Repository layout
Based on the project files:
- utility/
  - config.py — configuration and environment helpers
  - prompt.py — prompt templates and role-based prompts
  - schema.py — data schemas for ingestion and responses
  - embeder.py (or embedder.py) — wrapper around OpenAI embeddings
  - ingestion.py — ingestion pipeline implementation
  - pinecone_client.py — Pinecone client and index helpers
  - retrieval.py — retrieval / query pipeline
  - app.py — API server (endpoints for ingest/query)
  - requirements.txt
  - .env — local environment variables (not committed)
- .gitignore

Adjust filenames above if your repository uses slightly different names (e.g., `embedder.py` vs `embeder.py`).

## Getting started

### Prerequisites
- Python 3.9+
- An OpenAI API key (with access to `text-embedding-3-small` and the LLM model you use)
- A Pinecone account, API key, environment and an index created (vector dimension 521)
- (Optional) Virtualenv or poetry for dependency isolation

### Environment variables
Create a `.env` file in the project root or set these in your environment:

- OPENAI_API_KEY — OpenAI API key
- OPENAI_API_BASE — (optional, if using a custom OpenAI endpoint)
- PINECONE_API_KEY — Pinecone API key
- PINECONE_ENVIRONMENT — Pinecone environment/region
- PINECONE_INDEX_NAME — The index name used for storing vectors
- EMBEDDING_MODEL — e.g., `text-embedding-3-small` (default)
- EMBEDDING_DIM — `521` (important: index must match this)
- LLM_MODEL — the LLM model used for generation (e.g., `gpt-4o-mini` or other)
- SERVICE_ROLE or ROLE_NAME — (optional) if you use role-based prompting logic

Example `.env`:
```
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=pc-...
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=tech-community-index
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=521
LLM_MODEL=gpt-4o-mini
```

### Install
Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r utility/requirements.txt
```

(Adjust path if `requirements.txt` is in project root.)

### Run locally
Start the API server (example, adjust if you use FastAPI or Flask):

```bash
python utility/app.py
```

Check `app.py` for the actual entrypoint and any CLI flags.

## Pipelines

### Ingestion pipeline
High-level steps:
1. Receive content (e.g., post body, title, author, url, created_at).
2. Preprocess and chunk text (if needed).
3. Use OpenAI embeddings: `text-embedding-3-small` to create vector embedding (dim 521).
4. Store vectors in Pinecone index with metadata: e.g., `source`, `title`, `author`, `created_at`, `chunk_id`, `doc_id`, and any tags.

Recommended metadata keys:
- source (string)
- doc_id (string)
- chunk_id (string)
- title (string)
- author (string)
- created_at (ISO timestamp)
- url (optional)
- lang (optional)

Batch writes for higher throughput and lower cost. Ensure your Pinecone index vector dimension equals `EMBEDDING_DIM=521`.

### Query pipeline
High-level steps:
1. Receive user question and optional role/context settings.
2. Convert question into embedding using same embedding model.
3. Query Pinecone for top-k similar vectors (e.g., k=5 or k=10).
4. Aggregate the retrieved chunks into a context prompt.
5. Use role-specific prompt templates from `prompt.py` to instruct the LLM to respond in JSON format.
6. Return the LLM-generated JSON response to the caller.

Use retrieval-augmented prompts that include explicit instructions about output schema to keep responses structured.

## API examples

Below are suggested endpoints. Confirm names in `app.py` and update if different.

- POST /ingest
  - Request JSON (example):
    ```json
    {
      "doc_id": "post-123",
      "title": "How to use the new router",
      "author": "alice",
      "content": "Full post text...",
      "created_at": "2026-01-10T10:00:00Z",
      "url": "https://community.example/posts/123"
    }
    ```
  - Response: status, inserted vector ids, or an ingestion job id.

- POST /query
  - Request JSON (example):
    ```json
    {
      "question": "How do I set up the router middleware?",
      "top_k": 5,
      "role": "mentor"
    }
    ```
  - Response: JSON produced by the LLM. Example structure:
    ```json
    {
      "answer": "Step-by-step guidance ...",
      "sources": [
        {"doc_id": "post-123", "chunk_id": "c1", "score": 0.92},
        {"doc_id": "post-98", "chunk_id": "c2", "score": 0.87}
      ],
      "metadata": {
        "model": "gpt-4o-mini",
        "embedding_model": "text-embedding-3-small"
      }
    }
    ```

Curl example (replace host and port):
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is RAG and how is it used here?","top_k":5}'
```

## Embedding & index details
- Embedding model: text-embedding-3-small
- Vector dimension: 521 (IMPORTANT: Pinecone index must be created with this dimension)
- Similarity metric: cosine (recommended), or dot-product depending on tuning
- Upsert in batches (e.g., 100–1000 vectors per request depending on payload size)
- Keep consistent normalization/use of the same embedding model for ingestion and queries

## Prompting & response schema
- Use `prompt.py` to centralize role-specific templates and output-schema enforcement.
- Prefer few-shot examples in prompts to make LLM responses consistent and JSON-valid.
- Always instruct the LLM to respond with strict JSON (no extra commentary) so downstream systems can parse reliably.

Suggested prompt pattern:
- System instruction: role & behavior (e.g., "You are a concise mentor for developers. Output only JSON matching schema X.")
- Context: concatenated retrieved chunks (clearly labeled and trimmed to token limits)
- User instruction: the question and required response format (fields, types)

## Production considerations
- Rate limiting and retries for OpenAI and Pinecone API calls
- Caching frequent queries / responses
- Monitor embedding and similarity drift after model updates
- Secure your keys using secret manager (do not store in repo)
- Ensure the Pinecone index dimension matches embedding output (mismatches will cause errors)
- Use incremental ingestion with idempotency (upsert by doc_id + chunk_id)
- Audit logs for queries and responses for moderation and analytics
- Token / prompt length constraints — truncate or prioritize retrieved chunks to fit the LLM context window
- Consider using a batching/worker queue for ingestion (Celery / RQ / background worker)
- Implement content moderation / safe-filtering if user-supplied content may be harmful

## Troubleshooting
- "Dimension mismatch" errors: Verify `EMBEDDING_DIM` and Pinecone index dimension are the same.
- Empty or poor results: increase top_k, check embedding model is the same for queries and ingestion, and inspect metadata stored with vectors.
- API key errors: confirm env vars and network egress to OpenAI and Pinecone endpoints.
- Cost: embedding every token is expensive—use chunking, deduplication, and selective ingestion.

## Contributing
Contributions are welcome. Please:
1. Open an issue describing the change or problem.
2. Create a feature branch.
3. Submit a pull request with tests and documentation updates.

## License
Add your preferred license here (e.g., MIT). If you don't have one yet, consider `MIT` for permissive use.

---

If you want, I can:
- open a PR adding this README to the repo,
- tailor the README to exactly match the endpoints and field names found in `app.py` and other files (I can read those files next),
- add a deployment section with an example Dockerfile and Kubernetes manifest.

Tell me which you'd like me to do next.
