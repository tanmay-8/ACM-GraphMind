# Source Tracking - System Architecture Diagrams

## 1. High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                             │
│                       (React Frontend)                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Citation Card Component                                           │
│  ├─ Receives: c.source = "graph" | "vector" | "hybrid"            │
│  ├─ Maps: source → (sourceColor, sourceLabel)                     │
│  └─ Renders: <span className={sourceColor}>{sourceLabel}</span>   │
│                                                                     │
│  Visual Result:                                                    │
│  ┌────────────────────────────────────────────┐                   │
│  │ 1 │ Fact │ Graph │ "Investment..." │ 91%  │                   │
│  │     ↑              ↑ (NEW!)                 │                   │
│  │   TypeBadge     SourceBadge                │                   │
│  └────────────────────────────────────────────┘                   │
│                                                                     │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       │ JSON Response with citations
                       │
┌──────────────────────▼──────────────────────────────────────────────┐
│                      API LAYER                                      │
│              (FastAPI / Python)                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ChatResponse Model                                                │
│  ├─ intent: IntentType                                             │
│  ├─ answer: str                                                    │
│  ├─ memory_citations: List[MemoryCitation]                        │
│  │  └─ Each citation has: source: "graph" | "vector"             │
│  ├─ retrieval_metrics: RetrievalMetrics                           │
│  └─ message: str                                                  │
│                                                                     │
│  Example Citation:                                                │
│  {                                                                 │
│    "node_type": "Fact",                                           │
│    "retrieval_score": 0.95,                                       │
│    "source": "graph",  ← ADDED FIELD                             │
│    "snippet": "Investment data..."                                │
│  }                                                                 │
│                                                                     │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       │ Internal routing
                       │
┌──────────────────────▼──────────────────────────────────────────────┐
│                  ORCHESTRATION LAYER                                │
│           (RetrievalOrchestrator Service)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  retrieve_and_answer(user_id, query)                              │
│  ├─ graph_retrieval.retrieve() → List[nodes]                      │
│  ├─ vector_retrieval.search() → List[chunks]                      │
│  ├─ _fuse_rrf(graph_results, vector_results)                     │
│  │  └─ Returns fused list with source info:                      │
│  │     [                                                           │
│  │       {source: "graph", payload: node, ...},                  │
│  │       {source: "vector", payload: chunk, ...}                 │
│  │     ]                                                           │
│  └─ _format_memory_citations(fused_results)                      │
│     ├─ For each item in fused_results:                           │
│     ├─ IF source == "graph":                                     │
│     │   citation["source"] = "graph"  ← SET HERE                │
│     └─ IF source == "vector":                                    │
│         citation["source"] = "vector"  ← SET HERE               │
│                                                                     │
│  Output: List[MemoryCitation] with source field                  │
│                                                                     │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    ┌────────┐   ┌──────────┐   ┌────────┐
    │ Graph  │   │  Vector  │   │ Other  │
    │   DB   │   │  Search  │   │Sources │
    └────────┘   └──────────┘   └────────┘
```

## 2. Citation Formatting Pipeline

```
Input: fused_results from RRF
│
├─ Item 1: {source: "graph", payload: {type: "Fact", ...}}
│  │
│  └─→ Format as citation:
│      {
│        "node_type": "Fact",
│        "retrieval_score": 0.95,
│        "hop_distance": 1,
│        "snippet": "...",
│        "source": "graph",  ← ASSIGNED
│        "properties": {...},
│        "score_breakdown": {
│          "rrf_score": 0.0167,
│          "source": "graph",  ← ALSO IN BREAKDOWN
│          "rank": 1
│        }
│      }
│
├─ Item 2: {source: "vector", payload: {text: "...", ...}}
│  │
│  └─→ Format as citation:
│      {
│        "node_type": "DocumentChunk",
│        "retrieval_score": 0.87,
│        "hop_distance": "vector",
│        "snippet": "...",
│        "source": "vector",  ← ASSIGNED
│        "properties": {...},
│        "score_breakdown": {
│          "vector_similarity": 0.87,
│          "rrf_score": 0.0159,
│          "source": "vector",  ← ALSO IN BREAKDOWN
│          "rank": 2
│        }
│      }
│
└─ ... more items ...

