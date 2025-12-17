---
id: 001
title: Update RAG Chatbot Constitution
stage: constitution
date: 2025-12-07
surface: agent
model: claude-sonnet-4-5-20250929
feature: rag-chatbot
branch: main
user: unknown
command: /sp.constitution
labels: ["constitution", "rag-chatbot", "initial-setup"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - none
---

## Prompt

  Build an Integrated Retrieval-Augmented Generation (RAG) Chatbot for the book "Physical AI & Humanoid Robotics" using SpecifyPlusKit and Claude Code Router.


1. The chatbot must be embedded within the published Docusaurus book and be able to answer user questions about the book's content.
2. The chatbot must retrieve answers only from the text selected by the user, ensuring context-specific and accurate responses.
3. Use OpenAI Agents or ChatKit SDKs to handle LLM-driven conversational logic.
4. Use FastAPI to serve the backend API for the chatbot.
5. Store and manage book content metadata in Neon Serverless Postgres database.
6. Store vector embeddings of book passages in Qdrant Cloud Free Tier for similarity search.
7. Ensure the system supports passage-level citation: when a response is generated, the chatbot must reference the passage(s) used.
8. The chatbot should handle multi-turn conversation, remembering previous context per session.
9. Ensure the solution is modular so future updates to the book do not break the chatbot.
10. Use best practices for vector indexing, query embeddings, and retrieval in a RAG pipeline.
11. Include proper error handling when no relevant content is found in the selected text.

Book Context (for Reference):
- Focus: AI Systems in the Physical World, Embodied Intelligence.
- Modules:
- Module 1: Robotic Nervous System (ROS 2)
- Module 2: Digital Twin (Gazebo & Unity)
- Module 3: AI-Robot Brain (NVIDIA Isaac)
- Module 4: Vision-Language-Action (VLA)
- Course Goal: Bridging the gap between digital brain and physical humanoid robots. Students control robots in simulation and real-world environments.
- Content contains detailed explanations on ROS 2, Gazebo, Unity simulations, NVIDIA Isaac, sensors (LiDAR, Depth Cameras, IMUs), VLA models, and Capstone project with Autonomous Humanoid.

Instructions for AI (SpecifyPlusKit / Claude Code Router):
- Generate all necessary Python/JS code for:
    1. Extracting and chunking book text from Docusaurus docs.
    2. Embedding passages using OpenAI or Claude embeddings.
    3. Upserting embeddings into Qdrant Cloud.
    4. Serving a FastAPI backend with `/search` and `/rag` endpoints.
    5. Handling user selection input to restrict retrieval to that selection.
    6. Integrating OpenAI Agents / Claude Code Router for generating answers from retrieved passages.
    7. Including metadata and passage citation in responses.
    8. Generating front-end Docusaurus React component to select text and query the RAG chatbot.
- Ensure the code is production-ready and modular.
- Include inline comments explaining each module.
- Output must be ready to deploy on localhost first, then optionally on Vercel/Cloud.

## Response snapshot

The project constitution for the Integrated RAG Chatbot for Physical AI & Humanoid Robotics has been updated to version 1.0.0. The constitution now includes core principles for embedded and context-specific retrieval, LLM-driven conversational logic, modular backend architecture, hybrid data storage, and passage-level citation with error handling. Sections on technology stack, deployment, and governance have also been defined.

## Outcome

- ✅ Impact: Constitution updated, project principles established.
- 🧪 Tests: N/A
- 📁 Files: .specify/memory/constitution.md updated.
- 🔁 Next prompts: Begin planning phase (/sp.plan) for the RAG Chatbot.
- 🧠 Reflection: Successfully updated the constitution based on user requirements and project context. Ensured all placeholders were filled and the version was incremented correctly. The sync impact report was generated and prepended to the file.

## Evaluation notes (flywheel)

- Failure modes observed: Bash script for PHR creation failed, fallback to agent-native tools successful.
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Investigate why .specify/scripts/bash/create-phr.sh is not found or executable.
