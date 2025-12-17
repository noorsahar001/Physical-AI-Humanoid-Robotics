<!-- Sync Impact Report -->
<!--
Version change: 1.1.0 → 2.0.0 (MAJOR)
List of modified principles:
  - I. Accurate Book Content Retrieval → retained (unchanged)
  - II. Context-Aware Response Generation → retained (unchanged)
  - III. RAG Architecture with Vector Storage → retained (unchanged)
  - IV. Modular Backend Architecture → expanded to include subagent routing
  - V. Passage-Level Citation and Error Handling → retained (unchanged)
  - VI. Dependency and Environment Integrity → retained (unchanged)
  - VII. Step-by-Step Implementation Discipline → retained (unchanged)
  - VIII. Verification and Error-Free Execution → retained (unchanged)
  - IX. Reliable Query Resolution Guarantee → retained (unchanged)
Added sections:
  - X. Modular Subagent Architecture (Part 4 - Reusable Intelligence)
  - XI. Domain-Specific Agent Isolation
  - XII. Seamless Query Delegation and Routing
  - XIII. Agent Scalability and Extension
  - New "Part 4: Reusable Intelligence Architecture" grouping
  - Updated Technology Stack to include Claude Code Subagents and Agent Skills
Removed sections: None
Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ no changes required (generic)
  - .specify/templates/spec-template.md: ✅ no changes required (generic)
  - .specify/templates/tasks-template.md: ✅ no changes required (generic)
Follow-up TODOs: None
-->
# Integrated RAG Chatbot for Physical AI & Humanoid Robotics Constitution

## Core Principles (Part 1-3: RAG Chatbot Foundation)

### I. Accurate Book Content Retrieval
The chatbot MUST answer any question related to the book's content accurately. All responses MUST be derived exclusively from the "Physical AI & Humanoid Robotics" book material. The system MUST NOT hallucinate or invent information beyond what exists in the source content.

### II. Context-Aware Response Generation
All answers MUST be context-aware and based only on book material. The chatbot MUST use Retrieval-Augmented Generation (RAG) to ensure responses are grounded in specific passages. When no relevant content is found, the system MUST inform the user rather than fabricate an answer.

### III. RAG Architecture with Vector Storage
The system MUST implement a RAG approach using embeddings and Qdrant as the vector storage solution. This architecture ensures semantic search capabilities across book passages, enabling accurate retrieval of contextually relevant content for query answering.

### IV. Modular Backend Architecture
Implement a FastAPI backend to serve API endpoints. This architecture MUST be modular, allowing for independent updates to book content without impacting chatbot functionality. The backend MUST support clean separation between ingestion, embedding, retrieval, response generation, and subagent routing.

### V. Passage-Level Citation and Error Handling
All generated responses MUST include clear citations to the source passage(s) from the book. Robust error handling MUST be implemented to gracefully manage scenarios where no relevant content is found for a given query, providing informative feedback to the user.

### VI. Dependency and Environment Integrity
All dependencies MUST be installed correctly without errors. The project environment MUST use:
- **Python**: 3.13
- **Web Framework**: FastAPI with Uvicorn
- **LLM Orchestration**: LangChain
- **Vector Database**: Qdrant

Any dependency conflicts or installation failures MUST be resolved before proceeding to implementation.

### VII. Step-by-Step Implementation Discipline
The project MUST provide clear, step-by-step instructions for:
1. Environment setup and dependency installation
2. Ingestion of book content into the vector store
3. Running the chatbot service

All tasks MUST be broken down so they can be implemented sequentially, ensuring each step builds upon the previous without skipping prerequisites.

### VIII. Verification and Error-Free Execution
Each implementation step MUST be verified to ensure no errors occur during installation or runtime. The development process MUST include:
- Dependency verification after installation
- Service health checks after startup
- Query validation after RAG pipeline completion

Proceeding to the next step is ONLY permitted after the current step passes verification.

### IX. Reliable Query Resolution Guarantee
Once setup is complete, the chatbot MUST be able to answer any query from the book reliably. This includes:
- Technical concepts from all chapters
- Code examples and implementation details
- Theoretical foundations and practical applications

The system MUST maintain consistent availability and response quality across all supported query types.

## Part 4: Reusable Intelligence Architecture