Output: Sorted list of MemoryCitation objects
         (Top 10 by retrieval_score)
         Each with explicit source field
```

## 3. Frontend Component Architecture

```
ChatPage
└─ CitationCard Component
   ├─ Props: { c: MemoryCitation, i: number }
   │
   ├─ Extract values:
   │  ├─ c.node_type → "Fact"
   │  ├─ c.source → "graph" (NEW!)
   │  └─ c.retrieval_score → 0.95
   │
   ├─ Compute styles:
   │  ├─ NODE_COLORS[c.node_type] → 'bg-indigo-500/15 ...'
   │  ├─ sourceColor mapping:
   │  │  ├─ "graph" → 'bg-purple-500/20 ...'
   │  │  ├─ "vector" → 'bg-cyan-500/20 ...'
   │  │  └─ else → 'bg-indigo-500/20 ...'
   │  └─ sourceLabel mapping:
   │     ├─ "graph" → "Graph"
   │     ├─ "vector" → "Vector DB"
   │     └─ else → "Hybrid"
   │
   ├─ Render header button:
   │  ├─ <span> #{i+1} </span>
   │  ├─ <span className={cls}> {c.node_type} </span>
   │  ├─ <span className={sourceColor}> {sourceLabel} </span>  ← NEW!
   │  ├─ <span> {c.snippet} </span>
   │  ├─ <div> {retrieval_score}% </div>
   │  └─ {hop_distance}
   │
   └─ [Optional] Expandable details section
```

## 4. Source Color Mapping

```
Citation received from backend
        │
        ├─ source: "graph"
        │  │
        │  └─→ sourceColor = 'bg-purple-500/20 text-purple-300 border-purple-500/30'
        │      sourceLabel = "Graph"
        │      │
        │      └─→ Render:
        │          ┌─────────────────────┐
        │          │ Graph               │  Purple badge
        │          │ (Semantic meaning)  │  Indicates: Knowledge Graph
        │          └─────────────────────┘
        │
        ├─ source: "vector"
        │  │
        │  └─→ sourceColor = 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
        │      sourceLabel = "Vector DB"
        │      │
        │      └─→ Render:
        │          ┌─────────────────────┐
        │          │ Vector DB           │  Cyan badge
        │          │ (Semantic meaning)  │  Indicates: Vector Database
        │          └─────────────────────┘
        │
        └─ source: undefined | "hybrid" | other
           │
           └─→ sourceColor = 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30'
               sourceLabel = "Hybrid"
               │
               └─→ Render:
                   ┌─────────────────────┐
                   │ Hybrid              │  Indigo badge
                   │ (Semantic meaning)  │  Indicates: Unknown/Mixed
                   └─────────────────────┘
```

## 5. Request-Response Cycle

```
User Input
    │
    └─→ POST /chat
        {
          "user_id": "user123",
          "message": "How much have I invested?"
        }
        │
        ▼
RetrievalOrchestrator.retrieve_and_answer()
        │
        ├─→ Graph Retrieval (nodes with graph source)
        ├─→ Vector Retrieval (chunks with vector source)
        ├─→ RRF Fusion (preserves source info)
        └─→ Citation Formatting (ASSIGNS source field)
        │
        ▼
ChatResponse
{
  "intent": "QUESTION",
  "answer": "You invested ₹50,000 this month",
  "memory_citations": [
    {
      "node_type": "Transaction",
      "retrieval_score": 0.95,
      "hop_distance": 1,
      "snippet": "HDFC investment ₹10,000",
      "source": "graph",  ← GRAPH SOURCE
      ...
    },
    {
      "node_type": "DocumentChunk",
      "retrieval_score": 0.87,
      "hop_distance": "vector",
      "snippet": "Monthly investment summary...",
      "source": "vector",  ← VECTOR SOURCE
      ...
    }
  ],
  "retrieval_metrics": {...}
}
        │
        ▼
