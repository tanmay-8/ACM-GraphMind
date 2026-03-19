# Source Tracking Implementation Summary

## Overview
Implemented comprehensive source tracking throughout the retrieval pipeline to show users whether citations come from the Knowledge Graph, Vector Database, or both (Hybrid).

## Changes Made

### 1. Backend Model Updates
**File:** `backend/api/models.py`

Added `source` field to the `MemoryCitation` model:
```python
source: str = Field(
    default="hybrid",
    description="Source of the citation: 'graph', 'vector', or 'hybrid'.",
    example="graph"
)
```

**Purpose:** Provides explicit information about which retrieval system provided each citation.

### 2. Backend Orchestration Updates
**File:** `backend/services/orchestrator/retrieval_orchestrator.py`

Updated the `_format_memory_citations()` method to include source information in citations:

#### For Graph Citations:
```python
citation = {
    "node_type": node_type,
    "retrieval_score": score,
    "hop_distance": hop_distance,
    "snippet": snippet,
    "source": "graph",  # ← Explicit source indicator
    "properties": {...},
    "score_breakdown": {...}
}
```

#### For Vector/Document Chunk Citations:
```python
citations.append({
    "node_type": "DocumentChunk",
    "retrieval_score": ...,
    "hop_distance": "vector",
    "snippet": ...,
    "source": "vector",  # ← Explicit source indicator
    "properties": {...},
    "score_breakdown": {...}
})
```

**Implementation Details:**
- Graph citations get `source: "graph"`
- Vector DB citations get `source: "vector"`
- The RRF fusion process preserves source information from the fused results
- Citations sorted by retrieval_score, top 10 returned

### 3. Frontend UI Updates
**File:** `frontend/src/pages/Chat.tsx`

#### Citation Card Component Enhancement:

1. **Color-Coded Source Badges:**
   - Graph sources: Purple (`bg-purple-500/20 text-purple-300`)
   - Vector DB sources: Cyan (`bg-cyan-500/20 text-cyan-300`)
   - Hybrid sources: Indigo (fallback)

2. **Dynamic Source Display:**
   ```typescript
   const sourceLabel = c.source === 'graph' 
     ? 'Graph' 
     : c.source === 'vector' 
     ? 'Vector DB' 
     : 'Hybrid';
   ```

3. **UI Layout:**
   - Source badge displays next to node type badge
   - Maintains consistent spacing and visual hierarchy
   - Uses the same badge styling as node type for consistency

## Data Flow

```
User Query
    ↓
RetrievalOrchestrator.retrieve_and_answer()
    ├─ Graph Retrieval (retrieval.py)
    │   └─ Returns nodes with type info
    ├─ Vector Retrieval (vector/retrieval.py)
    │   └─ Returns document chunks
    ├─ RRF Fusion (_fuse_rrf)
    │   └─ Preserves source: "graph" | "vector"
    └─ Format Citations (_format_memory_citations)
        └─ Creates MemoryCitation objects with source field
        └─ Returns citations to API
            ↓
        ChatResponse (includes memory_citations)
            ↓
        Frontend receives citations with source info
            ├─ Graph citations → Purple badge "Graph"
            ├─ Vector citations → Cyan badge "Vector DB"
            └─ Hybrid citations → Indigo badge "Hybrid"
```

## API Contract

### ChatResponse Model
```python
class ChatResponse(BaseModel):
    intent: IntentType
    answer: Optional[str] = None
    memory_storage: Optional[MemoryStorageResult] = None
    retrieval_metrics: Optional[RetrievalMetrics] = None
    memory_citations: Optional[List[MemoryCitation]] = None  # ← Includes source
    message: str
```

### Example Citation JSON
```json
{
  "node_type": "Fact",
  "retrieval_score": 0.91,
  "hop_distance": 1,
  "snippet": "Investment in HDFC Mutual Fund",
  "source": "graph",
  "properties": {
    "text": "Investment in HDFC Mutual Fund",
    "confidence": 0.95,
    "reinforcement_count": 2
  },
  "score_breakdown": {
    "hop_distance": 1,
    "recency": 0.8,
    "confidence": 0.95,
    "reinforcement": 1.2,
    "rrf_score": 0.0168,
    "source": "graph",
    "rank": 1
  }
}
```

## Frontend Styling

### Source Badge CSS Classes
```css
/* Graph Sources */
bg-purple-500/20 text-purple-300 border-purple-500/30

/* Vector DB Sources */
bg-cyan-500/20 text-cyan-300 border-cyan-500/30

/* Hybrid Sources */
bg-indigo-500/20 text-indigo-300 border-indigo-500/30
```

### Citation Card Structure
```
┌─────────────────────────────────────────────────────────┐
│ ① TypeBadge | SourceBadge | Snippet... | Score | Hops ↕ │
├─────────────────────────────────────────────────────────┤
│ [Expanded Details when clicked]                         │
└─────────────────────────────────────────────────────────┘
```

## Testing Recommendations

1. **Graph-Only Queries:** Verify "Graph" badge appears for graph-sourced citations
2. **Vector-Only Queries:** Verify "Vector DB" badge appears for document citations
3. **Hybrid Queries:** Verify mixed citations show appropriate source badges
4. **Visual Consistency:** Confirm badge colors and styling match design system
5. **Responsiveness:** Test badge layout on various screen sizes

## Future Enhancements

- [ ] Filter citations by source (Graph/Vector DB/All)
- [ ] Analytics dashboard showing source distribution
- [ ] Confidence scores based on source reliability
- [ ] Toggle to hide certain sources for focused answers
- [ ] Weighted scoring based on source type

## Files Modified

1. `backend/api/models.py` - Added `source` field to MemoryCitation
2. `backend/services/orchestrator/retrieval_orchestrator.py` - Updated citation formatting
3. `frontend/src/pages/Chat.tsx` - Enhanced CitationCard UI component

## Backwards Compatibility

The `source` field includes a default value of `"hybrid"`, ensuring backward compatibility with existing code that may not explicitly set the source.

