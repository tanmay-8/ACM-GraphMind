# 🧠 GraphMind - Financial Graph Memory Assistant

> An intelligent financial memory assistant using PostgreSQL for user data and Neo4j for knowledge graphs, with production-grade multi-hop retrieval.

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Neo4j](https://img.shields.io/badge/Neo4j-008CC1?style=for-the-badge&logo=neo4j&logoColor=white)](https://neo4j.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

---

## 🎯 What It Does

GraphMind stores your financial conversations and facts in a knowledge graph, then retrieves relevant context to answer your questions with explainable citations.

**Example:**
```
You: "I invested $50,000 in HDFC Mutual Fund last month"
GraphMind: ✓ Stored in knowledge graph

You: "How much is my investment?"
GraphMind: "Based on your records, you invested $50,000 in HDFC Mutual Fund"
[Citations: Transaction #123, Asset: HDFC MF, hop distance: 2]
```

---

## ✨ Key Features

- **Dual Database**: PostgreSQL (users, chat history) + Neo4j (knowledge graph)
- **Smart Retrieval**: Mode-based queries (direct lookup, aggregation, relational reasoning)
- **Chat Persistence**: Full conversation history with metrics and citations
- **User Authentication**: JWT tokens with bcrypt password hashing
- **Explainable AI**: Every answer includes source citations and hop distances
- **Production-Ready**: Docker Compose, connection pooling, error handling

---

## 🏗️ Architecture

```
┌─────────────┐
│   React     │ (TypeScript + Vite)
│  Frontend   │
└──────┬──────┘
       │ REST API
       ▼
┌─────────────┐
│   FastAPI   │ (Python 3.10)
│   Backend   │
└──────┬──────┘
       │
   ┌───┴────────────────┐
   ▼                    ▼
┌──────────┐      ┌──────────┐
│PostgreSQL│      │  Neo4j   │
│ (Users,  │      │ (Facts,  │
│  Chat)   │      │  Graph)  │
└──────────┘      └──────────┘
```

**Data Flow:**
1. User sends message → FastAPI authenticates (JWT)
2. Save user message to PostgreSQL
3. Classify intent (MEMORY/QUESTION/BOTH)
4. **MEMORY**: Extract facts → Store in Neo4j graph
5. **QUESTION**: Retrieve from Neo4j → Generate answer (Gemini)
6. Save assistant response with metadata to PostgreSQL

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose

### 1. Clone & Setup Environment

```bash
git clone <repo-url>
cd graphmind

# Setup backend .env
cd backend
cp .env.example .env
# Add your GEMINI_API_KEY
```

### 2. Start Databases

```bash
cd /home/tanmay08/graphmind
docker compose up -d

# Verify services
docker compose ps
```

### 3. Install Dependencies

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 4. Run Application

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8001

# Terminal 2: Frontend
cd frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001/docs

---

## 🗂️ Project Structure

```
graphmind/
├── backend/
│   ├── api/
│   │   ├── main.py                    # FastAPI app
│   │   ├── models.py                  # Request/response models
│   │   └── routes/
│   │       ├── auth.py                # Signup, login, /me
│   │       └── chat.py                # Chat + history endpoints
│   ├── services/
│   │   ├── auth/
│   │   │   └── auth_service.py        # JWT, user management
│   │   ├── database/
│   │   │   ├── user_service.py        # PostgreSQL users
│   │   │   └── chat_service.py        # PostgreSQL chat history
│   │   ├── graph/
│   │   │   ├── ingest.py              # Neo4j memory storage
│   │   │   ├── retrieval.py           # Mode-based retrieval
│   │   │   ├── query_understanding.py # Intent classification
│   │   │   └── schema.cypher          # Graph schema
│   │   ├── llm/
│   │   │   └── intent_classifier.py   # MEMORY/QUESTION/BOTH
│   │   └── orchestrator/
│   │       ├── memory_orchestrator.py # Ingestion workflow
│   │       └── retrieval_orchestrator.py # Query workflow
│   ├── database/
│   │   ├── postgres.py                # Connection pooling
│   │   └── init.sql                   # PostgreSQL schema
│   ├── config/
│   │   └── settings.py                # Environment config
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Auth/                  # Login, Signup
│       │   └── Chat/                  # Chat interface
│       ├── contexts/
│       │   └── AuthContext.tsx        # Auth state management
│       └── services/
│           └── api.ts                 # Axios API client
│
├── docker-compose.yml                 # PostgreSQL + Neo4j
└── README.md
```

---

## 🔧 Tech Stack

**Frontend:** React 18, TypeScript, Vite, Axios  
**Backend:** FastAPI 0.109.0, Python 3.10, Uvicorn  
**Databases:**
- PostgreSQL 16 (users, chat_sessions, chat_messages)
- Neo4j 5.14.0 (knowledge graph with APOC)

**Authentication:** JWT (python-jose), bcrypt 4.1.2  
**LLM:** Google Gemini 1.5-flash  
**Infrastructure:** Docker Compose, psycopg2 connection pooling

---

## 🎯 Retrieval System

**Mode-Based Queries:**
- `DIRECT_LOOKUP`: Simple facts (depth 1) - "What's my balance?"
- `AGGREGATION`: Sum/count queries (depth 2) - "Total investments?"
- `RELATIONAL_REASONING`: Multi-hop (depth 3) - "Am I aligned with goals?"

**Scoring Algorithm:**
```
score = 0.4 × graph_relevance 
      + 0.3 × recency (exp decay)
      + 0.2 × confidence
      + 0.1 × reinforcement (log scale)
```

**Features:**
- No wildcard paths (prevents query explosion)
- Real hop distance calculation via `shortestPath()`
- Timeline filtering ("last month", "in 2024")
- Deferred reinforcement (updates after answer generation)

---

## 📡 API Endpoints

### Base URL

- Local (frontend default): `http://localhost:8001`
- FastAPI interactive docs: `/docs`
- OpenAPI schema: `/openapi.json`
- Standalone spec file: `docs/swagger.yaml`

### Authentication

Most endpoints require a JWT in the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

### Error Format

FastAPI errors follow this format:

```json
{
  "detail": "Error message"
}
```

---

### `GET /`

Root metadata endpoint.

Response:

```json
{
  "message": "Welcome to GraphMind API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health",
  "chat": "/chat"
}
```

### `GET /health`

Health check endpoint.

Response:

```json
{
  "status": "healthy",
  "message": "API is running"
}
```

---

## 🔐 Auth API

### `POST /auth/signup`

Create a new user and return an access token.

Request body:

```json
{
  "email": "user@example.com",
  "password": "secret123",
  "full_name": "Tanmay Sharma"
}
```

Validation:
- `email` must be a valid email.
- `password` minimum length is 6.
- `full_name` minimum length is 1.

Success response (`201`):

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user_id": "f4a2fca4-39d0-4028-8fb5-4f0b84b6c9d5",
  "email": "user@example.com",
  "full_name": "Tanmay Sharma"
}
```

Common errors:
- `400`: Email already registered

### `POST /auth/login`

Authenticate an existing user.

Request body:

```json
{
  "email": "user@example.com",
  "password": "secret123"
}
```

Success response (`200`):

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user_id": "f4a2fca4-39d0-4028-8fb5-4f0b84b6c9d5",
  "email": "user@example.com",
  "full_name": "Tanmay Sharma"
}
```

