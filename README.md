# Tech Community Assistant — Production-grade RAG Assistant

A production-grade AI assistant built for a technical community learning platform. This project implements a Retrieval-Augmented Generation (RAG) architecture with separate ingestion and query pipelines:

- Ingestion pipeline: ingests user posts, converts them to vector embeddings using OpenAI's `text-embedding-3-small` (dim: 521), and stores vectors + metadata in a Pinecone index.
- Query pipeline: converts user questions to embeddings, performs similarity search against Pinecone to retrieve top-k relevant chunks, and uses those chunks as context (plus role-specified prompts) to generate a JSON response via an LLM.

This repository contains the core utilities for embedding, Pinecone integration, ingestion, retrieval, prompt templates and a minimal app interface.

Contents
- Brief overview (quickstart)
- Detailed architecture & flow
- Running locally (install, env, commands)
- Pipelines (ingest & query) — implementation notes
- Request / response schema & examples
- Production notes, observability & security
- Contributing & license

---

## Brief (Quickstart)

1. Create a `.env` file with your OpenAI and Pinecone credentials (see “Environment variables”).
2. Install dependencies:
   - pip install -r utility/requirements.txt
3. Start the app or run the scripts:
   - Check `app.py` for HTTP endpoints (ingest / query) or run `utility/ingestion.py` to ingest data and `utility/retrieval.py` to test queries.
4. Ingestion converts posts into 521-dimensional vectors using `text-embedding-3-small` and stores them in Pinecone along with metadata.
5. Querying converts the question to an embedding, does a top-k similarity search in Pinecone, retrieves chunks, and asks the LLM to generate a JSON response with content, suggested posts, and suggestions.

---

## Architecture & Data Flow (Detailed)

1. Data Ingestion
   - Source: community posts (title, body, images, links, author, category, postId, profile, etc.).
   - Text is chunked / normalized (see `schema.py` / `prompt.py` for structure).
   - Embedding: `utility/embedder.py` calls OpenAI’s `text-embedding-3-small` (embedding dim = 521).
   - Storage: `utility/pinecone_client.py` upserts embeddings with metadata into a Pinecone index (index config and namespace are set via env vars).

2. Query / Retrieval
   - Input: user question (and optional `current_post_id` or other filters).
   - Query embedding: same `text-embedding-3-small`.
   - Similarity search: Pinecone similarity search returns top-k matching chunks.
   - LLM prompt: Constructed using retrieved context + role and templates in `utility/prompt.py`.
   - LLM response: LLM generates a structured JSON (see schema below). The response is returned to the user.

ASCII overview:

User Post(s) --> Ingestion (chunk -> embed -> Pinecone) <---> Pinecone Index
                                                          ^
                                                          |
User Query --> Embed --> Pinecone similarity search --> Retrieve top-k chunks --> Build prompt (context + role) --> LLM -> JSON response

---

## Environment variables

Create a `.env` file with at least the following keys:

- OPENAI_API_KEY=your_openai_key
- OPENAI_EMBED_MODEL=text-embedding-3-small
- EMBEDDING_DIM=521
- PINECONE_API_KEY=your_pinecone_key
- PINECONE_ENV=your-pinecone-environment (e.g., us-west1-gcp)
- PINECONE_INDEX=your_index_name
- PINECONE_NAMESPACE=optional_namespace
- OPTIONAL: OPENAI_API_BASE, OPENAI_API_TYPE, etc. if using a proxy/enterprise deployment

Note: The repo includes a `.env` template place; inspect `utility/config.py` for exact environment variable names expected by the code.

---

## Install & Run

1. Clone the repository:
   ```
   git clone https://github.com/YUGESHKARAN/Assistant_Knowledge_Hub.git
   cd Assistant_Knowledge_Hub
   ```

2. Install dependencies:
   ```
   pip install -r utility/requirements.txt
   ```

3. Configure `.env` (at repo root or as expected by the code). Example:
   ```
   OPENAI_API_KEY=sk-...
   PINECONE_API_KEY=pc-...
   PINECONE_ENV=us-west1-gcp
   PINECONE_INDEX=assistant-index
   PINECONE_NAMESPACE=community
   OPENAI_EMBED_MODEL=text-embedding-3-small
   EMBEDDING_DIM=521
   ```

4. Ingest data (example):
   - There is a script `utility/ingestion.py` which performs ingestion; run it to index posts:
     ```
     python utility/ingestion.py
     ```
   - The script will read posts (from your source), embed them with `utility/embedder.py` and upsert into Pinecone via `utility/pinecone_client.py`.

5. Query / Run server:
   - `app.py` exposes a minimal HTTP interface. Inspect `app.py` for routes. Typical flow:
     - POST /query  (body: {"query": "...", "current_post_id": "..."})
     - POST /ingest (to ingest individual posts via HTTP) — if implemented
   - Example (assumes a `/query` endpoint — confirm by reading `app.py`):
     ```
     curl -X POST http://localhost:8000/query \
       -H "Content-Type: application/json" \
       -d '{"query":"summarize it, suggest post content", "current_post_id":"689c1079f0093cfba6c981d5"}'
     ```

---

## Important files / modules