### X. Modular Subagent Architecture
The system MUST implement reusable intelligence using Claude Code Subagents and Agent Skills. Each subagent MUST:
- Be implemented using Claude Code for consistent execution
- Encapsulate domain-specific knowledge and reasoning capabilities
- Operate as an independent, self-contained unit that can answer queries without relying on other subagents
- Be reusable across multiple chapters and contexts within the book project

Subagents MUST NOT duplicate content or logic; shared functionality MUST be abstracted into common utilities or base agent skills.

### XI. Domain-Specific Agent Isolation
Each subagent MUST focus on a specific domain within the Physical AI & Humanoid Robotics book:
- **Robotics Fundamentals Agent**: Kinematics, dynamics, and control systems
- **Computer Vision Agent**: Visual perception, image processing, and object recognition
- **Natural Language Agent**: Speech processing, NLU, and human-robot dialogue
- **Motion Planning Agent**: Path planning, trajectory optimization, and navigation
- **Simulation Agent**: Humanoid simulation, physics engines, and virtual testing

Each agent MUST maintain clear boundaries and MUST NOT encroach on another agent's domain unless explicitly designed for cross-domain integration.

### XII. Seamless Query Delegation and Routing
The main chatbot MUST integrate with subagents for seamless query delegation:
- The routing layer MUST analyze incoming queries and determine the appropriate subagent(s) to handle the request
- Query delegation MUST be transparent to the user; responses MUST appear as a unified chatbot experience
- When a query spans multiple domains, the router MUST coordinate responses from multiple subagents and synthesize a coherent answer
- Fallback behavior MUST be defined for queries that no subagent can handle

### XIII. Agent Scalability and Extension
The subagent architecture MUST be designed for scalability:
- Adding new subagents (e.g., for additional book modules or hardware setups) MUST NOT require modifications to existing agents
- The registration mechanism MUST support dynamic discovery of available agents
- Agent interfaces MUST follow a standardized contract to ensure interoperability
- Performance MUST scale linearly with the number of active subagents; no single agent failure should cascade to others

## Technology Stack and Best Practices

The project adheres to the following technology stack and best practices:
- **Language**: Python 3.13
- **Backend**: FastAPI for robust and scalable API services
- **ASGI Server**: Uvicorn for production-ready async serving
- **LLM Orchestration**: LangChain for RAG pipeline management
- **Vector Database**: Qdrant for efficient storage and similarity search of embeddings
- **Subagent Framework**: Claude Code Subagents with Agent Skills for reusable intelligence
- **Frontend Integration**: Docusaurus for book publishing (optional React chatbot component)
- **RAG Pipeline**: Best practices for text extraction, chunking, embedding, vector indexing, query embeddings, and retrieval
- **Agent Design**: Modular, domain-isolated agents with standardized interfaces and registration
- **Code Quality**: Production-ready, modular code with inline comments explaining each module

## Deployment and Environment

The solution is designed for deployment flexibility:
- **Local Development**: Ready to deploy and test on localhost with Python 3.13
- **Cloud Deployment**: Optional deployment on platforms like Vercel/Cloud for frontend and suitable cloud providers for backend services
- **Environment Management**: Use `.env` files for managing environment variables and sensitive information; never hardcode secrets
- **Qdrant Options**: Local Qdrant instance for development; Qdrant Cloud for production
- **Subagent Deployment**: Agents MUST be deployable independently for isolated testing and can be composed at runtime

## Governance

This Constitution supersedes all other project practices. Amendments require thorough documentation, explicit approval from stakeholders, and a clear migration plan. All Pull Requests and code reviews MUST verify compliance with these principles. Complexity introduced into the codebase MUST be justified and align with project goals.

### Amendment Procedure
1. Propose changes with rationale
2. Review against existing principles for conflicts
3. Update version number following semantic versioning
4. Document changes in Sync Impact Report

### Compliance Review
- All implementation tasks MUST reference applicable constitution principles
- Code reviews MUST verify adherence to verification requirements (Principle VIII)
- Subagent implementations MUST demonstrate domain isolation (Principle XI) and scalability (Principle XIII)
- Deployment MUST only proceed after all thirteen principles are satisfied

**Version**: 2.0.0 | **Ratified**: 2025-12-07 | **Last Amended**: 2025-12-17
