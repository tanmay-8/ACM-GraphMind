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

### Authentication
- `POST /auth/signup` - Create account
- `POST /auth/login` - Get JWT token
- `GET /auth/me` - Get current user

### Chat
- `POST /chat` - Send message (requires JWT)
- `GET /sessions` - List chat sessions
- `GET /sessions/{id}/messages` - Get conversation history
- `POST /sessions/{id}/archive` - Archive session
- `DELETE /sessions/{id}` - Delete session

### Example Request
```bash
curl -X POST http://localhost:8001/chat \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "I invested $50k in stocks"}'
```

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

## 🎯 Current Status

✅ **Working:**
- User signup/login with PostgreSQL
- JWT authentication
- Chat message persistence
- Neo4j graph ingestion
- Production-grade retrieval system
- Session management API

⚠️ **Known Issues:**
- Gemini API quota limit (20 req/day on free tier)

📋 **Pending:**
- Chat history UI components
- Session switching in frontend
- Real-time message loading

---

## 🛣️ Roadmap

**Phase 1 (Complete):**
- ✅ Dual database architecture
- ✅ User authentication
- ✅ Chat persistence
- ✅ Mode-based retrieval

**Phase 2 (In Progress):**
- 🔄 Chat history UI
- 🔄 Session management UI

**Phase 3 (Future):**
- Analytics dashboard
- Export chat history
- Advanced filtering
- Production deployment

---

## 📄 License

MIT License

---

**Built with ❤️ using FastAPI, React, PostgreSQL, and Neo4j**
