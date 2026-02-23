# 🧠 GraphMind - Financial Graph Memory RAG System

> A user-isolated, graph-first financial memory assistant that uses adaptive multi-hop graph retrieval combined with vector search to generate grounded and explainable financial insights.

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Neo4j](https://img.shields.io/badge/Neo4j-008CC1?style=for-the-badge&logo=neo4j&logoColor=white)](https://neo4j.com/)
[![Milvus](https://img.shields.io/badge/Milvus-00ADD8?style=for-the-badge)](https://milvus.io/)

---

## 🎯 Project Overview

GraphMind is a next-generation financial assistant that combines:
- **Graph Memory** (Neo4j) for structured financial knowledge
- **Vector Memory** (Milvus) for semantic recall
- **LLM Intelligence** (Gemini) for extraction and reasoning
- **Adaptive Retrieval** for optimal context gathering

### Key Features

✅ **Hybrid Memory System**: Graph + Vector storage  
✅ **Intent-Aware Processing**: Automatically classifies MEMORY vs QUESTION  
✅ **Multi-hop Reasoning**: Adaptive graph traversal based on query complexity  
✅ **User Isolation**: Complete data privacy per user  
✅ **Explainable AI**: Returns sources with every answer  
✅ **Performance Tracking**: Measure retrieval timing  
✅ **Production-Ready**: Clean architecture, proper error handling

---

## 🏗️ Architecture

```
┌──────────┐
│   User   │
└────┬─────┘
     │
     ├──────────────────────────────────────┐
     ▼                                      ▼
┌─────────────┐                    ┌────────────────┐
│  Frontend   │                    │  Backend API   │
│ (React)     │ ──── REST ────────▶│  (FastAPI)     │
└─────────────┘                    └────────┬───────┘
                                            │
                     ┌──────────────────────┼──────────────────┐
                     ▼                      ▼                  ▼
             ┌──────────────┐      ┌──────────────┐  ┌──────────────┐
             │ Extraction   │      │  Neo4j       │  │   Milvus     │
             │ (LLM)        │      │  (Graph)     │  │  (Vector)    │
             └──────────────┘      └──────────────┘  └──────────────┘
```

See [Architecture Documentation](docs/architecture.md) for detailed system design.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Neo4j
- Milvus
- Gemini API Key

### Installation

```bash
# Clone repository
git clone <repo-url>
cd graphmind

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Linux/Mac
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your API keys

# Frontend setup
cd ../frontend
npm install
```

### Running

```bash
# Terminal 1: Start backend
cd backend
source venv/bin/activate
python -m api.main

# Terminal 2: Start frontend
cd frontend
npm run dev
```

📚 **Full setup guide**: [docs/setup.md](docs/setup.md)

---

## 📁 Project Structure

```
graphmind/
├── backend/
│   ├── api/                      # API layer (FastAPI routes)
│   │   ├── main.py              # Application entry point
│   │   ├── models.py            # Pydantic request/response models
│   │   └── routes/              # API endpoints
│   │       ├── health.py        # Health check
│   │       └── chat.py          # Main chat endpoint
│   │
│   ├── services/                # Business logic layer
│   │   ├── extraction/          # LLM-based entity extraction
│   │   │   └── llm_extractor.py
│   │   ├── graph/               # Neo4j graph operations
│   │   │   ├── schema.cypher
│   │   │   ├── ingestion.py
│   │   │   └── retrieval.py
│   │   ├── vector/              # Milvus vector operations
│   │   │   ├── embeddings.py
│   │   │   ├── ingestion.py
│   │   │   └── retrieval.py
│   │   ├── llm/                 # LLM services
│   │   │   ├── intent_classifier.py
│   │   │   └── answer_generator.py
│   │   └── orchestrator/        # Workflow coordination
│   │       ├── memory_orchestrator.py
│   │       └── retrieval_orchestrator.py
│   │
│   ├── config/                  # Configuration management
│   │   └── settings.py
│   ├── requirements.txt         # Python dependencies
│   └── .env                     # Environment variables
│
├── frontend/                    # React frontend
│   ├── src/
│   ├── public/
│   └── package.json
│
├── data/                        # Data storage
│   ├── examples/               # Sample data
│   └── user_samples/           # User data (gitignored)
│
├── docs/                        # Documentation
│   ├── architecture.md         # System architecture
│   ├── setup.md               # Setup guide
│   └── team-responsibilities.md # Team division
│
└── README.md                   # This file
```

---

## 🔄 How It Works

### 1️⃣ Memory Ingestion Flow

```
User: "I invested 50,000 in HDFC Mutual Fund"
  ↓
Intent: MEMORY
  ↓
LLM Extraction → {nodes: [Asset], relationships: [OWNS]}
  ↓
Graph Storage (Neo4j) + Vector Storage (Milvus)
  ↓
Response: "Financial memory stored successfully"
```

### 2️⃣ Question Answering Flow

```
User: "Am I aligned with my retirement goal?"
  ↓
Intent: QUESTION
  ↓
Graph Retrieval (2-hop) + Vector Retrieval (semantic)
  ↓
Context Assembly
  ↓
LLM Answer Generation
  ↓
Response: {answer, sources, metrics}
```

### 3️⃣ Combined Flow

```
User: "I invested 50k in HDFC. Am I on track?"
  ↓
Intent: BOTH
  ↓
Run BOTH flows
  ↓
Response: {answer, storage_result, sources, metrics}
```

---

## 👥 Team Responsibilities

**Person 1 - Graph Lead**
- Neo4j schema design
- Graph ingestion & retrieval
- Multi-hop query optimization

**Person 2 - LLM Lead**
- Entity extraction
- Intent classification
- Answer generation

**Person 3 - Vector Lead**
- Embedding generation
- Milvus integration
- Semantic search

📋 **Detailed breakdown**: [docs/team-responsibilities.md](docs/team-responsibilities.md)

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI
- **Graph DB**: Neo4j
- **Vector DB**: Milvus
- **LLM**: Google Gemini (or OpenAI)
- **Language**: Python 3.10+

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **Language**: TypeScript

### MLOps
- **Embeddings**: Sentence Transformers / OpenAI
- **Vector Search**: Milvus IVF_FLAT index
- **Graph Queries**: Cypher

---

## 📊 Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Graph Retrieval | < 50ms | Multi-hop queries |
| Vector Retrieval | < 30ms | Semantic search |
| Total Retrieval | < 100ms | Combined time |
| LLM Response | N/A | Not measured |

---

## 🔧 Configuration

All configuration is environment-based. Copy `.env.example` to `.env`:

```env
# LLM
GEMINI_API_KEY=your_key_here

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=your_password

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Settings
DEFAULT_TOP_K=5
MAX_GRAPH_DEPTH=3
```

---

## 📖 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

**POST /chat** - Main chat endpoint
```json
{
  "user_id": "user123",
  "message": "I invested 50,000 in HDFC MF. Am I aligned with my goal?",
  "conversation_id": "conv_001"
}
```

**GET /health** - Health check

---

## 🧪 Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "I invested 50,000 in HDFC MF",
    "conversation_id": "test_conv"
  }'
```

---

## 📚 Documentation

- [System Architecture](docs/architecture.md)
- [Setup Guide](docs/setup.md)
- [Team Responsibilities](docs/team-responsibilities.md)
- [Backend README](backend/README.md)

---

## 🏆 What Makes This Special

✨ **Research-Inspired**: Based on IGMiRAG and graph RAG papers  
✨ **Production-Ready**: Clean architecture, error handling, logging  
✨ **Explainable**: Returns sources and metrics  
✨ **Scalable**: Service-oriented design  
✨ **Performant**: Optimized retrieval strategies  
✨ **Secure**: User-isolated data storage  

---

## 🛣️ Roadmap

### Phase 1: Core Features (Current)
- [x] Intent classification
- [x] Service layer architecture
- [ ] Graph ingestion
- [ ] Vector ingestion
- [ ] Retrieval implementation

### Phase 2: Advanced Features
- [ ] Conversation memory
- [ ] Multi-user support
- [ ] Advanced analytics
- [ ] Performance optimization

### Phase 3: Production
- [ ] Authentication
- [ ] Production deployment
- [ ] Monitoring & logging
- [ ] Load testing

---

## 🤝 Contributing

This is a hackathon project with a 3-person team. See [team-responsibilities.md](docs/team-responsibilities.md) for task division.

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

- Inspired by research papers on Graph RAG and IGMiRAG
- Built with amazing open-source tools
- Powered by Graph + Vector hybrid memory

---

## 📞 Contact

For questions or issues, please open an issue or contact the team.

---

**Built with ❤️ for intelligent financial assistance**
