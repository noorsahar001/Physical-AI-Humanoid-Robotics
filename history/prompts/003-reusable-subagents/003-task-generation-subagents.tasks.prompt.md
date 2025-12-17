---
id: 003
title: Task Generation for Reusable Subagents
stage: tasks
date: 2025-12-17
surface: agent
model: claude-opus-4-5-20251101
feature: 003-reusable-subagents
branch: 003-reusable-subagents
user: system
command: /sp.tasks
labels: ["tasks", "subagents", "implementation", "part-4"]
links:
  spec: specs/003-reusable-subagents/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/003-reusable-subagents/tasks.md
tests:
  - null
---

## Prompt

You are tasked with creating detailed coding tasks for Part 4 of a book project on "Physical AI & Humanoid Robotics" using Claude Code Subagents and Agent Skills.

Objective:
- Implement reusable intelligence in the book project.
- Define exact coding tasks for each subagent and their integration with the main chatbot.

Task Requirements:

1. **Glossary Subagent**
   - Task: Create a subagent that can answer definitions of technical terms from ROS 2, Gazebo, Isaac, and VLA.
   - Input: User query asking about a term.
   - Output: Concise, accurate definition or explanation.
   - Reusability: Must be callable from any chapter.

2. **Hardware Subagent**
   - Task: Create a subagent to guide users about hardware setups.
   - Input: User query about workstation requirements, Jetson Edge kits, GPU/CPU/RAM needs.
   - Output: Clear recommendation and guidance based on course content.
   - Reusability: Usable in chapters discussing simulations, edge deployments, or labs.

3. **Module Info Subagent**
   - Task: Create a subagent for module-specific explanations.
   - Input: User query about any module (ROS 2, Gazebo, Isaac, VLA).
   - Output: Stepwise explanation of concepts, relevant examples, or code snippets.
   - Reusability: Should work across chapters covering multiple modules.

4. **Capstone Guidance Subagent**
   - Task: Create a subagent to assist with the Autonomous Humanoid project.
   - Input: User query about capstone tasks (planning, navigation, object manipulation).
   - Output: Structured guidance, step-by-step instructions, or code examples.
   - Reusability: Can be referenced in project-related chapters.

5. **Integration Tasks**
   - Task: Implement a main chatbot agent that:
     - Receives user queries.
     - Identifies the relevant subagent based on query type.
     - Delegates to appropriate subagent.

## Response snapshot

Generated comprehensive tasks.md with 106 tasks organized by user story:

**User Story Mapping:**
- US1 (P1): Glossary Term Lookup - 14 tasks
- US2 (P2): Hardware Setup Guidance - 14 tasks
- US3 (P2): Module Concept Explanation - 14 tasks
- US4 (P3): Capstone Project Guidance - 16 tasks
- US5 (P1): Automatic Query Delegation - 17 tasks

**Phase Structure:**
- Phase 1: Setup (5 tasks)
- Phase 2: Foundational (14 tasks) - BLOCKS all user stories
- Phase 3: US5 Router (17 tasks) - MUST be first
- Phase 4-7: Domain agents (Glossary, Hardware, Module Info, Capstone)
- Phase 8: Multi-Agent Coordination (5 tasks)
- Phase 9: Polish (7 tasks)

**Key Features:**
- All 106 tasks follow strict checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
- 43 tasks marked as parallelizable [P]
- 75 tasks have user story labels [US1-US5]
- MVP scope defined: 50 tasks (Setup + Foundational + Router + Glossary)
- Success criteria mapped to specific tasks

## Outcome

- Impact: Generated actionable, dependency-ordered tasks.md enabling immediate implementation
- Tests: Test tasks included for all 5 user stories per Constitution Principle VIII
- Files: specs/003-reusable-subagents/tasks.md (created)
- Next prompts: /sp.implement to begin implementation; /sp.adr for architectural decisions
- Reflection: Tasks organized by user story enable parallel development and incremental delivery

## Evaluation notes (flywheel)

- Failure modes observed: None - all tasks follow required format
- Graders run and results (PASS/FAIL): Format validation PASS (106 tasks with IDs, 75 with story labels)
- Prompt variant (if applicable): Standard /sp.tasks workflow
- Next experiment (smallest change to try): None needed - successful generation
