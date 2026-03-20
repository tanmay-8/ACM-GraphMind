# GraphMind Actual Ingestion and Retrieval: Step-by-Step with Why

## Purpose of This Document
This document explains the real runtime ingestion and retrieval pipeline in GraphMind, in strict step order, with the reason each step exists.

It is intentionally operational (what actually happens in code), not just conceptual.

---

## A. High-Level Runtime Model
GraphMind uses two memory layers in parallel:

1. Graph memory (Neo4j)
- Stores explicit typed knowledge (Fact, Transaction, Asset, Goal, etc.) and relationships.
- Best for structured reasoning and explainability.

2. Vector memory (chunk embeddings)
- Stores semantic representations for fuzzy similarity retrieval.
- Best for recall when wording differs.

Why both:
- Graph gives precision and structure.
- Vector gives semantic recall.
- Fusing both improves answer quality and robustness.

Primary implementation files:
- backend/api/routes/chat.py
- backend/services/orchestrator/memory_orchestrator.py
- backend/services/orchestrator/retrieval_orchestrator.py
- backend/services/graph/ingestion.py
- backend/services/graph/retrieval.py
- backend/services/vector/retrieval.py

---

## B. Chat Ingestion Flow (When a user sends memory-like text)

### Step 1: API entry and auth validation
Where:
- backend/api/routes/chat.py

What happens:
- Request hits POST /chat.
- JWT is verified.
- PostgreSQL user is resolved and mapped to neo4j_user_id.
- Session is created/fetched.
- User message is persisted to chat_messages.

Why:
- Authentication ensures tenant isolation.
- Session persistence creates chat history continuity.
- Storing user message first gives auditability even if downstream fails.

---

### Step 2: Intent classification (MEMORY / QUESTION / BOTH)
Where:
- backend/services/llm/intent_classifier.py
- called from backend/api/routes/chat.py

What happens:
- Message intent is classified.
- MEMORY -> store memory only.
- QUESTION -> retrieve + answer only.
- BOTH -> store then retrieve + answer.

Why:
- Avoid unnecessary retrieval for pure memory updates.
- Avoid unnecessary ingestion for pure questions.
- Keeps latency and cost lower.

---

### Step 3: Structured extraction from natural language
Where:
- backend/services/extraction/llm_extractor.py
- called by backend/services/orchestrator/memory_orchestrator.py

What happens:
- LLM extracts facts, nodes, relationships from raw text.
- Schema is constrained by prompt (types/relations).
- IDs are added if missing.

Why:
- Raw text is not directly query-efficient.
- Structured extraction converts narrative into retrievable graph primitives.
- Schema constraints reduce hallucinated structure drift.

---

### Step 4: Graph ingestion (deterministic write phase)
Where:
- backend/services/graph/ingestion.py

What happens:
1. Ensure User node exists.
2. Create Message node linked to User.
3. Create or reinforce Fact nodes (dedupe by text).
4. Merge domain nodes (Transaction, Asset, Goal, etc.).
5. Build canonical edges (e.g., MADE_TRANSACTION, AFFECTS_ASSET).
6. Link facts via CONFIRMS / RELATES_TO.
7. Optional contradiction detection for fresh facts.

Why:
- Creates stable, user-scoped knowledge graph.
- Dedupe + reinforcement prevent memory spam and track confidence over time.
- Canonical edge shapes enable predictable retrieval queries.

---

### Step 5: Retrieval quality finalization
Where:
- backend/services/graph/entity_finalizer.py
- called from backend/services/orchestrator/memory_orchestrator.py

What happens:
- Computes retrieval-oriented features (for ranking).
- Builds/updates RetrievalView-like precomputed hints.

Why:
- Moves some retrieval work to write-time.
- Improves query-time speed and ranking quality.

---

### Step 6: Vector ingestion
Where:
- backend/services/vector/retrieval.py
- backend/services/vector/milvus_service.py
- called from backend/services/orchestrator/memory_orchestrator.py

What happens:
- Message is chunked.
- Chunks are embedded.
- Chunks are stored in Neo4j as DocumentChunk (with metadata).
- Optional Milvus batch ingestion executes if available.

Why:
- Graph retrieval alone can miss semantically similar phrasing.
- Vector index improves fuzzy recall and long-text matching.
- Optional Milvus provides faster semantic search for larger scale.

