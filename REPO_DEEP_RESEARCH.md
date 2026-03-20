# Ingestion and Retrieval Deep Concepts (GraphMind + Optimized GraphRAG)

## Document Goal
This single document explains the ingestion and retrieval system end-to-end at implementation depth, with special focus on concepts introduced or inspired by the optimized GraphRAG material in the repository.

## Source Basis
- Runtime implementation: backend route, orchestrator, graph, vector, extraction, cache, and background services.
- Optimized references: GraphRAG indexing and query docs from optimized/.
- optimized/docs/index/overview.md
- optimized/docs/index/default_dataflow.md
- optimized/docs/index/methods.md
- optimized/docs/query/overview.md
- optimized/docs/query/local_search.md
- optimized/docs/query/global_search.md
- optimized/docs/query/drift_search.md

## 1. System Mental Model
At runtime, GraphMind is a hybrid memory engine with two tightly coupled planes:
1. Graph memory plane: typed nodes and edges in Neo4j for explicit reasoning, user isolation, contradiction tracking, and relationship-aware scoring.
2. Vector memory plane: chunk embeddings for fuzzy semantic recall, with Milvus-first search and Neo4j-vector fallback.

The core design principle is: ingest once into both planes, retrieve from both planes in parallel, then fuse and rank with strategy-aware controls.

## 2. Ingestion Concepts in Detail
### 2.1 Entry Points and Ingestion Triggers
- Chat ingestion path: backend/api/routes/chat.py classifies a message into MEMORY, QUESTION, or BOTH. MEMORY and BOTH trigger memory ingestion before response finalization.
- Document ingestion path: backend/api/routes/documents.py extracts text (PDF/DOCX/TXT/Image OCR), then runs extraction and graph/vector persistence pipeline.

### 2.2 LLM-to-Graph Translation Contract
The extractor (backend/services/extraction/llm_extractor.py) defines a strict schema contract:
- Entity types are constrained (Asset, Goal, Transaction, RiskProfile, Entity, Event, Preference, Fact).
- Relationship types are constrained (OWNS, MADE_TRANSACTION, AFFECTS_ASSET, CONFIRMS, RELATES_TO, etc.).
- Canonical memory pattern is enforced in prompt design: User -> MADE_TRANSACTION -> Transaction -> AFFECTS_ASSET -> Asset, with Fact -> CONFIRMS.
- Facts should be atomic and non-redundant, minimizing semantic duplication.

### 2.3 Graph Persistence Algorithm
GraphIngestion (backend/services/graph/ingestion.py) applies deterministic write semantics after probabilistic extraction:
1. Ensure User node exists (MERGE).
2. Create Message node and link ownership.
3. Deduplicate Fact by text per user; reinforce confidence/reinforcement_count if existing.
4. Merge typed nodes and construct canonical relationships for transaction and asset flow.
5. Link facts to structured nodes using CONFIRMS; add RELATES_TO for semantic back-links.
6. Optionally run contradiction detection and contradiction edges (skipped for some document workflows).

Important property: user_id is embedded in virtually all matching and writing clauses, establishing strict tenant isolation.

### 2.4 Finalization Layer (Ingestion-Time Retrieval Optimization)
Entity finalization (called by MemoryOrchestrator) computes retrieval-oriented features and materialized retrieval views. This is a major bridge to optimized GraphRAG ideas: preprocessing graph artifacts to make query-time retrieval cheaper and higher quality.

### 2.5 Vector Ingestion Algorithm
VectorRetrieval.ingest_message (backend/services/vector/retrieval.py):
- Splits message into overlapping chunks.
- Embeds each chunk.
- Persists DocumentChunk nodes with embedding vectors and metadata.
- Creates MENTIONS links to related graph node ids when available.

MemoryOrchestrator also pushes chunk batches to Milvus when available; this adds a high-performance ANN path while preserving Neo4j fallback.

### 2.6 Document/OCR Ingestion
TextExtractor (backend/services/extraction/text_extractor.py) supports:
- PDF text extraction with scanned-PDF fallback to OCR.
- DOCX structured text and table extraction.
- Image OCR through PaddleOCR.
- TXT pass-through.

Conceptual significance: ingestion quality in OCR modes directly bounds retrieval relevance later, because graph and vectors depend on extracted text quality.

### 2.7 Cache Invalidation as Ingestion Primitive
After ingestion, retrieval cache is invalidated for that user. This is essential to prevent stale retrieval context after memory writes.