Common errors:
- `401`: Incorrect email or password

### `GET /auth/me`

Get the current authenticated user.

Headers:
- `Authorization: Bearer <token>`

Success response (`200`):

```json
{
  "user_id": "f4a2fca4-39d0-4028-8fb5-4f0b84b6c9d5",
  "email": "user@example.com",
  "full_name": "Tanmay Sharma",
  "created_at": "2026-03-17T06:30:10.323919"
}
```

Common errors:
- `401`: Missing/invalid/expired token
- `404`: User not found

---

## 💬 Chat API

### `POST /chat`

Unified endpoint for memory ingestion and question answering. Intent is auto-classified to one of:
- `MEMORY`
- `QUESTION`
- `BOTH`

Headers:
- `Authorization: Bearer <token>`

Request body:

```json
{
  "user_id": "f4a2fca4-39d0-4028-8fb5-4f0b84b6c9d5",
  "message": "I invested 50000 in HDFC Mutual Fund",
  "conversation_id": null
}
```

Response shape (`200`):

```json
{
  "intent": "MEMORY | QUESTION | BOTH",
  "answer": "optional assistant answer",
  "memory_storage": {
    "nodes_created": 0,
    "relationships_created": 0,
    "facts_created": 0,
    "chunks_indexed": 0
  },
  "retrieval_metrics": {
    "graph_query_ms": 0,
    "vector_search_ms": 0,
    "context_assembly_ms": 0,
    "retrieval_ms": 0,
    "llm_generation_ms": 0
  },
  "memory_citations": [
    {
      "node_type": "Fact",
      "retrieval_score": 0.91,
      "hop_distance": 1,
      "snippet": "Investment in HDFC Mutual Fund",
      "properties": {},
      "score_breakdown": {
        "graph_distance": 0.9,
        "recency": 0.8,
        "confidence": 0.9,
        "reinforcement": 0.7
      }
    }
  ],
  "message": "Status message"
}
```

