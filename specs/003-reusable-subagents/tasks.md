# Tasks: Reusable Subagents for Physical AI & Humanoid Robotics

**Input**: Design documents from `/specs/003-reusable-subagents/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/
**Branch**: `003-reusable-subagents`
**Date**: 2025-12-17

**Tests**: Tests are included as per Constitution Principle VIII (Verification).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)

## User Story Mapping

| Story | Priority | Title | Description |
|-------|----------|-------|-------------|
| US1 | P1 | Glossary Term Lookup | Technical term definitions from all modules |
| US2 | P2 | Hardware Setup Guidance | Hardware requirements and recommendations |
| US3 | P2 | Module Concept Explanation | Module-specific explanations |
| US4 | P3 | Capstone Project Guidance | Autonomous Humanoid project guidance |
| US5 | P1 | Automatic Query Delegation | Main router and seamless delegation |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and agent/skills directory structure

- [X] T001 Create agents directory structure at backend/app/agents/
- [X] T002 Create skills directory structure at backend/app/skills/
- [X] T003 [P] Create agents/__init__.py with AgentRegistry class
- [X] T004 [P] Create skills/__init__.py with skill exports
- [X] T005 [P] Add agent-related schemas to backend/app/models/schemas.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core agent infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

### Core Agent Framework

- [X] T006 Create BaseAgent abstract class in backend/app/agents/base_agent.py
- [X] T007 Create AgentContext dataclass in backend/app/agents/base_agent.py
- [X] T008 Create AgentResponse dataclass in backend/app/agents/base_agent.py
- [X] T009 Create AgentDomain enum in backend/app/models/schemas.py

### Shared Skills Layer

- [X] T010 [P] Implement RAGSkill with domain filtering in backend/app/skills/rag_skill.py
- [X] T011 [P] Implement CitationSkill for source formatting in backend/app/skills/citation_skill.py
- [X] T012 [P] Implement ContextSkill for session management in backend/app/skills/context_skill.py

### Query Router Core

- [X] T013 Create RouteResult dataclass in backend/app/agents/router.py
- [X] T014 Implement QueryRouter class with keyword matching in backend/app/agents/router.py
- [X] T015 Implement intent classification fallback in backend/app/agents/router.py

### Schema Extensions

- [X] T016 [P] Add agent_used field to ChatResponse in backend/app/models/schemas.py
- [X] T017 [P] Add routing_confidence field to ChatResponse in backend/app/models/schemas.py
- [X] T018 [P] Create RouteRequest/RouteResponse schemas in backend/app/models/schemas.py
- [X] T019 [P] Create AgentListResponse/AgentSummary schemas in backend/app/models/schemas.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 5 - Automatic Query Delegation (Priority: P1)

**Goal**: Implement the main chatbot agent that receives user queries, identifies the relevant subagent based on query type, and delegates seamlessly

**Independent Test**: Send varied queries (glossary, hardware, module, capstone) to the main chatbot and verify correct routing without user intervention

### Tests for User Story 5

- [X] T020 [P] [US5] Create test_router.py with routing test matrix in backend/tests/agents/test_router.py
- [X] T021 [P] [US5] Create test cases for confidence scoring in backend/tests/agents/test_router.py
- [X] T022 [P] [US5] Create test cases for multi-domain detection in backend/tests/agents/test_router.py
- [X] T023 [P] [US5] Create fallback routing tests in backend/tests/agents/test_router.py

### Implementation for User Story 5

- [X] T024 [US5] Implement agent registration on startup in backend/app/agents/__init__.py
- [X] T025 [US5] Update RAGPipeline to use QueryRouter in backend/app/services/rag_pipeline.py
- [X] T026 [US5] Create agents route module in backend/app/routes/agents.py
- [X] T027 [US5] Implement GET /agents endpoint in backend/app/routes/agents.py
- [X] T028 [US5] Implement GET /agents/{agent_name} endpoint in backend/app/routes/agents.py
- [X] T029 [US5] Implement POST /agents/{agent_name}/chat endpoint in backend/app/routes/agents.py
- [X] T030 [US5] Implement POST /chat/route preview endpoint in backend/app/routes/chat.py
- [X] T031 [US5] Update /chat endpoint to include agent_used in response in backend/app/routes/chat.py
- [X] T032 [US5] Update /chat/stream to include agent attribution in backend/app/routes/chat.py
- [X] T033 [US5] Register agents route in main.py
- [X] T034 [US5] Update /health to include agent status in backend/app/routes/health.py

### Integration Tests for User Story 5

- [X] T035 [US5] Create subagent integration test file in backend/tests/integration/test_subagent_integration.py
- [X] T036 [US5] Test full routing flow with mock agents in backend/tests/integration/test_subagent_integration.py

**Checkpoint**: Query delegation infrastructure is functional - subagents can now be added and will be routed to automatically

---

## Phase 4: User Story 1 - Glossary Term Lookup (Priority: P1)

**Goal**: Create a subagent that answers definitions of technical terms from ROS 2, Gazebo, Isaac, and VLA

**Independent Test**: Query technical terms from any module and verify the response matches book content with citations

### Tests for User Story 1

- [X] T037 [P] [US1] Create test_glossary_agent.py in backend/tests/agents/test_glossary_agent.py
- [X] T038 [P] [US1] Test ROS 2 term definitions (topic, node, service) in backend/tests/agents/test_glossary_agent.py
- [X] T039 [P] [US1] Test Gazebo term definitions (digital twin, SDF) in backend/tests/agents/test_glossary_agent.py
- [X] T040 [P] [US1] Test Isaac term definitions in backend/tests/agents/test_glossary_agent.py
- [X] T041 [P] [US1] Test VLA term definitions in backend/tests/agents/test_glossary_agent.py
- [X] T042 [P] [US1] Test term-not-found handling in backend/tests/agents/test_glossary_agent.py

### Implementation for User Story 1

- [X] T043 [US1] Create GlossaryAgent class in backend/app/agents/glossary_agent.py
- [X] T044 [US1] Define glossary domain keywords list in backend/app/agents/glossary_agent.py
- [X] T045 [US1] Implement can_handle with definition-pattern detection in backend/app/agents/glossary_agent.py
- [X] T046 [US1] Implement system_prompt for glossary context in backend/app/agents/glossary_agent.py
- [X] T047 [US1] Implement run() method with RAGSkill domain filtering in backend/app/agents/glossary_agent.py
- [X] T048 [US1] Implement run_stream() for real-time responses in backend/app/agents/glossary_agent.py
- [X] T049 [US1] Add cross-module term disambiguation logic in backend/app/agents/glossary_agent.py
- [X] T050 [US1] Register GlossaryAgent in AgentRegistry in backend/app/agents/__init__.py

**Checkpoint**: Glossary Agent is fully functional - students can query technical terms and receive accurate definitions

---

## Phase 5: User Story 2 - Hardware Setup Guidance (Priority: P2)

**Goal**: Create a subagent to guide users about hardware setups including workstation requirements, Jetson Edge kits, GPU/CPU/RAM needs

**Independent Test**: Ask hardware-related questions and verify accurate specs, comparisons, and recommendations

### Tests for User Story 2

- [X] T051 [P] [US2] Create test_hardware_agent.py in backend/tests/agents/test_hardware_agent.py
- [X] T052 [P] [US2] Test workstation requirements query in backend/tests/agents/test_hardware_agent.py
- [X] T053 [P] [US2] Test Jetson Edge kit guidance in backend/tests/agents/test_hardware_agent.py
- [X] T054 [P] [US2] Test GPU/RAM specifications query in backend/tests/agents/test_hardware_agent.py
- [X] T055 [P] [US2] Test hardware comparison (RTX vs Jetson) in backend/tests/agents/test_hardware_agent.py
- [X] T056 [P] [US2] Test sensor requirements query (LiDAR, cameras) in backend/tests/agents/test_hardware_agent.py

### Implementation for User Story 2

- [X] T057 [US2] Create HardwareAgent class in backend/app/agents/hardware_agent.py
- [X] T058 [US2] Define hardware domain keywords list in backend/app/agents/hardware_agent.py
- [X] T059 [US2] Implement can_handle with hardware-pattern detection in backend/app/agents/hardware_agent.py
- [X] T060 [US2] Implement system_prompt for hardware guidance in backend/app/agents/hardware_agent.py
- [X] T061 [US2] Implement run() method with hardware domain filtering in backend/app/agents/hardware_agent.py
- [X] T062 [US2] Implement run_stream() for real-time responses in backend/app/agents/hardware_agent.py
- [X] T063 [US2] Add comparison logic for RTX vs Jetson scenarios in backend/app/agents/hardware_agent.py
- [X] T064 [US2] Register HardwareAgent in AgentRegistry in backend/app/agents/__init__.py

**Checkpoint**: Hardware Agent is fully functional - students can get hardware guidance for simulations, edge deployments, or labs

---

## Phase 6: User Story 3 - Module Concept Explanation (Priority: P2)

**Goal**: Create a subagent for module-specific explanations with stepwise explanations, relevant examples, or code snippets

**Independent Test**: Query concepts from each module (ROS 2, Gazebo, Isaac, VLA) and verify contextually appropriate responses

### Tests for User Story 3

- [X] T065 [P] [US3] Create test_module_info_agent.py in backend/tests/agents/test_module_info_agent.py
- [X] T066 [P] [US3] Test ROS 2 module explanations in backend/tests/agents/test_module_info_agent.py
- [X] T067 [P] [US3] Test Gazebo/Unity module explanations in backend/tests/agents/test_module_info_agent.py
- [X] T068 [P] [US3] Test Isaac module explanations in backend/tests/agents/test_module_info_agent.py
- [X] T069 [P] [US3] Test VLA module explanations in backend/tests/agents/test_module_info_agent.py
- [X] T070 [P] [US3] Test cross-module integration questions in backend/tests/agents/test_module_info_agent.py

### Implementation for User Story 3

- [X] T071 [US3] Create ModuleInfoAgent class in backend/app/agents/module_info_agent.py
- [X] T072 [US3] Define module domain keywords list per module in backend/app/agents/module_info_agent.py
- [X] T073 [US3] Implement can_handle with explanation-pattern detection in backend/app/agents/module_info_agent.py
- [X] T074 [US3] Implement system_prompt for module context in backend/app/agents/module_info_agent.py
- [X] T075 [US3] Implement run() method with module domain filtering in backend/app/agents/module_info_agent.py
- [X] T076 [US3] Implement run_stream() for real-time responses in backend/app/agents/module_info_agent.py
- [X] T077 [US3] Add prerequisite cross-referencing logic in backend/app/agents/module_info_agent.py
- [X] T078 [US3] Register ModuleInfoAgent in AgentRegistry in backend/app/agents/__init__.py

**Checkpoint**: Module Info Agent is fully functional - students can get concept explanations from any module

---

## Phase 7: User Story 4 - Capstone Project Guidance (Priority: P3)

**Goal**: Create a subagent to assist with the Autonomous Humanoid project with pipeline guidance, step-by-step instructions, and code examples

**Independent Test**: Ask capstone-specific questions covering the full pipeline (voice command -> path planning -> navigation -> object manipulation) and verify comprehensive guidance

### Tests for User Story 4

- [X] T079 [P] [US4] Create test_capstone_agent.py in backend/tests/agents/test_capstone_agent.py
- [X] T080 [P] [US4] Test voice command integration guidance in backend/tests/agents/test_capstone_agent.py
- [X] T081 [P] [US4] Test path planning guidance in backend/tests/agents/test_capstone_agent.py
- [X] T082 [P] [US4] Test navigation stack guidance in backend/tests/agents/test_capstone_agent.py
- [X] T083 [P] [US4] Test object manipulation guidance in backend/tests/agents/test_capstone_agent.py
- [X] T084 [P] [US4] Test capstone milestone query in backend/tests/agents/test_capstone_agent.py
- [X] T085 [P] [US4] Test troubleshooting guidance in backend/tests/agents/test_capstone_agent.py

### Implementation for User Story 4

- [X] T086 [US4] Create CapstoneAgent class in backend/app/agents/capstone_agent.py
- [X] T087 [US4] Define capstone domain keywords list in backend/app/agents/capstone_agent.py
- [X] T088 [US4] Implement can_handle with capstone-pattern detection in backend/app/agents/capstone_agent.py
- [X] T089 [US4] Implement system_prompt for capstone context in backend/app/agents/capstone_agent.py
- [X] T090 [US4] Implement run() method with capstone domain filtering in backend/app/agents/capstone_agent.py
- [X] T091 [US4] Implement run_stream() for real-time responses in backend/app/agents/capstone_agent.py
- [X] T092 [US4] Add pipeline-aware guidance logic (voice->plan->nav->manipulate) in backend/app/agents/capstone_agent.py
- [X] T093 [US4] Add milestone tracking helpers in backend/app/agents/capstone_agent.py
- [X] T094 [US4] Register CapstoneAgent in AgentRegistry in backend/app/agents/__init__.py

**Checkpoint**: Capstone Agent is fully functional - students can get project-specific guidance for the Autonomous Humanoid capstone

---

## Phase 8: Multi-Agent Coordination

**Purpose**: Enable handling of queries that span multiple domains

- [X] T095 Implement multi-agent detection in QueryRouter in backend/app/agents/router.py
- [X] T096 Implement sequential agent execution in backend/app/agents/router.py
- [X] T097 Implement response synthesis for multi-domain queries in backend/app/agents/router.py
- [X] T098 Add multi-agent coordination tests in backend/tests/agents/test_router.py
- [X] T099 Update ChatResponse to support multi-agent responses in backend/app/models/schemas.py

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T100 [P] Add comprehensive logging for all agents in backend/app/agents/
- [X] T101 [P] Add error handling and graceful degradation in backend/app/agents/router.py
- [X] T102 [P] Add performance metrics collection for routing decisions
- [X] T103 Validate all agents against success checklist from plan.md
- [X] T104 [P] Run quickstart.md validation steps
- [X] T105 Update API documentation with agent endpoints
- [X] T106 Code cleanup and consistent formatting across agents module

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 5 (Phase 3)**: Depends on Foundational - SHOULD be done first to enable routing
- **User Story 1 (Phase 4)**: Depends on Phase 2 + Phase 3 routing infrastructure
- **User Story 2 (Phase 5)**: Depends on Phase 2 + Phase 3 routing infrastructure
- **User Story 3 (Phase 6)**: Depends on Phase 2 + Phase 3 routing infrastructure
- **User Story 4 (Phase 7)**: Depends on Phase 2 + Phase 3 routing infrastructure
- **Multi-Agent (Phase 8)**: Depends on at least 2 user stories implemented
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 5 (P1 - Router)**: MUST be first - enables all other stories
- **User Story 1 (P1 - Glossary)**: Can start after Router is functional
- **User Story 2 (P2 - Hardware)**: Can start after Router is functional
- **User Story 3 (P2 - Module Info)**: Can start after Router is functional
- **User Story 4 (P3 - Capstone)**: Can start after Router is functional

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Agent class before methods
- can_handle() before run() before run_stream()
- Core implementation before registration
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
```bash
# All setup tasks can run in parallel
Task: T003 agents/__init__.py
Task: T004 skills/__init__.py
Task: T005 schemas.py
```

**Phase 2 (Foundational)**:
```bash
# Skills can be implemented in parallel
Task: T010 rag_skill.py
Task: T011 citation_skill.py
Task: T012 context_skill.py