---

### Step 7: Cache invalidation
Where:
- backend/services/cache/retrieval_cache.py
- called from backend/services/orchestrator/memory_orchestrator.py

What happens:
- User-specific retrieval cache is invalidated after write.

Why:
- Prevent stale answers immediately after new memory is ingested.

---

### Step 8: Assistant persistence for ingestion outcome
Where:
- backend/api/routes/chat.py
- backend/services/database/chat_service.py

What happens:
- Assistant message is persisted with intent and metadata.

Why:
- Makes memory action visible in chat history and debuggable.

---

## C. Document Ingestion Flow (Upload + ingest)

### Step 1: Upload and type validation
Where:
- backend/api/routes/documents.py

What happens:
- Validates extension and size.
- Reads file bytes.

Why:
- Reject unsupported or unsafe payloads early.

---

### Step 2: Text extraction (format-specific)
Where:
- backend/services/extraction/text_extractor.py

What happens:
- PDF: text extraction, OCR fallback for scanned docs.
- DOCX: paragraphs + tables.
- Images: PaddleOCR.
- TXT: direct decode.

Why:
- Everything downstream requires text.
- OCR fallback ensures scanned docs still become memory.

---

### Step 3: Optional S3 upload
Where:
- backend/services/storage/s3_storage.py

What happens:
- Attempts to upload original file to S3.
- Failures are best-effort warnings, not hard failure.

Why:
- Keeps ingestion usable even when object storage is unavailable.

---

### Step 4: Ingest through same memory pipeline
Where:
- backend/api/routes/documents.py
- backend/services/orchestrator/memory_orchestrator.py

What happens:
- Extracted text is pushed into memory orchestrator.
- Graph + vector + finalizer + cache invalidation run exactly like chat memory ingestion.

Why:
- Single ingestion pipeline means consistent memory semantics.
- Avoids divergence between chat-sourced and document-sourced memory.

---

### Step 5: Document event trace in chat history
Where:
- backend/api/routes/documents.py
- backend/services/database/chat_service.py

What happens:
- After successful document ingestion, an assistant message is written to active chat session with counts and document metadata.

Why:
- User needs visible trace of uploads in chat timeline.
- Improves trust and observability.

---

## D. Retrieval Flow (Question answering)

### Step 1: Entry and strategy setup
Where:
- backend/services/orchestrator/retrieval_orchestrator.py
- backend/services/graph/query_decomposition.py
- backend/services/graph/query_router.py

What happens:
- Decompose query into intent cues.
- Choose strategy: basic, local, global, drift.
- Apply optional strategy override from request.

Why:
- Different questions need different retrieval plans.
- Strategy controls depth, top_k, and vector usage budget.

---

### Step 2: Retrieval cache check
Where:
- backend/services/cache/retrieval_cache.py

What happens:
- Check user+query retrieval context cache (TTL-based).
- If hit: skip retrieval calls.
- If miss: execute retrieval.

Why:
- Reduces repeated latency/cost for near-identical queries.

---

### Step 3: Parallel graph + vector retrieval
Where:
- backend/services/orchestrator/retrieval_orchestrator.py

What happens:
- Graph retrieval and vector retrieval are executed concurrently (thread pool / async wrappers).
- Failures fall back gracefully to sequential or partial results.

Why:
- Most latency comes from I/O and DB calls; parallelization lowers p95 latency.

---

### Step 4: Graph retrieval internals
Where:
- backend/services/graph/retrieval.py
- backend/services/graph/query_understanding.py

What happens:
1. Query mode classification (DIRECT_LOOKUP / AGGREGATION / RELATIONAL_REASONING).
2. Optional timeline extraction.
3. Mode-specific Cypher execution (no wildcard path explosion).
4. Precomputed candidate fast path (RetrievalView).
5. Multi-signal score calculation:
   - relevance
   - hop distance
   - centrality
   - recency
   - confidence
   - reinforcement
   - relationship weight
6. Filter low-score nodes and return top_k.

Why:
- Controlled traversal protects performance and relevance.
- Multi-signal ranking balances freshness, importance, and semantic fit.

---

### Step 5: Vector retrieval internals
Where:
- backend/services/orchestrator/retrieval_orchestrator.py
- backend/services/vector/milvus_service.py
- backend/services/vector/retrieval.py

