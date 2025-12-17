---
id: 002
title: Subagent Implementation Plan
stage: plan
date: 2025-12-17
surface: agent
model: claude-opus-4-5-20251101
feature: 003-reusable-subagents
branch: 003-reusable-subagents
user: system
command: /sp.plan
labels: ["subagents", "architecture", "planning", "routing", "agents"]
links:
  spec: specs/003-reusable-subagents/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/003-reusable-subagents/plan.md
  - specs/003-reusable-subagents/research.md
  - specs/003-reusable-subagents/data-model.md
  - specs/003-reusable-subagents/contracts/openapi.yaml
  - specs/003-reusable-subagents/quickstart.md
tests:
  - null
---

## Prompt

You are tasked with creating a high-level implementation plan for Part 4 of a book project on "Physical AI & Humanoid Robotics".

Objective:
- Implement reusable intelligence using Claude Code Subagents and Agent Skills.
- Ensure subagents are modular, independent, and reusable across multiple chapters of the book.

Plan Requirements:

1. **Identify Topics for Reusable Intelligence**
   - Glossary of technical terms from ROS 2, Gazebo, Isaac, VLA.
   - Hardware guidance: Workstation vs Edge Kit requirements.
   - Module-specific explanations (Module 1 to Module 4).
   - Capstone project guidance (Autonomous Humanoid simulation).

2. **Design Subagents**
   - Define each subagent's purpose, inputs, outputs, and scope.
   - Ensure subagents can be reused across chapters.
   - Example subagents:
     - Glossary Agent
     - Hardware Agent
     - Module Info Agent
     - Capstone Agent

3. **Claude Code Implementation**
   - Generate Python classes/functions for each subagent using Claude Code.
   - Ensure each subagent:
     - Accepts a user query
     - Returns accurate, concise answer
     - Accesses only relevant course content
   - Follow modular design principles to allow future extension.

4. **Integration with Main Chatbot**
   - Implement query delegation:
     - Main chatbot receives user query
     - Identifies appropriate subagent
     - Forwards query to subagent and returns answer
   - Ensure seamless user experience and maintain context.

5. **Testing & Validation**
   - Test each subagent individually with sample queries.
   - Test full chatbot with integrated subagents.
   - Ensure accuracy, reusability, and scalability.

6. **Iteration & Optimization**
   - Refine subagents based on testing results.
   - Optimize for faster responses and minimal duplication.
   - Prepare for future subagent additions (new modules, hardware updates).

Expected Outcome:
- A set of fully functional, modular subagents integrated with the main chatbot.
- Chatbot can efficiently answer user queries on course content, hardware, glossary, and capstone guidance.
- System is scalable, maintainable.

## Response snapshot

Created comprehensive implementation plan for Part 4 (Reusable Subagents) of the Physical AI & Humanoid Robotics book project. The plan includes:

**Architecture**:
- Abstract BaseAgent class with standardized interface
- Four domain-specific subagents: Glossary, Hardware, Module Info, Capstone
- QueryRouter for intelligent query delegation
- Shared Skills layer (RAG, Citation, Context)
- Integration with existing RAG pipeline preserving BookAgent as fallback

**Key Design Decisions**:
1. Hybrid keyword + intent classification routing (<2s performance target)
2. Sequential multi-agent coordination for cross-domain queries
3. Domain-filtered Qdrant retrieval
4. Registration-based agent discovery for scalability

**Generated Artifacts**:
- plan.md: Full implementation plan with architecture diagrams
- research.md: Technical decisions with rationale and alternatives
- data-model.md: Entity definitions and relationships
- contracts/openapi.yaml: Extended API specification
- quickstart.md: Step-by-step setup guide

## Outcome

- Impact: High - Complete architectural blueprint for subagent system ready for implementation
- Tests: None yet - tasks.md will define test requirements
- Files: 5 files created/updated in specs/003-reusable-subagents/
- Next prompts: Run /sp.tasks to generate implementation task list, then implement BaseAgent and Router
- Reflection: Plan balances complexity with pragmatism - sequential multi-agent over parallel, keyword routing over LLM routing

## Evaluation notes (flywheel)

- Failure modes observed: None - planning phase successful
- Graders run and results (PASS/FAIL): N/A - design phase
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Validate routing logic with 10 sample queries before full implementation