## 3. Retrieval Concepts in Detail
### 3.1 Retrieval Control Plane
RetrievalOrchestrator (backend/services/orchestrator/retrieval_orchestrator.py) is the top-level retrieval algorithm controller. It performs:
1. Query decomposition and routing to strategy plan.
2. Cache lookup for retrieval context reuse.
3. Parallel graph + vector retrieval.
4. Reciprocal-rank-fusion-like mixing and hybrid learned ranking.
5. Strategy-aware context budgeting.
6. Answer generation, citations, and deferred reinforcement feedback.

### 3.2 Strategy Layer (Basic / Local / Global / Drift)
QueryRouter (backend/services/graph/query_router.py) adds a GraphRAG-style strategy abstraction:
- BASIC: short direct lookup queries.
- LOCAL: default personalized reasoning mode.
- GLOBAL: broad summarization intent.
- DRIFT: exploratory follow-up expansion mode.

This is one of the clearest new contributions aligned with optimized docs: explicit strategy selection with per-strategy retrieval budgets.

### 3.3 Query Understanding and Mode Selection
QueryUnderstanding (backend/services/graph/query_understanding.py) classifies queries into graph retrieval modes:
- DIRECT_LOOKUP
- AGGREGATION
- RELATIONAL_REASONING
It also extracts timeline filters and query keywords used downstream for relevance scoring.

### 3.4 Graph Retrieval Algorithm
GraphRetrieval (backend/services/graph/retrieval.py) performs controlled traversal, not wildcard expansion:
1. Mode-specific Cypher templates are selected.
2. RetrievalView precomputed candidates are tried first (fast path).
3. Timeline and user isolation filters are applied.
4. Nodes are scored by a multi-signal function: query relevance, hop distance, centrality, recency, confidence, reinforcement, relationship quality.
5. Low-score noise is filtered; top-k returned.

Scoring design reflects a shift from pure distance to importance-aware retrieval (centrality and reinforcement carry explicit weight).

### 3.5 Vector Retrieval Algorithm
Vector path has two operational modes:
- Milvus semantic search first (when collection available).
- Neo4j chunk similarity fallback with adaptive thresholding and recency ordering.

The fallback behavior ensures continuity when ANN infra is unavailable, but can change recall/latency characteristics.

### 3.6 Fusion and Ranking
Two-layer ranking is applied:
1. Adaptive RRF-like fusion in orchestrator with confidence-modulated source weighting.
2. HybridRanker mode-aware scoring (graph, vector, recency, confidence, reinforcement, community signals) plus user feedback bias persistence.

### 3.7 Global Retrieval (Map-Reduce Style)
Global mode in orchestrator implements GraphRAG-style map-reduce behavior:
- Select communities dynamically from retrieved evidence.
- Generate per-community map summaries.
- Reduce summaries into a final answer.
- Persist selected communities and summaries for reuse across sessions.

### 3.8 Drift Retrieval (Iterative Expansion)
DRIFT mode runs iterative follow-up expansion:
- Seed with initial retrieval.
- Generate follow-up questions from current evidence.
- Re-retrieve and merge unique graph/vector evidence across iterations.
- Stop by depth and follow-up caps, then synthesize final answer.

### 3.9 Context Budgeting and Citation Construction
Strategy-specific thresholds and context limits decide graph/vector payload size into answer generation. Citation objects include retrieval score, confidence, source attribution, and score breakdown for explainability.

