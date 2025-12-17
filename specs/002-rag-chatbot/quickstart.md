# Quickstart: RAG Chatbot for Physical AI & Humanoid Robotics Book

**Branch**: `002-rag-chatbot` | **Constitution**: v1.1.0

This guide provides step-by-step instructions to set up, run, and verify the RAG chatbot on Windows with Python 3.13.

---

## Prerequisites

Before starting, ensure you have:

- [ ] Windows 10/11
- [ ] Python 3.13 installed ([Download](https://www.python.org/downloads/))
- [ ] Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop/))
- [ ] Git installed
- [ ] OpenAI API key (or alternative LLM provider)

---

## Step 1: Environment Setup

### 1.1 Verify Python Version

```powershell
python --version
# Expected: Python 3.13.x
```

If you have multiple Python versions:
```powershell
py -3.13 --version
```

### 1.2 Clone Repository (if not done)

```powershell
cd C:\humanoid_robotics_ai_book
```

### 1.3 Create Virtual Environment

```powershell
# Create venv
python -m venv venv

# Activate venv (PowerShell)
.\venv\Scripts\Activate.ps1

# Or for Command Prompt
.\venv\Scripts\activate.bat
```

**Verification**: Your prompt should show `(venv)` prefix.

---

## Step 2: Install Dependencies

### 2.1 Create requirements.txt

Create `backend/requirements.txt`:

```text
# Core Framework
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.9.0
python-dotenv>=1.0.0

# LangChain RAG Stack
langchain>=0.3.0
langchain-core>=0.3.0
langchain-openai>=0.2.0
langchain-qdrant>=0.2.0
langchain-text-splitters>=0.3.0

# Vector Database
qdrant-client>=1.12.0

# Utilities
httpx>=0.27.0
tiktoken>=0.8.0
```

### 2.2 Install Dependencies

```powershell
cd backend
pip install -r requirements.txt
```

### 2.3 Verify Installation

```powershell
python -c "import fastapi; import langchain; import qdrant_client; print('All dependencies installed!')"
```

**Expected Output**: `All dependencies installed!`

---

## Step 3: Configure Environment

### 3.1 Create .env File

Create `backend/.env`:

```env
# LLM Configuration
OPENAI_API_KEY=sk-your-api-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# Embedding Configuration
EMBEDDING_MODEL=text-embedding-3-small

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=physical_ai_book

# Book Content Path
DOCS_PATH=../physical-ai-humanoid-robotics/docs

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### 3.2 Verify .env Loaded

```powershell
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key Set:', bool(os.getenv('OPENAI_API_KEY')))"
```

**Expected Output**: `API Key Set: True`

---

## Step 4: Start Qdrant Vector Database

### 4.1 Start Docker Desktop

Ensure Docker Desktop is running (check system tray icon).

### 4.2 Run Qdrant Container

```powershell
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### 4.3 Verify Qdrant Running

```powershell
curl http://localhost:6333/health
# Or in PowerShell:
Invoke-RestMethod -Uri http://localhost:6333/health
```

**Expected Output**: `{"title":"qdrant - vector search engine","version":"..."}`

---

## Step 5: Ingest Book Content

### 5.1 Run Ingestion Script

```powershell
cd backend
python -m scripts.ingest
```

Or via API once server is running:
```powershell
curl -X POST http://localhost:8000/ingest
```

### 5.2 Verify Ingestion

```powershell
# Check collection exists
Invoke-RestMethod -Uri "http://localhost:6333/collections/physical_ai_book"
```

**Expected**: Response showing collection with points count > 0

---

## Step 6: Run the Chatbot Server

### 6.1 Start FastAPI Server

```powershell
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6.2 Verify Server Running

Open browser: http://localhost:8000/docs

**Expected**: FastAPI Swagger UI with available endpoints

---

## Step 7: Test the Chatbot

### 7.1 Health Check

```powershell
Invoke-RestMethod -Uri http://localhost:8000/health
```

**Expected**:
```json
{
  "status": "healthy",
  "services": {
    "api": {"status": "up"},
    "qdrant": {"status": "up"},
    "llm": {"status": "up"}
  }
}
```

### 7.2 Send Test Query

```powershell
$body = @{
    query = "What is ROS 2?"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -Body $body -ContentType "application/json"
```

**Expected**: Response with answer about ROS 2 from book content with citations

### 7.3 Test Out-of-Scope Query

```powershell
$body = @{
    query = "What is the recipe for chocolate cake?"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -Body $body -ContentType "application/json"
```

**Expected**: Response indicating content not found in book

---

## Troubleshooting

### Issue: "ModuleNotFoundError"

**Solution**: Ensure virtual environment is activated and dependencies installed:
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Issue: "Connection refused" to Qdrant

**Solution**: Verify Docker container is running:
```powershell
docker ps | findstr qdrant
# If not running:
docker start qdrant
```

### Issue: "Invalid API Key"

**Solution**: Check .env file has correct API key without quotes:
```env
OPENAI_API_KEY=sk-proj-...
```

### Issue: "No relevant content found" for valid questions

**Solution**: Run ingestion to populate vector store:
```powershell
python -m scripts.ingest
```

---

## Success Criteria Validation

| Criterion | Test Command | Expected Result |
|-----------|--------------|-----------------|
| SC-001: Accurate answers | Query about ROS 2 | Answer matches book content |
| SC-002: Response < 5s | Time the /chat request | Under 5 seconds |
| SC-003: Out-of-scope detection | Query unrelated topic | "Not found" message |
| SC-004: Ingestion success | Check Qdrant collection | Points count > 0 |
| SC-005: Citations included | Check /chat response | citations array non-empty |
| SC-006: Service uptime | /health endpoint | status: "healthy" |
| SC-007: No unhandled errors | Various queries | No 500 errors |

---

## Next Steps

1. Run full test suite: `pytest tests/`
2. Try different questions from book topics
3. Optional: Deploy to cloud (see deployment guide)

---

## Quick Reference

| Action | Command |
|--------|---------|
| Activate venv | `.\venv\Scripts\Activate.ps1` |
| Start Qdrant | `docker start qdrant` |
| Start server | `uvicorn main:app --reload` |
| Run ingestion | `python -m scripts.ingest` |
| Health check | `curl http://localhost:8000/health` |
| API docs | http://localhost:8000/docs |
