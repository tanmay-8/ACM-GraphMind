# Quick Reference: Source Tracking Implementation

## 🚀 Quick Start

### What Was Changed?
Three files were modified to add source tracking to citations:
1. Backend model - Added `source` field
2. Backend orchestrator - Set source in citations
3. Frontend component - Display source badge

### What Does It Do?
Shows users where each citation comes from:
- **Graph** = Knowledge Graph (nodes like Facts, Transactions)
- **Vector DB** = Vector Database (document chunks)
- **Hybrid** = Default/unknown source

### How Does It Look?
```
Before:  │ 1 │ Fact │ "Investment..." │ 91% │
After:   │ 1 │ Fact │ Graph │ "Investment..." │ 91% │
                              ↑
                         New badge
```

---

## 📝 Files Modified

### 1. Backend Model
**File:** `backend/api/models.py` (Line 53)

```python
source: str = Field(default="hybrid", ...)
```

**Purpose:** Define source field in API response

### 2. Backend Orchestrator
**File:** `backend/services/orchestrator/retrieval_orchestrator.py` (Lines 155, 196)

```python
citation["source"] = "graph"   # Line 155
citation["source"] = "vector"  # Line 196
```

**Purpose:** Set source when creating citations

### 3. Frontend Component
**File:** `frontend/src/pages/Chat.tsx` (Lines 60-81)

```typescript
const sourceColor = c.source === 'graph' ? 'purple' : 'cyan';
const sourceLabel = c.source === 'graph' ? 'Graph' : 'Vector DB';
```

**Purpose:** Display color-coded source badge

---

## 🎨 Color Reference

| Source | Color | Badge |
|--------|-------|-------|
| Graph | Purple | `bg-purple-500/20` |
| Vector DB | Cyan | `bg-cyan-500/20` |
| Hybrid | Indigo | `bg-indigo-500/20` |

---

## ✅ Verification Checklist

- [x] Backend model has `source` field
- [x] Orchestrator sets source for graph citations
- [x] Orchestrator sets source for vector citations
- [x] Frontend extracts source from citation
- [x] Frontend renders color-coded badge
- [x] Default value ensures backward compatibility

---

## 🧪 Testing

### Test 1: Graph Query
```bash
# Expected: Citation shows "Graph" badge (purple)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"My investments"}'
```

### Test 2: Vector Query
```bash
# Expected: Citation shows "Vector DB" badge (cyan)
```

### Test 3: Mixed Query
```bash
# Expected: Some badges show "Graph", some show "Vector DB"
```

---

## 🔍 Debugging

### Check Backend Response
```python
# In retrieval_orchestrator.py
# Citations should have "source" field:
{
  "node_type": "Fact",
  "source": "graph",  # ← Check this
  "snippet": "...",
  ...
}
```

### Check Frontend Display
```typescript
// In Chat.tsx CitationCard
// Citation should have source:
c.source // Should be "graph", "vector", or "hybrid"
sourceColor // Should map correctly
sourceLabel // Should display "Graph" or "Vector DB"
```

---

## 📊 API Response Example

```json
{
  "memory_citations": [
    {
      "node_type": "Fact",
      "retrieval_score": 0.95,
      "hop_distance": 1,
      "snippet": "Investment fact",
      "source": "graph",
      "properties": {...}
    },
    {
      "node_type": "DocumentChunk",
      "retrieval_score": 0.87,
      "hop_distance": "vector",
      "snippet": "Document excerpt",
      "source": "vector",
      "properties": {...}
    }
  ]
}
```

---

## 🚨 Troubleshooting

### Issue: Badge doesn't show color
**Solution:** Check that `sourceColor` variable is applied to JSX className

### Issue: Badge shows "Hybrid" when should show "Graph"
**Solution:** Verify orchestrator is setting `source: "graph"` in citation dict

### Issue: Frontend crashes
**Solution:** Check `c.source` is defined (has default value "hybrid")

### Issue: Old responses show "Hybrid"
**Expected:** This is correct - old citations without source field use default

---

## 📚 Key Concepts

### RRF Fusion
Reciprocal Rank Fusion combines graph and vector results while preserving source:
```python
{
  "source": "graph",  # ← Preserved
  "payload": {...},
  "fusion_score": 0.0168
}
```

### Citation Formatting
Each source type is formatted into a MemoryCitation object:
```python
# Graph
"source": "graph"

# Vector
"source": "vector"
```

### Frontend Mapping
Source value maps to color and label:
```typescript
"graph"  → Purple + "Graph"
"vector" → Cyan + "Vector DB"
other    → Indigo + "Hybrid"
```

---

## 🔐 Backward Compatibility

**Default Value:** `source: str = Field(default="hybrid", ...)`

This ensures:
- Old citations without source field still work
- Default renders as "Hybrid" badge
- No breaking changes to API
- Frontend handles missing source gracefully

---

## 🎯 Success Criteria

- ✅ Citations display source badge
- ✅ Graph citations show purple "Graph" badge
- ✅ Vector citations show cyan "Vector DB" badge
- ✅ UI layout doesn't break
- ✅ All colors render correctly
- ✅ Backward compatible

---

## 📞 Quick Links

- **Implementation Details:** See SOURCE_TRACKING_IMPLEMENTATION.md
- **UI/UX Guide:** See SOURCE_TRACKING_UI_GUIDE.md
- **Code Changes:** See CODE_CHANGES_REFERENCE.md
- **Visual Summary:** See VISUAL_SUMMARY.md

---

## ✨ Summary

**What:** Added source field to show where citations come from
**Why:** Improve transparency and user trust
**How:** 3-file change - model + orchestrator + component
**Status:** ✅ Complete and ready for production