Notes:
- `answer`, `memory_storage`, `retrieval_metrics`, and `memory_citations` are optional depending on classified intent.
- This endpoint also persists user and assistant messages to PostgreSQL sessions.

Common errors:
- `401`: Missing/invalid/expired token
- `404`: User not found

Example:

```bash
curl -X POST http://localhost:8001/chat \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "f4a2fca4-39d0-4028-8fb5-4f0b84b6c9d5",
    "message": "How much have I invested this month?",
    "conversation_id": null
  }'
```

### `GET /sessions`

Get sessions for the current user.

Headers:
- `Authorization: Bearer <token>`

Query params:
- `include_archived` (boolean, default: `false`)

Success response (`200`):

```json
[
  {
    "id": "3a640334-9816-4f3b-8b4f-4dbf03b80229",
    "title": "New Chat",
    "created_at": "2026-03-17T07:10:00.000000",
    "updated_at": "2026-03-17T07:13:40.000000",
    "is_archived": false,
    "message_count": 8
  }
]
```

### `GET /sessions/{session_id}/messages`

Get messages for a given session.

Headers:
- `Authorization: Bearer <token>`

Path params:
- `session_id` (UUID)

Query params:
- `limit` (int, default: `50`)
- `offset` (int, default: `0`)

Success response (`200`):

```json
[
  {
    "id": "43a39cc0-c3d6-4f95-9f3f-bcc66d3d8d45",
    "session_id": "3a640334-9816-4f3b-8b4f-4dbf03b80229",
    "role": "assistant",
    "content": "Based on your memory graph...",
    "intent": "QUESTION",
    "created_at": "2026-03-17T07:13:40.000000",
    "retrieval_time_ms": 120.4,
    "llm_generation_time_ms": 502.7,
    "nodes_retrieved": 5,
    "memory_storage": null,
    "memory_citations": []
  }
]
```

Common errors:
- `403`: Session does not belong to authenticated user

### `POST /sessions/{session_id}/archive`

Archive a session.

Headers:
- `Authorization: Bearer <token>`

Path params:
- `session_id` (UUID)

Success response (`200`):

```json
{
  "message": "Session archived successfully"
}
```

### `DELETE /sessions/{session_id}`

Delete a session and all associated messages.

Headers:
- `Authorization: Bearer <token>`

Path params:
- `session_id` (UUID)

Success response (`200`):

```json
{
  "message": "Session deleted successfully"
}
```

---

## 🧠 Memory API

### `GET /memory/mindmap`

Returns the authenticated user's graph for visualization.

Headers:
- `Authorization: Bearer <token>`

Success response (`200`):

```json
{
  "nodes": [
    {
      "id": "fact_1",
      "type": "Fact",
      "label": "Invested in HDFC Mutual Fund",
      "properties": {
        "amount": 50000
      }
    }
  ],
  "edges": [
    {
      "id": "rel_1",
      "source": "user_1",
      "target": "fact_1",
      "type": "OWNS_MEMORY",
      "label": "OWNS_MEMORY",
      "properties": {}
    }
  ],
  "total_nodes": 1,
  "total_edges": 1
}
```

Common errors:
- `401`: Missing/invalid/expired token
- `404`: User not found
- `400`: User not linked to knowledge graph

---

## 💾 Database Schema

**PostgreSQL Tables:**
- `users` - UUID, email, bcrypt password, neo4j_user_id mapping
- `chat_sessions` - Conversation grouping, archiving
- `chat_messages` - Full message history with JSONB metadata (retrieval_time_ms, citations)
- `user_preferences` - Key-value settings

**Neo4j Graph:**
- **Nodes**: User, Message, Fact, Transaction, Asset, Goal
- **Relationships**: OWNS_MEMORY, MADE_TRANSACTION, AFFECTS_ASSET, HAS_GOAL

---

## 🐳 Docker Services

```yaml
services:
  postgres:
    image: postgres:16-alpine
    port: 5432
    volumes: ./backend/database/init.sql
    
  neo4j:
    image: neo4j:5.14.0
    ports: 7474, 7687
    plugins: APOC
```

**Default Admin:** admin@graphmind.ai / admin123

---

## ⚙️ Configuration (.env)

```env
# Gemini API
GEMINI_API_KEY=your_key_here

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=graphmind123

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=graphmind
POSTGRES_USER=graphmind_user
POSTGRES_PASSWORD=graphmind_pass_2026

# JWT
JWT_SECRET_KEY=your_secret_key_here
```

---


