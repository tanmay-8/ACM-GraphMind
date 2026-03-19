# Code Changes Reference

## Change 1: Backend Model - `backend/api/models.py`

### Location: Line 53
### Added field to MemoryCitation class:

```python
source: str = Field(
    default="hybrid", 
    description="Source of the citation: 'graph', 'vector', or 'hybrid'.", 
    example="graph"
)
```

**Full class definition:**
```python
class MemoryCitation(BaseModel):
    """Memory citation with retrieval score for explainability"""
    node_type: str = Field(..., description="Type of cited graph node.", example="Fact")
    retrieval_score: float = Field(..., description="Final ranking score for the citation.", example=0.91)
    hop_distance: Any = Field(..., description="Shortest path hop distance from user context.", example=1)
    snippet: str = Field(..., description="Human-readable citation snippet.", example="Investment in HDFC Mutual Fund")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Raw node properties used for explainability.")
    score_breakdown: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional weighted score components: graph_distance, recency, confidence, reinforcement."
    )
    source: str = Field(default="hybrid", description="Source of the citation: 'graph', 'vector', or 'hybrid'.", example="graph")
```

---

## Change 2: Backend Orchestrator - `backend/services/orchestrator/retrieval_orchestrator.py`

### Method: `_format_memory_citations()`
### Changes to graph citation formatting (Line 155):

**ADDED:**
```python
"source": "graph",
```

**Graph citation object (complete):**
```python
citation = {
    "node_type": node_type,
    "retrieval_score": score,
    "hop_distance": hop_distance,
    "snippet": snippet,
    "source": "graph",  # ← ADDED
    "properties": {},
    "score_breakdown": {
        **(node.get("score_breakdown", {}) or {}),
        "rrf_score": item.get("fusion_score", 0.0),
        "source": "graph",
        "rank": item.get("rank")
    }
}
```

### Vector citation formatting (Line 196):

**ADDED:**
```python
"source": "vector",
```

**Vector citation object (complete):**
```python
citations.append(
    {
        "node_type": "DocumentChunk",
        "retrieval_score": chunk.get("retrieval_score", chunk.get("similarity", 0.0)),
        "hop_distance": "vector",
        "snippet": chunk.get("text", "")[:120],
        "source": "vector",  # ← ADDED
        "properties": {
            "chunk_id": chunk.get("id"),
            "similarity": chunk.get("similarity", 0.0),
            "source": "vector"
        },
        "score_breakdown": {
            "vector_similarity": chunk.get("similarity", 0.0),
            "rrf_score": item.get("fusion_score", 0.0),
            "source": "vector",
            "rank": item.get("rank")
        }
    }
)
```

---

## Change 3: Frontend CitationCard - `frontend/src/pages/Chat.tsx`

### Location: Lines 60-81 (CitationCard function)

### Added code for source badge styling:

```typescript
// Determine source badge color and label
const sourceColor = c.source === 'graph' 
  ? 'bg-purple-500/20 text-purple-300 border-purple-500/30' 
  : c.source === 'vector' 
  ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
  : 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30';

const sourceLabel = c.source === 'graph' 
  ? 'Graph' 
  : c.source === 'vector' 
  ? 'Vector DB' 
  : 'Hybrid';
```

### Added JSX element in citation header:

```jsx
<span className={`px-1.5 py-0.5 rounded-md border text-[10px] font-semibold flex-shrink-0 ${sourceColor}`}>
  {sourceLabel}
</span>
```

**Full CitationCard header:**
```jsx
<button onClick={() => setOpen(v => !v)}
  className="w-full flex items-center gap-2 px-3 py-2 bg-white/[0.02] hover:bg-white/[0.04] transition-colors text-left">
  <span className="text-white/20 w-4 text-right flex-shrink-0">{i + 1}</span>
  <span className={`px-1.5 py-0.5 rounded-md border text-[10px] font-semibold flex-shrink-0 ${cls}`}>{c.node_type}</span>
  <span className={`px-1.5 py-0.5 rounded-md border text-[10px] font-semibold flex-shrink-0 ${sourceColor}`}>{sourceLabel}</span>
  <span className="flex-1 truncate text-white/50">{c.snippet || '—'}</span>
  <div className="flex items-center gap-1.5 flex-shrink-0">
    <div className="w-14 h-1 bg-white/10 rounded-full overflow-hidden">
      <div className="h-full bg-indigo-400/70 rounded-full" style={{ width: `${pct}%` }} />
    </div>
    <span className="text-white/30 w-7 text-right">{pct}%</span>
  </div>
  <span className="text-white/25 flex-shrink-0 ml-1 text-[10px]">
    {c.hop_distance !== 'N/A' ? `${c.hop_distance}-hop` : 'direct'}
  </span>
  <svg className={`w-3 h-3 text-white/25 flex-shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
    fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
    <path d="M6 9l6 6 6-6" />
  </svg>
</button>
```

---

## Summary of Changes

### Total Files Modified: 3
- `backend/api/models.py` - 1 line added
- `backend/services/orchestrator/retrieval_orchestrator.py` - 2 lines added (plus source field in citations)
- `frontend/src/pages/Chat.tsx` - ~15 lines added (source badge logic and UI)

### Total New Lines: ~18 lines
### Breaking Changes: None
### Backward Compatibility: Maintained via default value

---

## Validation Checklist

- [x] Model updated with source field
- [x] Backend properly sets source for graph citations
- [x] Backend properly sets source for vector citations
- [x] Frontend receives source in response
- [x] Frontend applies correct color based on source
- [x] Frontend displays correct label based on source
- [x] Default value ensures backward compatibility
- [x] No breaking changes to API
- [x] Type safety maintained
- [x] All changes are production-ready