Frontend CitationCard Component
        │
        ├─→ Extract source from each citation
        ├─→ Map source to (color, label)
        └─→ Render badge
        │
        ▼
User sees:
Citation | Graph | "HDFC investment..." | 95%
Citation | Vector DB | "Monthly summary..." | 87%
         ↑ (NEW! Source badge)
```

## 6. Source Assignment Logic

```
In _format_memory_citations():

for item in fused_results:
    if item.get("source") == "graph":
        ┌─────────────────────────────────────┐
        │ Graph Node Citation                 │
        ├─────────────────────────────────────┤
        │ node = item["payload"]              │
        │ citation = {                        │
        │   "node_type": node["type"],        │
        │   "retrieval_score": score,         │
        │   "hop_distance": hop_distance,     │
        │   "snippet": snippet,               │
        │   "source": "graph",  ← ASSIGNED   │
        │   "properties": {...},              │
        │   "score_breakdown": {...}          │
        │ }                                   │
        └─────────────────────────────────────┘
    
    elif item.get("source") == "vector":
        ┌─────────────────────────────────────┐
        │ Vector Chunk Citation               │
        ├─────────────────────────────────────┤
        │ chunk = item["payload"]             │
        │ citation = {                        │
        │   "node_type": "DocumentChunk",     │
        │   "retrieval_score": ...,           │
        │   "hop_distance": "vector",         │
        │   "snippet": chunk_text,            │
        │   "source": "vector",  ← ASSIGNED  │
        │   "properties": {...},              │
        │   "score_breakdown": {...}          │
        │ }                                   │
        └─────────────────────────────────────┘
```

## 7. Backward Compatibility

```
Old Citation (without source field)
{
  "node_type": "Fact",
  "retrieval_score": 0.95,
  "snippet": "Some fact"
  # Missing: "source" field
}
        │
        ▼
Frontend receives citation
        │
        ├─ Try to read: c.source
        ├─ Result: undefined
        │
        └─→ Use conditional logic:
            sourceColor = c.source === 'graph' ? purple : 
                         c.source === 'vector' ? cyan :
                         indigo  ← DEFAULT (matches undefined)
            
            sourceLabel = c.source === 'graph' ? 'Graph' :
                         c.source === 'vector' ? 'Vector DB' :
                         'Hybrid'  ← DEFAULT (matches undefined)
        │
        ▼
Renders as: 
Citation | Hybrid | "Some fact" | 95%
                   ↑ Shows default "Hybrid" label
```

## 8. Component Integration

```
App Component
└─ ChatPage
   └─ CitationList
      └─ CitationCard[] (for each citation)
         ├─ Input: MemoryCitation { source: "graph" | "vector" }
         ├─ Compute: sourceColor, sourceLabel
         └─ Render:
            ┌──────────────────────────────────┐
            │ Header (Button)                  │
            │ ├─ Index badge                   │
            │ ├─ Type badge (colored)          │
            │ ├─ Source badge (colored) ← NEW! │
            │ ├─ Snippet text                  │
            │ ├─ Score bar                     │
            │ └─ Expand/collapse icon          │
            │                                  │
            │ Details Section (optional)       │
            │ ├─ Full snippet quote            │
            │ ├─ Properties display            │
            │ └─ Score breakdown               │
            └──────────────────────────────────┘
```

---

## Summary: Key Diagram Points

1. **Backend Sets Source:** Citation formatting explicitly assigns "graph" or "vector"
2. **Frontend Receives Source:** API response includes source in each citation
3. **Frontend Maps Source:** Source value maps to color and label
4. **Frontend Displays:** Source badge renders with appropriate styling
5. **Backward Compatible:** Undefined source defaults to "Hybrid"

---

**Diagram Type:** Architecture Flow
**Last Updated:** 2024
**Status:** ✅ Complete