- utility/config.py — environment & configuration
- utility/embedder.py — OpenAI embedding calls
- utility/pinecone_client.py — Pinecone index client, upsert, query helpers
- utility/ingestion.py — ingestion pipeline runner
- utility/retrieval.py — query pipeline, retrieval + LLM prompting flow
- utility/prompt.py — prompt templates and role-based prompt builders
- utility/schema.py — expected data schema and types
- app.py — application entry / HTTP API handlers
- requirements: utility/requirements.txt

---

## Request / Response Schema

The system produces a JSON response designed for clients that render posts, suggestions, and optional videos. Example response:

Example (sample response produced by the LLM):
```json
{
  "content": "## Evaluating LLMs using LangSmith\n\nJust wrapped up a comprehensive evaluation ...",
  "posts": [
    {
      "authorEmail": "yugeshkaran01@gmail.com",
      "authorName": "Yugesh Karan",
      "category": "GenAI",
      "image": "IMG-20250317-WA0008.jpg",
      "links": [
        {"title":"new links 2: test h", "url":"new links 2: test h"},
        {"title":"YouTube: https://youtu.be/_ZvnD73m40o?si=6pbeG2cBhblMB89M", "url":"https://youtu.be/_ZvnD73m40o?si=6pbeG2cBhblMB89M"},
        {"title":"YouTube: https://youtu.be/ScKCy2udln8?si=fSc5H1dJy8xGrwSR", "url":"https://youtu.be/ScKCy2udln8?si=fSc5H1dJy8xGrwSR"}
      ],
      "postId": "67d83a9be0acac6d68d558cf",
      "profile": "4264684b-2286-4ff5-8f43-da163fb980d7-blog9.jpg",
      "title": "Prompt template structure"
    }
  ],
  "suggestions": [
    "How to evaluate LLMs in real-world applications?",
    "What are the key components of a RAG system?",
    "How does LangSmith enhance LLM performance?"
  ],
  "type": "post_suggestions",
  "videos": null
}
```

Field explanations:
- content: Markdown-formatted summary or explanation generated by the LLM.
- posts: Array of suggested or related posts (each contains metadata such as title, author, postId, images, links).
- suggestions: short follow-up questions/ideas for posts or further reading.
- type: high-level response classification (e.g., "post_suggestions").
- videos: optional video list or null.

---

## Example Query Input

A typical query payload:
```json
{
  "query": "summarize it, suggest post content",
  "current_post_id": "689c1079f0093cfba6c981d5"
}
```
This instructs the system to summarize the content related to `current_post_id` and propose suggested posts or content ideas.

---

## Implementation Notes & Best Practices

- Embedding model: `text-embedding-3-small` — ensure you use the same encoder for both ingestion and querying to keep vector spaces consistent.
- Embedding dimension: 521. When creating Pinecone index, make sure the vector dimension is set accordingly.
- Upsert metadata: store `postId`, `authorEmail`, `authorName`, `category`, `title`, `url`/`links`, chunk id / offset. Metadata ensures you can rehydrate results into structured post objects.
- Top-k retrieval: tune `k` (default often between 3–10) depending on chunk size and retrieval quality.
- Prompting: combine retrieved chunks with system & role prompts (see `utility/prompt.py`). Keep prompts deterministic and include instructions for JSON-only output if you want strict machine-parsable results.
- Chunking & overlap: choose chunk size & overlap to balance context quality vs. retrieval noise.
- Pinecone namespaces: use namespaces to separate environments or tenants.

---

## Production Considerations

- Rate limits & batching: batch embeddings to reduce API round-trips; handle OpenAI and Pinecone rate-limits.
- Cost monitoring: embeddings incur cost — monitor usage by counting tokens/requests.
- Vector index lifecycle: consider retention and reindexing strategies for updated posts.
- Caching: cache frequently asked queries or LLM responses where appropriate.
- Security: never commit secrets. Use environment variables or secret stores. Limit access to Pinecone and OpenAI keys.
- Observability: log retrieval scores, top-k ids, prompt sent to LLM (or a hashed version) for traceability. Add latency metrics for embeddings, Pinecone calls, and LLM calls.
- Testing & Evaluation: implement quality checks (e.g., ground-truth tests or human-in-the-loop review) to validate generated suggestions.

---

## Troubleshooting

- Mismatch embedding dim error in Pinecone: make sure the Pinecone index dimension matches EMBEDDING_DIM (521).
- No results returned: check namespace, index name, and that ingestion succeeded (inspect `pinecone_client.py` upsert logs).
- JSON parse errors from LLM: enforce stricter prompt instructions and consider sampling/temperature settings that favor deterministic outputs (e.g., temperature=0).

---

## Extending / Customization

- Swap LLM or embedding models: update `utility/embedder.py` and prompt temperature/parameters.
- Multiple indices or hybrid search: support separate indices per category or add metadata filtering in Pinecone queries.
- Add more output types: e.g., direct “tweetable summary”, long-form blog post, slides, or code snippets.

---

## Contributing

Contributions and improvements are welcome. Follow these steps:
1. Fork the repo
2. Create a new branch (feature/your-change)
3. Run tests (if present) and linters
4. Open a PR with a clear description of changes

Please keep secrets and API keys out of PRs.

---

## License & Contact

- License: Add appropriate license file (e.g., MIT) if desired.
- Contact: Yugesh Karan (owner): yugeshkaran01@gmail.com

---

If you want, I can:
- produce a shorter README (one-page summary), or
- generate an OpenAPI or Postman collection for the API surface (based on `app.py`), or
- open a draft README.md PR for you with this content.

```
