# RAG Chatbot Backend

A FastAPI-based RAG (Retrieval-Augmented Generation) chatbot for the "Physical AI & Humanoid Robotics" Docusaurus book.

## Overview

This backend provides a streaming chat API that:
- Searches the book content using vector similarity (Qdrant)
- Generates contextual answers using Gemini 2.0 Flash
- Stores chat sessions and history in Neon Postgres
- Returns citations for every answer

## Architecture

```
backend/
├── main.py                 # FastAPI application entry point
├── app/
│   ├── config.py          # Environment configuration
│   ├── models/
│   │   └── schemas.py     # Pydantic request/response models
│   ├── routes/
│   │   └── chat.py        # Chat API endpoints
│   ├── services/
│   │   ├── db_service.py       # Neon Postgres operations
│   │   ├── qdrant_service.py   # Qdrant vector operations
│   │   ├── embedding_service.py # Gemini embeddings
│   │   └── rag_pipeline.py     # RAG orchestration
│   └── agents/
│       └── book_agent.py  # LLM agent with tools
├── requirements.txt
├── Dockerfile
└── .env.example
```

## Quick Start (Local Development)

### Prerequisites

- Python 3.9+
- Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))
- Neon Postgres database ([Sign up free](https://neon.tech))
- Qdrant Cloud cluster ([Sign up free](https://cloud.qdrant.io))

### Setup

1. Create and activate virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy environment file and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. Run the server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. Access API docs at: http://localhost:8000/docs

### Ingest Book Content

After the backend is running, use the auto-chunker script to ingest book content:

```bash
cd docs
python auto-chunker.py --docs-path ../physical-ai-humanoid-robotics/docs --backend-url http://localhost:8000
```

## API Endpoints

### Health Check
- `GET /health` - Returns service health status

### Chat
- `POST /api/chatbot/chat/stream` - Streaming chat endpoint
  - Request body:
    ```json
    {
      "query": "What is ROS 2?",
      "selected_text": null,
      "session_id": null
    }
    ```
  - Response: Server-Sent Events stream

### Embed (Content Ingestion)
- `POST /api/chatbot/embed` - Embed new book content

### Info
- `GET /api/chatbot/info` - Get collection information

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `NEON_DATABASE_URL` | Neon Postgres connection string | Yes |
| `QDRANT_URL` | Qdrant Cloud cluster URL | Yes |
| `QDRANT_API_KEY` | Qdrant API key | Yes |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | Yes |
| `QDRANT_COLLECTION_NAME` | Qdrant collection name | No (default: physical_ai_book) |
| `LLM_MODEL` | LLM model name | No (default: gemini-2.5-flash) |
| `EMBEDDING_MODEL` | Embedding model name | No (default: text-embedding-004) |
| `LLM_BASE_URL` | Gemini OpenAI-compatible API URL | No |

## Deployment

### Docker (Local)

```bash
docker build -t rag-chatbot-backend .
docker run -p 8000:8000 --env-file .env rag-chatbot-backend
```

### Deploy to Render

1. Create a new Web Service on [Render](https://render.com)
2. Connect your GitHub repository
3. Configure the service:
   - **Environment**: Docker
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Docker Context**: `backend`
4. Add environment variables in the Render dashboard:
   - `GEMINI_API_KEY`
   - `NEON_DATABASE_URL`
   - `QDRANT_URL`
   - `QDRANT_API_KEY`
   - `CORS_ORIGINS` (set to your Vercel frontend URL)
5. Deploy

### Deploy to Fly.io

1. Install the Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Launch from the backend directory:
   ```bash
   cd backend
   fly launch --name rag-chatbot-backend
   ```
4. Set secrets:
   ```bash
   fly secrets set GEMINI_API_KEY=your_key
   fly secrets set NEON_DATABASE_URL=your_url
   fly secrets set QDRANT_URL=your_url
   fly secrets set QDRANT_API_KEY=your_key
   fly secrets set CORS_ORIGINS=https://your-frontend.vercel.app
   ```
5. Deploy: `fly deploy`

## Frontend Deployment (Vercel)

The Docusaurus frontend with the chatbot widget can be deployed to Vercel:

1. Push your repository to GitHub
2. Import the project on [Vercel](https://vercel.com)
3. Configure the build:
   - **Root Directory**: `physical-ai-humanoid-robotics`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
4. Add environment variable:
   - `CHATBOT_API_URL`: Your backend URL (e.g., `https://your-backend.onrender.com/api/chatbot`)
5. Deploy

### Configure Frontend API URL

In the frontend, update the API URL by setting `window.CHATBOT_API_URL` before the React app loads, or modify `src/theme/ChatbotWidget/index.tsx`:

```typescript
const API_BASE_URL = 'https://your-backend-url.onrender.com/api/chatbot';
```

## Testing the Chat

Once deployed, test the chat endpoint:

```bash
curl -X POST "https://your-backend-url/api/chatbot/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is ROS 2?", "session_id": null}'
```

## License

MIT
