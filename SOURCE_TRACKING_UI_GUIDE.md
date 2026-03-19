# Source Tracking UI Guide

## Citation Card Source Display

### Before Implementation
```
┌────────────────────────────────────────────────────────────┐
│ 1 | Fact | "Investment in HDFC Mutual Fund..." | 91% | 1-hop ↕ │
└────────────────────────────────────────────────────────────┘
```

### After Implementation
```
┌────────────────────────────────────────────────────────────┐
│ 1 | Fact | Graph | "Investment in HDFC..." | 91% | 1-hop ↕ │
└────────────────────────────────────────────────────────────┘
                    ↑
                Source Badge
```

## Source Badge Colors & Meanings

### Graph Source
```
┌──────────┐
│  Graph   │  Purple badge
└──────────┘  bg-purple-500/20
              text-purple-300
              border-purple-500/30

Indicates: Citation from Knowledge Graph
          (Nodes: Fact, Transaction, Asset, Goal, Entity)
```

### Vector Database Source
```
┌────────────┐
│ Vector DB  │  Cyan badge
└────────────┘  bg-cyan-500/20
                text-cyan-300
                border-cyan-500/30

Indicates: Citation from Vector Database
          (Document chunks retrieved via similarity search)
```

### Hybrid Source (Fallback)
```
┌────────┐
│ Hybrid │  Indigo badge
└────────┘  bg-indigo-500/20
            text-indigo-300
            border-indigo-500/30

Indicates: Source ambiguous or combined sources
```

## Citation Card Component Structure

```typescript
CitationCard Component
├─ Header (collapsible)
│  ├─ Number Badge (#1, #2, etc.)
│  ├─ Node Type Badge (Fact, Transaction, etc.)
│  ├─ Source Badge (Graph, Vector DB, Hybrid)  ← NEW
│  ├─ Snippet Text (truncated)
│  ├─ Relevance Score (0-100%)
│  ├─ Hop Distance / Retrieval Method
│  └─ Expand/Collapse Button
└─ Details (when expanded)
   ├─ Full Snippet Text
   ├─ Properties Display
   │  ├─ Text / Name
   │  ├─ Confidence Score
   │  ├─ Reinforcement Count
   │  └─ Other metadata
   └─ Score Breakdown
      ├─ Graph Distance / Vector Similarity
      ├─ RRF Score
      ├─ Source
      └─ Ranking
```

## Backend Citation Object Structure

```typescript
interface MemoryCitation {
  // Core Information
  node_type: string;           // "Fact", "Transaction", "Asset", etc.
  retrieval_score: number;     // 0.0-1.0 relevance score
  hop_distance: number | string; // Graph: 1, 2, 3... | Vector: "vector"
  snippet: string;             // Human-readable excerpt
  
  // SOURCE FIELD (NEW)
  source: "graph" | "vector" | "hybrid"; // Where citation came from
  
  // Additional Information
  properties: {
    [key: string]: any;       // Node-specific properties
  };
  
  score_breakdown?: {
    hop_distance?: number;
    recency?: number;
    confidence?: number;
    reinforcement?: number;
    rrf_score: number;        // Reciprocal rank fusion score
    source: "graph" | "vector"; // Same as top-level source
    rank?: number;            // Original rank in fused results
  };
}
```

## Frontend Citation Object (TypeScript)

```typescript
interface MemoryCitation {
  node_type: string;
  retrieval_score: number;
  hop_distance: string | number;
  snippet: string;
  source?: string;           // Optional for backwards compatibility
  properties: Record<string, any>;
  score_breakdown?: Record<string, any>;
}
```

## Color Mapping Logic

```typescript
const NODE_COLORS: Record<string, string> = {
  'Fact': 'bg-indigo-500/15 text-indigo-400 border-indigo-500/20',
  'Transaction': 'bg-green-500/15 text-green-400 border-green-500/20',
  'Asset': 'bg-blue-500/15 text-blue-400 border-blue-500/20',
  'Goal': 'bg-orange-500/15 text-orange-400 border-orange-500/20',
  'Entity': 'bg-pink-500/15 text-pink-400 border-pink-500/20',
  'DocumentChunk': 'bg-cyan-500/15 text-cyan-400 border-cyan-500/20',
  // ... default fallback
};

const SOURCE_COLORS: Record<string, string> = {
  'graph': 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  'vector': 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  'hybrid': 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
};

const SOURCE_LABELS: Record<string, string> = {
  'graph': 'Graph',
  'vector': 'Vector DB',
  'hybrid': 'Hybrid',
};
```

## User Experience Flow

### Step 1: Query Execution
```
User: "How much have I invested this month?"
         ↓
Retrieval Engine processes query
```

### Step 2: Dual Retrieval
```
Graph Retrieval              Vector Retrieval
├─ Transaction nodes    └─ Document chunks
├─ Related facts            indexed by similarity
└─ Entity relationships
```

### Step 3: RRF Fusion
```
Results fused with source tracking:
[
  { source: "graph", payload: {...} },
  { source: "vector", payload: {...} },
  { source: "graph", payload: {...} },
]
```

### Step 4: Citation Formatting
```
Each citation augmented with source field:
{
  node_type: "Transaction",
  source: "graph",           ← ✓ SET
  retrieval_score: 0.92,
  snippet: "HDFC Mutual Fund investment of ₹10,000 on 2024-01-15",
  ...
}
```

### Step 5: Frontend Display
```
Citation Card renders:
┌──────────────────────────────────────────────────┐
│ 1 | Transaction | Graph | "HDFC Mutual Fund..." │
└──────────────────────────────────────────────────┘
```

## Implementation Checklist

- [x] Backend: Add `source` field to MemoryCitation model
- [x] Backend: Set source in _format_memory_citations() method
- [x] Frontend: Accept source field in MemoryCitation interface
- [x] Frontend: Extract source values for badge display
- [x] Frontend: Add color-coded source badges to CitationCard
- [x] Frontend: Display source label ("Graph", "Vector DB", "Hybrid")
- [x] Testing: Verify graph citations show "Graph" badge
- [x] Testing: Verify vector citations show "Vector DB" badge
- [x] Documentation: Created implementation summary
- [x] Documentation: Created UI guide

## Quick Reference

| Source | Badge Color | Backend Value | Frontend Display |
|--------|-------------|---------------|------------------|
| Graph DB | Purple | `"graph"` | "Graph" |
| Vector DB | Cyan | `"vector"` | "Vector DB" |
| Hybrid/Unknown | Indigo | `"hybrid"` | "Hybrid" |

## Notes

- The `source` field in the backend is set explicitly during citation formatting
- The RRF fusion process preserves source information from original results
- Frontend gracefully handles missing source field (defaults to "Hybrid")
- Color scheme maintains visual consistency with existing node type badges
- All changes are backward compatible