## 4. New Additions from Optimized GraphRAG (What Changed Conceptually)
| Optimized Concept | Meaning in Optimized Docs | GraphMind Implementation Status | Runtime Location |
|---|---|---|---|
| Local Search | Entity-centered mixed graph+text retrieval | Implemented in spirit through LOCAL strategy + mixed graph/vector context | backend/services/graph/query_router.py, backend/services/orchestrator/retrieval_orchestrator.py |
| Global Search | Community report map-reduce over dataset themes | Implemented in adapted form with community selector + map/reduce answer flow | backend/services/orchestrator/retrieval_orchestrator.py, backend/services/graph/community_selector.py |
| DRIFT Search | Dynamic expansion with community-guided follow-ups | Implemented as iterative follow-up retrieval with capped depth/followups | backend/services/orchestrator/retrieval_orchestrator.py |
| Community Artifacts | Durable community-level summaries | Implemented via Neo4j Community nodes + persistence + refresh worker | backend/services/graph/community_persistence.py, backend/services/graph/community_refresh.py |
| Precomputed Retrieval Views | Query-time speedup through prepared access paths | Implemented via RetrievalView materialized candidate fast path | backend/services/graph/retrieval.py |
| Multi-Method Indexing Ideas | Standard vs Fast extraction tradeoffs | Partially reflected (LLM-first extractor still primary; NLP-fast extraction not yet first-class in runtime) | optimized/docs/index/methods.md, backend/services/extraction/llm_extractor.py |
| Knowledge Model Expansion | Documents, text units, entities, relations, covariates, communities | Partially mapped: Facts/Entities/Transactions/Assets/Goals/Community plus chunks in Neo4j | backend/services/graph/*.py, backend/services/vector/retrieval.py |

## 5. Ingestion and Retrieval Invariants
1. User isolation invariant: every retrieval/write must remain scoped by user id in graph and chunk stores.
2. Canonical event modeling invariant: transaction facts should map through Transaction node, not directly as denormalized asset facts.
3. Recency-confidence invariant: scoring and decay should not diverge (online scoring decay vs background hard decay).
4. Cache correctness invariant: all ingestion writes should invalidate or version retrieval cache.
5. Strategy-budget invariant: selected strategy must govern context limits and thresholds consistently.

## 6. Current Gaps and Engineering Risks (Conceptual)
- Chunking mismatch risk: orchestrator chunking uses character-style slicing while vector retrieval uses word-based chunking; harmonization would reduce retrieval drift between stores.
- Heuristic router risk: deterministic keyword routing can misclassify nuanced queries compared to model-assisted strategy selection.
- Optional dependency observability risk: Milvus/S3 fallback paths continue execution but rely on print warnings; structured telemetry would improve operability.
- Contradiction precision risk: contradiction handling is downstream and heuristic; model confidence calibration across contradictory facts may need stronger policy.

## 7. Constant Ledger for Ingestion/Retrieval Controls
This appendix lists machine-detected constants and control lines from ingestion/retrieval-critical modules.

| File | Line | Name | Kind | Value |
|---|---:|---|---|---|
| backend/services/cache/retrieval_cache.py | 26 | <line_control> | line_signal | def __init__(self, max_size: int = 1000, ttl_seconds: int = 300): |
| backend/services/cache/retrieval_cache.py | 32 | <line_control> | line_signal | ttl_seconds: Time-to-live for cached entries (default: 5 minutes) |
| backend/services/cache/retrieval_cache.py | 35 | <line_control> | line_signal | self.ttl_seconds = ttl_seconds |
| backend/services/cache/retrieval_cache.py | 85 | <line_control> | line_signal | "expires_at": time.time() + self.ttl_seconds, |
| backend/services/cache/retrieval_cache.py | 117 | <line_control> | line_signal | "ttl_seconds": self.ttl_seconds |
| backend/services/cache/retrieval_cache.py | 145 | <line_control> | line_signal | _retrieval_cache = RetrievalCache(max_size=1000, ttl_seconds=300) |
| backend/services/extraction/text_extractor.py | 52 | SUPPORTED_FORMATS | python_constant | {'.pdf': 'PDF Document', '.docx': 'Word Document', '.doc': 'Word Document (Legacy)', '.txt': 'Plain Text', '.png': 'Image (PNG)', '.jpg': 'Image (JPEG)', '.jpeg': 'Image (JPEG)'} |
| backend/services/extraction/text_extractor.py | 63 | <line_control> | line_signal | MAX_CHUNK_SIZE = 1000 |
| backend/services/extraction/text_extractor.py | 63 | MAX_CHUNK_SIZE | python_constant | 1000 |
| backend/services/extraction/text_extractor.py | 64 | <line_control> | line_signal | OVERLAP = 100 |
| backend/services/extraction/text_extractor.py | 64 | OVERLAP | python_constant | 100 |
| backend/services/extraction/text_extractor.py | 214 | <line_control> | line_signal | # Check if PDF is scanned (very little text extracted) |
| backend/services/extraction/text_extractor.py | 493 | <line_control> | line_signal | chunk_size: int = MAX_CHUNK_SIZE, |
| backend/services/graph/community_persistence.py | 138 | <line_control> | line_signal | top_k=top_k, |
| backend/services/graph/community_refresh.py | 34 | <line_control> | line_signal | self.interval_seconds = max(300, Settings.COMMUNITY_REFRESH_INTERVAL_SECONDS) |
| backend/services/graph/community_selector.py | 30 | STOP_WORDS | python_constant | {'the', 'a', 'an', 'of', 'to', 'and', 'or', 'in', 'on', 'for', 'with', 'is', 'are', 'was', 'were', 'my', 'your', 'our', 'their', 'what', 'how', 'when', 'where', 'why', 'which', 'show', 'tell', 'about', 'all', 'overall'} |
| backend/services/graph/community_selector.py | 111 | overlap | control_variable | len(chunk_tokens & title_tokens) / denom |
| backend/services/graph/hybrid_ranker.py | 29 | MODE_WEIGHTS | python_constant | {'basic': RankWeights(0.45, 0.3, 0.05, 0.1, 0.05, 0.05), 'local': RankWeights(0.35, 0.2, 0.15, 0.15, 0.1, 0.05), 'global': RankWeights(0.2, 0.1, 0.1, 0.1, 0.05, 0.45), 'drift': RankWeights(0.25, 0.25, 0.15, 0.1, 0.1, 0.1 |
| backend/services/graph/ingestion.py | 437 | STOP_WORDS | python_constant | {'i', 'a', 'in', 'of', 'the', 'is', 'my', 'to', 'and', 'or', 'at', 'for', 'have', 'has', 'had', 'by', 'it', 'be', 'an', 'on', 'user', 'that'} |
| backend/services/graph/ingestion.py | 472 | overlap | control_variable | new_words & old_words |
| backend/services/graph/memory_decay.py | 23 | <line_control> | line_signal | self.interval_seconds = max(60, Settings.MEMORY_HARD_DECAY_INTERVAL_SECONDS) |
| backend/services/graph/memory_decay.py | 24 | <line_control> | line_signal | self.batch_size = max(10, Settings.MEMORY_HARD_DECAY_BATCH_SIZE) |
| backend/services/graph/memory_decay.py | 25 | <line_control> | line_signal | self.half_life_days = max(1.0, Settings.MEMORY_DECAY_HALF_LIFE_DAYS) |
| backend/services/graph/query_decomposition.py | 27 | LOOKUP | python_constant | 'lookup' |
| backend/services/graph/query_decomposition.py | 28 | AGGREGATION | python_constant | 'aggregation' |
| backend/services/graph/query_decomposition.py | 29 | COMPARISON | python_constant | 'comparison' |
| backend/services/graph/query_decomposition.py | 30 | REASONING | python_constant | 'reasoning' |
| backend/services/graph/query_decomposition.py | 31 | ALIGNMENT | python_constant | 'alignment' |
| backend/services/graph/query_decomposition.py | 32 | TREND | python_constant | 'trend' |
| backend/services/graph/query_decomposition.py | 61 | SYNONYMS | python_constant | {'asset': ['holding', 'investment', 'stock', 'mutual fund', 'property', 'bond'], 'transaction': ['trade', 'purchase', 'sale', 'buy', 'sell', 'invest'], 'goal': ['target', 'objective', 'plan', 'aspiration'], 'aligned': [' |
| backend/services/graph/query_decomposition.py | 72 | INTENT_PATTERNS | python_constant | {QueryIntent.LOOKUP: ['what', 'list', 'show', 'tell me', 'which', 'where', 'find', 'get'], QueryIntent.AGGREGATION: ['how much', 'total', 'sum', 'count', 'all', 'entire', 'overall', 'combined'], QueryIntent.COMPARISON: [ |
| backend/services/graph/query_decomposition.py | 82 | TEMPORAL_PATTERNS | python_constant | {'last month': timedelta(days=30), 'last week': timedelta(days=7), 'last year': timedelta(days=365), 'last quarter': timedelta(days=90), 'this month': timedelta(days=30), 'this year': timedelta(days=365), 'last 3 months' |
| backend/services/graph/query_router.py | 17 | BASIC | python_constant | 'basic' |
| backend/services/graph/query_router.py | 18 | LOCAL | python_constant | 'local' |
| backend/services/graph/query_router.py | 19 | GLOBAL | python_constant | 'global' |
| backend/services/graph/query_router.py | 20 | DRIFT | python_constant | 'drift' |
| backend/services/graph/query_router.py | 42 | GLOBAL_KEYWORDS | python_constant | {'overall', 'summary', 'summarize', 'big picture', 'across', 'all', 'entire', 'portfolio review'} |
| backend/services/graph/query_router.py | 52 | DRIFT_KEYWORDS | python_constant | {'explore', 'brainstorm', 'what else', 'dig deeper', 'follow up', 'why'} |
| backend/services/graph/query_router.py | 60 | AGGREGATION_KEYWORDS | python_constant | {'how much', 'total', 'sum', 'overall amount', 'combined', 'in total'} |
| backend/services/graph/query_router.py | 79 | <line_control> | line_signal | graph_top_k=14, |
| backend/services/graph/query_router.py | 80 | <line_control> | line_signal | vector_top_k=6, |
| backend/services/graph/query_router.py | 89 | <line_control> | line_signal | graph_top_k=18, |
| backend/services/graph/query_router.py | 90 | <line_control> | line_signal | vector_top_k=7, |
| backend/services/graph/query_router.py | 99 | <line_control> | line_signal | graph_top_k=8, |
| backend/services/graph/query_router.py | 100 | <line_control> | line_signal | vector_top_k=0, |
| backend/services/graph/query_router.py | 109 | <line_control> | line_signal | graph_top_k=8, |
| backend/services/graph/query_router.py | 110 | <line_control> | line_signal | vector_top_k=3, |
| backend/services/graph/query_router.py | 118 | <line_control> | line_signal | graph_top_k=12, |
| backend/services/graph/query_router.py | 119 | <line_control> | line_signal | vector_top_k=5, |
| backend/services/graph/query_understanding.py | 18 | DIRECT_LOOKUP | python_constant | 'direct_lookup' |
| backend/services/graph/query_understanding.py | 19 | RELATIONAL_REASONING | python_constant | 'relational_reasoning' |
| backend/services/graph/query_understanding.py | 20 | AGGREGATION | python_constant | 'aggregation' |
| backend/services/graph/query_understanding.py | 31 | AGGREGATION_KEYWORDS | python_constant | ['how much', 'total', 'sum', 'count', 'all', 'entire', 'overall', 'calculate', 'add up', 'combined'] |
| backend/services/graph/query_understanding.py | 36 | RELATIONAL_KEYWORDS | python_constant | ['why', 'compare', 'aligned', 'relationship', 'between', 'impact', 'affect', 'contributing', 'towards', 'goal', 'progress', 'performance', 'vs', 'versus'] |
| backend/services/graph/query_understanding.py | 42 | DIRECT_LOOKUP_KEYWORDS | python_constant | ['what', 'list', 'show', 'tell me', 'which', 'where', 'who', 'when', 'find', 'get'] |
| backend/services/graph/query_understanding.py | 48 | TIMELINE_PATTERNS | python_constant | {'last month': timedelta(days=30), 'last week': timedelta(days=7), 'last year': timedelta(days=365), 'recent': timedelta(days=7), 'this month': timedelta(days=30), 'this year': timedelta(days=365), 'today': timedelta(day |
| backend/services/graph/retrieval.py | 41 | <line_control> | line_signal | SCORE_WEIGHTS = { |
| backend/services/graph/retrieval.py | 41 | SCORE_WEIGHTS | python_constant | {'graph_distance': 0.2, 'centrality': 0.25, 'recency': 0.2, 'confidence': 0.15, 'reinforcement': 0.1, 'relationship_weight': 0.1} |
| backend/services/graph/retrieval.py | 51 | <line_control> | line_signal | RECENCY_DECAY_LAMBDA = 0.1  # Exponential decay rate |
| backend/services/graph/retrieval.py | 51 | RECENCY_DECAY_LAMBDA | python_constant | 0.1 |
| backend/services/graph/retrieval.py | 160 | candidate_limit | control_variable | max(int(top_k) * 4, 20) |
| backend/services/graph/retrieval.py | 168 | <line_control> | line_signal | candidate_limit=candidate_limit, |
| backend/services/graph/retrieval.py | 372 | <line_control> | line_signal | candidate_limit=int(candidate_limit), |
| backend/services/graph/retrieval.py | 519 | <line_control> | line_signal | -self.RECENCY_DECAY_LAMBDA * days_ago) |
| backend/services/graph/retrieval.py | 537 | <line_control> | line_signal | self.SCORE_WEIGHTS["graph_distance"] * graph_score + |
| backend/services/graph/retrieval.py | 538 | <line_control> | line_signal | self.SCORE_WEIGHTS["centrality"] * centrality_score + |
| backend/services/graph/retrieval.py | 539 | <line_control> | line_signal | self.SCORE_WEIGHTS["recency"] * recency_score + |
| backend/services/graph/retrieval.py | 540 | <line_control> | line_signal | self.SCORE_WEIGHTS["confidence"] * confidence + |
| backend/services/graph/retrieval.py | 541 | <line_control> | line_signal | self.SCORE_WEIGHTS["reinforcement"] * reinforcement_score + |
| backend/services/graph/retrieval.py | 542 | <line_control> | line_signal | self.SCORE_WEIGHTS["relationship_weight"] * relationship_weight |
| backend/services/orchestrator/memory_orchestrator.py | 84 | <line_control> | line_signal | message, chunk_size=450, overlap=60) |
| backend/services/orchestrator/retrieval_orchestrator.py | 30 | <line_control> | line_signal | RRF_K = 60 |
| backend/services/orchestrator/retrieval_orchestrator.py | 30 | RRF_K | python_constant | 60 |
| backend/services/orchestrator/retrieval_orchestrator.py | 31 | <line_control> | line_signal | MAX_RETRIEVAL_MS = 100  # Target: sub-100ms retrieval |
| backend/services/orchestrator/retrieval_orchestrator.py | 31 | MAX_RETRIEVAL_MS | python_constant | 100 |
| backend/services/orchestrator/retrieval_orchestrator.py | 32 | <line_control> | line_signal | GLOBAL_MAP_BATCH_SIZE = 4 |
| backend/services/orchestrator/retrieval_orchestrator.py | 32 | GLOBAL_MAP_BATCH_SIZE | python_constant | 4 |
| backend/services/orchestrator/retrieval_orchestrator.py | 33 | <line_control> | line_signal | DRIFT_MAX_DEPTH = 2 |
| backend/services/orchestrator/retrieval_orchestrator.py | 33 | DRIFT_MAX_DEPTH | python_constant | 2 |
| backend/services/orchestrator/retrieval_orchestrator.py | 34 | <line_control> | line_signal | DRIFT_MAX_FOLLOWUPS = 2 |
| backend/services/orchestrator/retrieval_orchestrator.py | 34 | DRIFT_MAX_FOLLOWUPS | python_constant | 2 |
| backend/services/orchestrator/retrieval_orchestrator.py | 214 | <line_control> | line_signal | "retrieval_optimized": retrieval_ms < self.MAX_RETRIEVAL_MS, |
| backend/services/orchestrator/retrieval_orchestrator.py | 359 | <line_control> | line_signal | max_depth=retrieval_plan.graph_depth, |
| backend/services/orchestrator/retrieval_orchestrator.py | 360 | <line_control> | line_signal | top_k=retrieval_plan.graph_top_k, |
| backend/services/orchestrator/retrieval_orchestrator.py | 388 | <line_control> | line_signal | user_id, query, top_k=retrieval_plan.vector_top_k |
| backend/services/orchestrator/retrieval_orchestrator.py | 398 | <line_control> | line_signal | top_k=retrieval_plan.vector_top_k |
| backend/services/orchestrator/retrieval_orchestrator.py | 420 | <line_control> | line_signal | top_k=top_k, |
| backend/services/orchestrator/retrieval_orchestrator.py | 421 | <line_control> | line_signal | threshold=0.4  # Lower threshold for more results |
| backend/services/orchestrator/retrieval_orchestrator.py | 484 | graph_weight | control_variable | graph_confidence_avg / total_confidence |
| backend/services/orchestrator/retrieval_orchestrator.py | 485 | vector_weight | control_variable | vector_confidence_avg / total_confidence |
| backend/services/orchestrator/retrieval_orchestrator.py | 487 | graph_weight | control_variable | 0.5 |
| backend/services/orchestrator/retrieval_orchestrator.py | 488 | vector_weight | control_variable | 0.5 |
| backend/services/orchestrator/retrieval_orchestrator.py | 496 | <line_control> | line_signal | base_rrf = 1.0 / (self.RRF_K + rank) |
| backend/services/orchestrator/retrieval_orchestrator.py | 518 | <line_control> | line_signal | base_rrf = 1.0 / (self.RRF_K + rank) |
| backend/services/orchestrator/retrieval_orchestrator.py | 538 | top_k | control_variable | Settings.DEFAULT_TOP_K * 2 |
| backend/services/orchestrator/retrieval_orchestrator.py | 560 | <line_control> | line_signal | top_k=3, |
| backend/services/orchestrator/retrieval_orchestrator.py | 567 | <line_control> | line_signal | top_k=2, |
| backend/services/orchestrator/retrieval_orchestrator.py | 719 | <line_control> | line_signal | graph_top_k=max(8, retrieval_plan.graph_top_k), |
| backend/services/orchestrator/retrieval_orchestrator.py | 720 | <line_control> | line_signal | vector_top_k=max(4, retrieval_plan.vector_top_k), |
| backend/services/orchestrator/retrieval_orchestrator.py | 724 | <line_control> | line_signal | while pending_queries and iterations < self.DRIFT_MAX_DEPTH: |
| backend/services/orchestrator/retrieval_orchestrator.py | 748 | <line_control> | line_signal | if total_followups >= self.DRIFT_MAX_FOLLOWUPS: |
| backend/services/orchestrator/retrieval_orchestrator.py | 751 | <line_control> | line_signal | if total_followups >= self.DRIFT_MAX_FOLLOWUPS: |
| backend/services/orchestrator/retrieval_orchestrator.py | 788 | <line_control> | line_signal | return lines[: self.DRIFT_MAX_FOLLOWUPS] |
| backend/services/orchestrator/retrieval_orchestrator.py | 844 | quality_threshold | control_variable | 0.12 |
| backend/services/orchestrator/retrieval_orchestrator.py | 845 | graph_limit | control_variable | 5 |
| backend/services/orchestrator/retrieval_orchestrator.py | 846 | vector_limit | control_variable | 2 |
| backend/services/orchestrator/retrieval_orchestrator.py | 848 | quality_threshold | control_variable | 0.1 |
| backend/services/orchestrator/retrieval_orchestrator.py | 849 | graph_limit | control_variable | 12 |
| backend/services/orchestrator/retrieval_orchestrator.py | 850 | vector_limit | control_variable | 6 |
| backend/services/orchestrator/retrieval_orchestrator.py | 852 | quality_threshold | control_variable | 0.11 |
| backend/services/orchestrator/retrieval_orchestrator.py | 853 | graph_limit | control_variable | 10 |
| backend/services/orchestrator/retrieval_orchestrator.py | 854 | vector_limit | control_variable | 6 |
| backend/services/orchestrator/retrieval_orchestrator.py | 856 | quality_threshold | control_variable | 0.11 |
| backend/services/orchestrator/retrieval_orchestrator.py | 857 | graph_limit | control_variable | 8 |
| backend/services/orchestrator/retrieval_orchestrator.py | 858 | vector_limit | control_variable | 5 |
| backend/services/vector/retrieval.py | 49 | <line_control> | line_signal | message_text, chunk_size=chunk_size, overlap=overlap) |
| backend/services/vector/retrieval.py | 130 | top_k | control_variable | top_k or Settings.VECTOR_TOP_K |
| backend/services/vector/retrieval.py | 132 | candidate_limit | control_variable | candidate_limit or min(Settings.VECTOR_CANDIDATE_LIMIT, 200) |
| backend/services/vector/retrieval.py | 156 | <line_control> | line_signal | candidate_limit=candidate_limit |

## 8. Optimized Concept Reference Summary
- Indexing dataflow phases (TextUnits -> Graph extraction -> Communities -> Reports -> Embeddings): optimized/docs/index/default_dataflow.md
- Local search entity reasoning and mixed context: optimized/docs/query/local_search.md
- Global search map-reduce over community reports: optimized/docs/query/global_search.md
- DRIFT dynamic expansion and follow-up hierarchy: optimized/docs/query/drift_search.md
- Standard vs Fast GraphRAG indexing tradeoffs: optimized/docs/index/methods.md

## 9. Final Takeaway
Your current GraphMind ingestion/retrieval architecture already embeds core GraphRAG patterns from optimized materials: strategy-aware retrieval, community-assisted global answers, iterative drift expansion, and hybrid graph+vector fusion. The remaining frontier is consistency and calibration: unify chunking semantics, strengthen observability, and tighten routing/contradiction policies for production-grade reliability.
