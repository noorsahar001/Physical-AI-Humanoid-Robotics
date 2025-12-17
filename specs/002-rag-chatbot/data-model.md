# Data Model: RAG Chatbot for Physical AI & Humanoid Robotics Book

**Branch**: `002-rag-chatbot` | **Date**: 2025-12-13 | **Spec**: [spec.md](./spec.md)

## Overview

This document defines the data entities, their attributes, relationships, and validation rules for the RAG chatbot system.

---

## Entities

### 1. Document

Represents a source file from the book (Markdown/MDX).

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (UUID) | Yes | Unique identifier |
| `title` | string | Yes | Document title from frontmatter or filename |
| `file_path` | string | Yes | Relative path from docs folder |
| `module_label` | string | No | Module/chapter classification (e.g., "Module 1: ROS 2") |
| `content_hash` | string | Yes | SHA-256 hash for change detection |
| `created_at` | datetime | Yes | First ingestion timestamp |
| `updated_at` | datetime | Yes | Last re-ingestion timestamp |
| `chunk_count` | integer | Yes | Number of chunks generated |

**Validation Rules**:
- `file_path` must be unique
- `file_path` must end with `.md` or `.mdx`
- `title` max length: 500 characters

---

### 2. Chunk

A segment of a document optimized for retrieval.

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (UUID) | Yes | Unique identifier |
| `document_id` | string (UUID) | Yes | Foreign key to Document |
| `text_content` | string | Yes | The chunk text |
| `token_count` | integer | Yes | Number of tokens (300-500 range) |
| `position` | integer | Yes | Order within document (0-indexed) |
| `section_title` | string | No | Nearest heading above chunk |
| `section_hierarchy` | string | No | Full heading path (e.g., "Module 1 > ROS 2 Basics > Installation") |

**Validation Rules**:
- `token_count` must be between 100 and 600 (soft limits with 300-500 target)
- `position` must be >= 0
- `text_content` cannot be empty

**Relationships**:
- Belongs to one Document
- Has one Embedding (1:1 stored in Qdrant)

---

### 3. Embedding (Qdrant Point)

Vector representation of a chunk stored in Qdrant.

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (UUID) | Yes | Same as chunk_id for direct mapping |
| `vector` | float[1536] | Yes | Embedding vector (OpenAI text-embedding-3-small) |
| `payload.chunk_id` | string | Yes | Reference to Chunk |
| `payload.document_id` | string | Yes | Reference to Document |
| `payload.text` | string | Yes | Chunk text for retrieval display |
| `payload.source` | string | Yes | File path for citations |
| `payload.title` | string | Yes | Document title |
| `payload.section` | string | No | Section title |
| `payload.position` | integer | Yes | Position in document |

**Qdrant Collection Config**:
```json
{
  "collection_name": "physical_ai_book",
  "vectors": {
    "size": 1536,
    "distance": "Cosine"
  }
}
```

---

### 4. Query

A user's question (in-memory, not persisted in MVP).

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (UUID) | Yes | Unique identifier |
| `text` | string | Yes | User's question text |
| `timestamp` | datetime | Yes | When query was received |
| `session_id` | string | No | Session identifier for context |

**Validation Rules**:
- `text` cannot be empty
- `text` max length: 2000 characters

---

### 5. Response

The chatbot's answer (in-memory for MVP).

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (UUID) | Yes | Unique identifier |
| `query_id` | string (UUID) | Yes | Reference to Query |
| `answer_text` | string | Yes | Generated answer |
| `citations` | Citation[] | Yes | List of source citations |
| `retrieved_chunks` | string[] | Yes | IDs of chunks used |
| `timestamp` | datetime | Yes | When response was generated |
| `latency_ms` | integer | Yes | Processing time |

---

### 6. Citation

A reference to source material in a response.

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `index` | integer | Yes | Citation number (1-based) |
| `source` | string | Yes | File path |
| `title` | string | Yes | Document title |
| `section` | string | No | Section within document |
| `relevance_score` | float | No | Similarity score (0-1) |

---

## Entity Relationship Diagram (Text)

```
┌─────────────┐       ┌─────────────┐       ┌─────────────────┐
│  Document   │──1:N──│    Chunk    │──1:1──│    Embedding    │
│             │       │             │       │    (Qdrant)     │
│ id          │       │ id          │       │ id              │
│ title       │       │ document_id │       │ vector[1536]    │
│ file_path   │       │ text_content│       │ payload         │
│ module_label│       │ token_count │       └─────────────────┘
│ content_hash│       │ position    │
│ chunk_count │       │ section_*   │
└─────────────┘       └─────────────┘

┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    Query    │──1:1──│  Response   │──1:N──│  Citation   │
│             │       │             │       │             │
│ id          │       │ id          │       │ index       │
│ text        │       │ query_id    │       │ source      │
│ timestamp   │       │ answer_text │       │ title       │
│ session_id  │       │ citations   │       │ section     │
└─────────────┘       │ latency_ms  │       │ score       │
                      └─────────────┘       └─────────────┘
```

---

## State Transitions

### Document States

```
[Not Ingested] ──ingest──> [Ingested] ──update──> [Re-Ingested]
                                │
                                └──delete──> [Removed]
```

### Query-Response Flow

```
[Query Received] ──validate──> [Embedding Generated] ──search──> [Chunks Retrieved]
       │                                                               │
       │                                                               v
       └──invalid──> [Error Response]              [Context Assembled] ──generate──> [Response Sent]
                                                          │
                                                          └──no_chunks──> [Not Found Response]
```

---

## Indexing Strategy

### Qdrant Indexes

- **Vector Index**: HNSW on embedding vectors for similarity search
- **Payload Index**: Keyword filter on `source` and `title` fields

### In-Memory Tracking

- Document hash map: `file_path -> content_hash` for incremental updates
- Session context: `session_id -> [recent_messages]` for multi-turn (P3)

---

## Data Volume Estimates

| Entity | Estimated Count | Storage |
|--------|-----------------|---------|
| Documents | ~50-100 MDX files | N/A (metadata only) |
| Chunks | ~500-1000 | ~2MB text |
| Embeddings | ~500-1000 | ~6MB vectors (1536 * 4 bytes * 1000) |

**Qdrant Free Tier**: 1GB storage - well within limits