# Schema extensions can run in parallel
Task: T016-T019 (all schema tasks)
```

**User Story Tests (within each story)**:
```bash
# All tests for a story can run in parallel
Task: T037-T042 (Glossary Agent tests)
Task: T051-T056 (Hardware Agent tests)
Task: T065-T070 (Module Info Agent tests)
Task: T079-T085 (Capstone Agent tests)
```

**After Router Complete**:
```bash
# User Stories 1-4 can run in parallel
Developer A: User Story 1 (Glossary)
Developer B: User Story 2 (Hardware)
Developer C: User Story 3 (Module Info)
Developer D: User Story 4 (Capstone)
```

---

## Parallel Example: Foundational Phase

```bash
# Launch all skills together:
Task: "Implement RAGSkill with domain filtering in backend/app/skills/rag_skill.py"
Task: "Implement CitationSkill for source formatting in backend/app/skills/citation_skill.py"
Task: "Implement ContextSkill for session management in backend/app/skills/context_skill.py"

# Launch all schema extensions together:
Task: "Add agent_used field to ChatResponse in backend/app/models/schemas.py"
Task: "Add routing_confidence field to ChatResponse in backend/app/models/schemas.py"
Task: "Create RouteRequest/RouteResponse schemas in backend/app/models/schemas.py"
Task: "Create AgentListResponse/AgentSummary schemas in backend/app/models/schemas.py"
```

---

## Implementation Strategy

### MVP First (Router + Glossary)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 5 (Router) - enables delegation
4. Complete Phase 4: User Story 1 (Glossary) - first domain agent
5. **STOP and VALIDATE**: Test routing to Glossary Agent
6. Deploy/demo with basic glossary functionality

### Incremental Delivery

1. Setup + Foundational + Router -> Delegation infrastructure ready
2. Add Glossary Agent -> Test independently -> Deploy/Demo (MVP!)
3. Add Hardware Agent -> Test independently -> Deploy/Demo
4. Add Module Info Agent -> Test independently -> Deploy/Demo
5. Add Capstone Agent -> Test independently -> Deploy/Demo
6. Add Multi-Agent Coordination -> Full functionality complete
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + Router together
2. Once Router is done:
   - Developer A: User Story 1 (Glossary)
   - Developer B: User Story 2 (Hardware)
   - Developer C: User Story 3 (Module Info)
   - Developer D: User Story 4 (Capstone)
3. Stories complete and integrate independently
4. Team completes Multi-Agent Coordination together

---

## Success Criteria Validation

| Criterion | Task | Validation |
|-----------|------|------------|
| All 4 agents registered | T050, T064, T078, T094 | Registry contains 4 agents |
| Router routes correctly | T020-T023 | 90%+ correct routing on 10 sample queries |
| Glossary answers terms | T037-T042 | Returns ROS 2 definition for "What is a topic?" |
| Hardware gives specs | T051-T056 | Returns GPU/RAM specs for "Isaac requirements" |
| Module Info explains | T065-T070 | Returns Module 1 content for "ROS 2 nodes" |
| Capstone guides | T079-T085 | Returns structured list for "capstone milestones" |
| Multi-agent works | T095-T099 | Coherent combined response for cross-domain query |
| Fallback works | T023 | BookAgent handles out-of-scope gracefully |
| Citations preserved | All agent tests | Responses include [Source N] format |
| Streaming works | T048, T062, T076, T091 | Real-time token delivery |

---

## Summary

| Phase | Task Count | Parallel Opportunities |
|-------|------------|----------------------|
| Phase 1: Setup | 5 | 3 tasks |
| Phase 2: Foundational | 14 | 7 tasks (skills + schemas) |
| Phase 3: US5 Router | 17 | 4 tests |
| Phase 4: US1 Glossary | 14 | 6 tests |
| Phase 5: US2 Hardware | 14 | 6 tests |
| Phase 6: US3 Module Info | 14 | 6 tests |
| Phase 7: US4 Capstone | 16 | 7 tests |
| Phase 8: Multi-Agent | 5 | 0 (sequential) |
| Phase 9: Polish | 7 | 4 tasks |
| **Total** | **106** | **43 parallel** |

### MVP Scope (Suggested)

- Phase 1: Setup (5 tasks)
- Phase 2: Foundational (14 tasks)
- Phase 3: User Story 5 - Router (17 tasks)
- Phase 4: User Story 1 - Glossary (14 tasks)
- **MVP Total: 50 tasks**

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