What happens:
- Try Milvus semantic search first (if available).
- Fallback to Neo4j chunk similarity search.
- Candidate filtering and top_k truncation applied.

Why:
- Milvus is faster for ANN at scale.
- Neo4j fallback maintains functionality when Milvus is unavailable.

---

### Step 6: Fusion and reranking
Where:
- backend/services/orchestrator/retrieval_orchestrator.py
- backend/services/graph/hybrid_ranker.py

What happens:
1. RRF-style fusion merges graph + vector ranked lists.
2. Source weights adapt using confidence averages.
3. Hybrid ranker applies mode-aware weights and feedback bias.
4. Results are strategy-filtered into graph and vector context budgets.

Why:
- Single-source retrieval is brittle.
- Fusion improves recall; reranking improves precision.
- Strategy budgets prevent context overflow and noise.

---

### Step 7: Strategy-specific answer generation
Where:
- backend/services/orchestrator/retrieval_orchestrator.py
- backend/services/llm/answer_generator.py
- backend/services/graph/community_selector.py
- backend/services/graph/community_persistence.py

What happens:
- BASIC/LOCAL: direct answer generation from selected context.
- GLOBAL: community selection -> map summaries -> reduce final answer.
- DRIFT: iterative follow-up query expansion and merge before final answer.

Why:
- Global summary questions need community abstraction.
- Exploratory questions need iterative expansion.
- Direct questions need focused minimal context.

---

### Step 8: Metrics capture and citations
Where:
- backend/services/orchestrator/retrieval_orchestrator.py

What happens:
- Collect decomposition, graph_query_ms, vector_search_ms, retrieval_ms, llm_generation_ms.
- Build citation list with source, score, snippet, breakdown.

Why:
- Transparent timing and grounding for users.
- Essential for debugging and performance tuning.

---

### Step 9: Deferred reinforcement
Where:
- backend/services/orchestrator/retrieval_orchestrator.py
- backend/services/graph/retrieval.py
- backend/services/graph/hybrid_ranker.py

What happens:
- Cited nodes are reinforced asynchronously.
- Ranker feedback bias is updated.

Why:
- Make repeatedly useful memory more retrievable over time.
- Do not block response latency for post-processing.

---

## E. Where Separate Timings Are Stored and Used
Stored fields in chat message persistence:
- graph_query_ms
- vector_search_ms
- retrieval_time_ms
- llm_generation_time_ms

Why this matters:
- Lets UI show precise phase-level timing.
- Makes bottleneck diagnosis possible (graph vs vector vs generation).

Primary files:
- backend/services/database/chat_service.py
- backend/api/routes/chat.py
- frontend/src/pages/Chat.tsx

---

## F. Key Invariants (Must stay true)
1. User isolation invariant
- Every graph/vector query and write must be scoped to the current user.

2. Ingestion consistency invariant
- Chat and document ingestion should pass through equivalent memory semantics.

3. Cache correctness invariant
- Any memory write must invalidate retrieval cache for that user.

4. Strategy-budget invariant
- Router-selected strategy must control retrieval depth/top_k/context limits.

5. Explainability invariant
- Returned answers should preserve citation and score traceability.

---

## G. Practical Debug Checklist
If ingestion seems broken:
1. Verify extraction output contains facts/nodes/relationships.
2. Verify Neo4j write counts (nodes/relationships/facts).
3. Verify chunks_indexed > 0 for vector ingestion.
4. Verify cache invalidation happened.
5. Verify assistant/document event appears in chat_messages.

If retrieval seems weak:
1. Inspect chosen strategy and decomposition confidence.
2. Compare graph_query_ms vs vector_search_ms.
3. Check if vector retrieval is disabled by strategy.
4. Inspect rank scores and citation breakdown.
5. Validate community selection for global mode.

---

## H. Final Summary
Ingestion is a transform-and-persist pipeline:
- text -> structured graph memory + semantic vector memory -> cache invalidation -> history trace.

Retrieval is a plan-and-fuse pipeline:
- query understanding -> parallel graph/vector retrieval -> hybrid fusion/ranking -> strategy-aware generation -> reinforcement.

This architecture is designed to balance:
- precision (graph)
- recall (vector)
- speed (parallelism + cache + precompute)
- transparency (metrics + citations)
- adaptability (strategy routing + feedback reinforcement)
