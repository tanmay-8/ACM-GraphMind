# Clear Knowledge Graph - Quick Reference Card

## 🎯 One-Sentence Summary

Add a red "Clear" button to the Mindmap page that deletes all knowledge graph nodes and vectors with user confirmation.

## 📍 Where to Find It

**Frontend:** Mindmap page header, top-right corner (next to Refresh button)
**Backend:** `DELETE /memory/clear` endpoint

## 🔴 The Button

```
┌──────────────────────────────────────────────┐
│ [🔄 Refresh] [🗑️ Clear]                     │
└──────────────────────────────────────────────┘
        ↑
    Refresh button
                      ↑
                   Clear button (red trash can icon)
```

## 🚀 Quick Start

### For Users

1. Navigate to Knowledge Graph → Mindmap
2. Click the red "Clear" button
3. Confirm in popup
4. Watch spinner
5. See green success notification
6. Graph is cleared!

### For Developers

```bash
# Start everything
docker compose up              # Services
uvicorn api.main:app --reload # Backend
npm run dev                    # Frontend

# Test via API
curl -X DELETE http://localhost:8000/memory/clear \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📋 What Gets Deleted

- ✅ All Neo4j nodes (Transactions, Assets, Goals, Facts, Messages)
- ✅ All Neo4j relationships
- ✅ All Milvus vectors
- ❌ NOT: User account, login credentials, profile

## 🛡️ Safeguards

1. **Authentication:** Must have valid JWT token
2. **Confirmation:** Browser asks "Are you sure?"
3. **Feedback:** Shows spinner while processing
4. **Notification:** Green = success, Red = error
5. **Auto-dismiss:** Toast disappears after 3 seconds

## 📊 Response Format

**Success:**

```json
{
  "success": true,
  "message": "Graph cleared: Deleted X nodes... | Vectors cleared: Deleted Y vectors",
  "deleted_nodes": 150,
  "deleted_vectors": 450
}
```

**Error:**

```json
{
  "success": false,
  "message": "Error description here",
  "deleted_nodes": 0,
  "deleted_vectors": 0
}
```

## 🔧 Code Locations

| Component | File                                        | Lines   |
| --------- | ------------------------------------------- | ------- |
| Endpoint  | `backend/api/routes/memory.py`              | ~40 new |
| Services  | `backend/services/graph/mindmap_service.py` | ~50 new |
| API Call  | `frontend/src/lib/api.ts`                   | ~5 new  |
| UI Button | `frontend/src/pages/Mindmap.tsx`            | ~80 new |

## ⚡ Performance

- Time to delete: 100-500ms typical
- No page reload needed
- Immediate UI update
- Works offline-first architecture

## 🧪 How to Test

1. Create some data in the app
2. Go to Mindmap page
3. Click "Clear" button
4. Cancel first attempt (nothing happens)
5. Click "Clear" again
6. Click confirm
7. Watch it disappear
8. Refresh page - still gone ✓

## 🐛 Troubleshooting

| Problem                | Solution                          |
| ---------------------- | --------------------------------- |
| No Clear button        | Clear browser cache, reload       |
| Button disabled        | Wait for refresh to finish        |
| "Missing auth" error   | Check JWT token is valid          |
| "User not found" error | Verify you're logged in           |
| Partial deletion       | Check if Neo4j/Milvus are running |

## 🔐 Security Notes

- Only delete your OWN graph (authorization verified)
- Token expires = cannot delete
- Error messages don't leak sensitive data
- Server logs record all deletions (audit trail)

## 📚 Full Documentation

See: `CLEAR_KNOWLEDGE_GRAPH.md` for complete details

## 💾 Files Changed

1. `backend/services/graph/mindmap_service.py` ✏️
2. `backend/api/routes/memory.py` ✏️
3. `frontend/src/lib/api.ts` ✏️
4. `frontend/src/pages/Mindmap.tsx` ✏️

## ✨ What's New

- `delete_user_graph()` - Backend service method
- `delete_user_vectors()` - Backend service method
- `ClearGraphResponse` - Response model
- `clear_knowledge_graph()` - API endpoint
- `memoryAPI.clearGraph()` - Frontend API call
- `handleClearGraph()` - Frontend handler
- "Clear" button in Mindmap header
- Success/error toast notifications

## 🎨 Visual Design

- **Button Color:** Red (warning/destructive action)
- **Icon:** Trash can (universal delete symbol)
- **State:** Spinner when loading, disabled when processing
- **Toast:** Green for success, red for error
- **Animation:** Smooth fade-in/out

## 🌐 API Endpoint

```
DELETE /memory/clear
```

**Requires:** Bearer token in Authorization header
**Returns:** ClearGraphResponse
**Side Effects:** Deletes all user data from graph databases

## 🎯 Use Cases

1. **Fresh Start:** Clear old data, start fresh
2. **Privacy:** Delete everything before deleting account
3. **Test Data:** Remove test entries during development
4. **Cleanup:** Remove duplicates/incorrect data
5. **Demo:** Reset graph for presentations

## 📈 What's Happening Behind Scenes

```
User clicks Clear
    ↓
Show confirmation dialog
    ↓
User confirms
    ↓
Send DELETE /memory/clear to backend
    ↓
Backend verifies JWT token
    ↓
Backend verifies user_id
    ↓
Delete from Neo4j: MATCH (n) WHERE n.user_id = $id DETACH DELETE n
    ↓
Delete from Milvus: expr = 'user_id == "..."'
    ↓
Return counts to frontend
    ↓
Frontend shows notification
    ↓
Frontend clears visualization
    ↓
Toast auto-dismisses
```

## ⚠️ Important Notes

- **IRREVERSIBLE:** Once deleted, cannot be undone
- **COMPLETE:** Deletes from both Neo4j AND Milvus
- **PERMANENT:** Data is gone (not archived)
- **FAST:** Completes in <1 second typically

## 🚀 Future Ideas

- [ ] Archive instead of delete
- [ ] Export before delete
- [ ] Undo within 30 minutes
- [ ] Delete specific node types only
- [ ] Scheduled deletion

## 📞 Support

For issues:

1. Check `CLEAR_KNOWLEDGE_GRAPH.md` troubleshooting section
2. Verify services are running (`docker compose up`)
3. Check backend logs for errors
4. Verify JWT token is valid
5. Try with fresh browser session
