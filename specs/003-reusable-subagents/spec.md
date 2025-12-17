# Feature Specification: Reusable Subagents for Physical AI & Humanoid Robotics

**Feature Branch**: `003-reusable-subagents`
**Created**: 2025-12-17
**Status**: Draft
**Input**: Implement reusable intelligence using Claude Code Subagents and Agent Skills for the Physical AI & Humanoid Robotics book project

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Glossary Term Lookup (Priority: P1)

A student reading about ROS 2 nodes encounters the term "topic" and wants to understand its meaning in the robotics context. They ask the chatbot "What is a topic in ROS 2?" and receive an accurate, context-specific definition derived from the book content.

**Why this priority**: Glossary lookup is the most fundamental interaction. Students frequently encounter unfamiliar technical terms, and providing accurate definitions is essential for learning. This forms the foundation that other agents build upon.

**Independent Test**: Can be fully tested by querying technical terms from any module (ROS 2, Gazebo, Isaac, VLA) and verifying the response matches book content. Delivers immediate value to students navigating technical terminology.

**Acceptance Scenarios**:

1. **Given** a student is reading about ROS 2, **When** they ask "What is a topic in ROS 2?", **Then** the Glossary Agent returns the definition from the book with a citation to the relevant passage.
2. **Given** a student asks about a term from Gazebo module, **When** they query "What is a digital twin?", **Then** the system returns the module-specific definition, not a generic one.
3. **Given** a student asks about a term not in the glossary, **When** they query "What is quantum entanglement?", **Then** the system informs them the term is not covered in this course.

---

### User Story 2 - Hardware Setup Guidance (Priority: P2)

A student preparing to run simulations needs to understand whether their RTX workstation meets the requirements, or if they should use the Jetson Edge kit. They ask the chatbot about hardware requirements and receive structured guidance based on their use case.

**Why this priority**: Hardware decisions directly impact a student's ability to complete labs and projects. Incorrect hardware choices can lead to frustration and blocked progress. This is critical but less frequently accessed than glossary terms.

**Independent Test**: Can be tested by asking hardware-related questions and verifying the agent provides accurate specs, comparisons, and recommendations. Delivers value by preventing hardware misconfigurations.

**Acceptance Scenarios**:

1. **Given** a student wants to run Isaac simulations, **When** they ask "What hardware do I need for NVIDIA Isaac?", **Then** the Hardware Agent provides minimum and recommended specifications from the book.
2. **Given** a student is choosing between setups, **When** they ask "Should I use RTX workstation or Jetson for the capstone?", **Then** the system provides a comparison with pros/cons for each option.
3. **Given** a student has specific hardware, **When** they ask "Can I run Gazebo on a laptop with integrated graphics?", **Then** the system provides an honest assessment with any limitations.

---

### User Story 3 - Module Concept Explanation (Priority: P2)

A student working through Module 3 (NVIDIA Isaac) needs help understanding perception pipeline concepts. They ask the chatbot for an explanation and receive a detailed, chapter-appropriate response that builds on prior module knowledge.

**Why this priority**: Module-specific explanations are core to the learning experience. Students need conceptual clarity to complete exercises. Tied with hardware guidance as both are essential but secondary to immediate term lookups.

**Independent Test**: Can be tested by querying concepts from each module (ROS 2, Gazebo, Isaac, VLA) and verifying responses are contextually appropriate and reference the correct chapters.

**Acceptance Scenarios**:

1. **Given** a student is in Module 3, **When** they ask "How does Isaac handle perception?", **Then** the Module Info Agent provides an explanation covering perception pipeline as described in the book.
2. **Given** a student asks about ROS 2 fundamentals, **When** they query "Explain ROS 2 nodes and services", **Then** the system provides the foundational explanation from Module 1.
3. **Given** a student asks a cross-module question, **When** they query "How does ROS 2 integrate with Gazebo?", **Then** the system synthesizes information from both modules.

---

### User Story 4 - Capstone Project Guidance (Priority: P3)

A student working on the Autonomous Humanoid capstone project needs guidance on integrating voice commands with path planning. They ask the chatbot for project-specific help and receive step-by-step guidance aligned with the capstone requirements.

**Why this priority**: Capstone guidance is valuable but relevant only to students who have completed prerequisite modules. It serves a narrower audience at any given time but is critical for course completion.

**Independent Test**: Can be tested by asking capstone-specific questions covering the full pipeline (voice command → path planning → navigation → object manipulation) and verifying comprehensive guidance.

**Acceptance Scenarios**:

1. **Given** a student is working on the capstone, **When** they ask "How do I connect Whisper voice commands to the navigation stack?", **Then** the Capstone Agent provides integration guidance from the book.
2. **Given** a student needs project milestones, **When** they ask "What are the steps to complete the Autonomous Humanoid project?", **Then** the system provides the structured milestone list from the capstone chapter.
3. **Given** a student encounters a capstone-specific error, **When** they describe their issue, **Then** the system provides troubleshooting guidance relevant to the capstone context.

---

### User Story 5 - Automatic Query Delegation (Priority: P1)

A student asks a question without specifying which domain it relates to. The main chatbot automatically determines the appropriate subagent(s) and routes the query, returning a unified response without the student needing to know about the underlying delegation.

**Why this priority**: Seamless delegation is foundational to user experience. Students should not need to know which agent handles which domain. This enables all other user stories to function transparently.

**Independent Test**: Can be tested by sending varied queries (glossary, hardware, module, capstone) to the main chatbot and verifying correct routing without user intervention.

**Acceptance Scenarios**:

1. **Given** a student asks a glossary question to the main chatbot, **When** they query "Define LiDAR", **Then** the chatbot delegates to Glossary Agent and returns the definition seamlessly.
2. **Given** a student asks a multi-domain question, **When** they query "What sensors does Isaac use and what hardware do they require?", **Then** the chatbot coordinates Module Info and Hardware agents to synthesize a response.
3. **Given** a student asks an out-of-scope question, **When** they query "What is the weather today?", **Then** the chatbot politely informs them this is outside the course scope.

---

### Edge Cases

- What happens when a query matches multiple agents equally (e.g., "ROS 2 nodes" could be glossary or module info)?
  - System prioritizes based on query structure: definition-style queries go to Glossary, explanation-style go to Module Info.
- What happens when a subagent fails or times out?
  - System returns a graceful error message and suggests rephrasing or trying again.
- What happens when a student asks about content not yet covered in their current module?
  - System provides the information but notes it relates to a later module.
- How does the system handle follow-up questions that require context?
  - Each agent maintains conversation context within a session to support follow-ups appropriately.

## Requirements *(mandatory)*

### Functional Requirements

**Subagent Architecture**

- **FR-001**: System MUST implement four domain-specific subagents: Glossary Agent, Hardware Agent, Module Info Agent, and Capstone Agent.
- **FR-002**: Each subagent MUST operate independently and answer queries without relying on other subagents.
- **FR-003**: Subagents MUST derive all answers from the book content stored in the vector database (RAG-based retrieval).
- **FR-004**: Subagents MUST be implemented using Claude Code for consistent execution and reusability.

**Glossary Agent**

- **FR-005**: Glossary Agent MUST answer technical term definitions from all four modules (ROS 2, Gazebo/Unity, Isaac, VLA).
- **FR-006**: Glossary Agent MUST return the module-specific context for terms that appear across multiple modules.
- **FR-007**: Glossary Agent MUST indicate when a term is not found in the course glossary.

**Hardware Agent**

- **FR-008**: Hardware Agent MUST provide specifications for RTX workstation and Jetson Edge kit setups.
- **FR-009**: Hardware Agent MUST compare hardware options based on use case (simulation, edge deployment, capstone).
- **FR-010**: Hardware Agent MUST specify sensor requirements (LiDAR, Depth Cameras, IMUs) for different modules.

**Module Info Agent**

- **FR-011**: Module Info Agent MUST explain concepts from each of the five modules: ROS 2, Gazebo/Unity, Isaac, VLA, and Capstone.
- **FR-012**: Module Info Agent MUST maintain module boundaries and indicate when questions span multiple modules.
- **FR-013**: Module Info Agent MUST reference prerequisite concepts from earlier modules when explaining advanced topics.

**Capstone Agent**

- **FR-014**: Capstone Agent MUST provide guidance for the Autonomous Humanoid project pipeline: voice command → path planning → navigation → object manipulation.
- **FR-015**: Capstone Agent MUST offer milestone-based progress tracking aligned with the capstone chapter structure.
- **FR-016**: Capstone Agent MUST troubleshoot common capstone integration issues.

**Query Delegation**

- **FR-017**: Main chatbot MUST automatically delegate queries to the appropriate subagent without user specification.
- **FR-018**: Query router MUST analyze query intent to determine routing (definition vs. explanation vs. guidance).
- **FR-019**: System MUST support multi-agent coordination for queries spanning multiple domains.
- **FR-020**: System MUST provide fallback behavior with a helpful message when no subagent can handle a query.

**Reusability and Scalability**

- **FR-021**: Subagents MUST be callable from any chapter or context without duplication of logic.
- **FR-022**: Adding new subagents MUST NOT require modifications to existing agents.
- **FR-023**: Subagent interfaces MUST follow a standardized contract for interoperability.

### Key Entities

- **Subagent**: An independent, domain-specific intelligence unit that handles queries within its domain. Has a name, domain scope, and query interface.
- **Query Router**: The delegation layer that analyzes incoming queries and routes them to appropriate subagent(s). Maintains routing rules and fallback behavior.
- **Agent Skill**: A reusable capability that can be shared across subagents (e.g., citation formatting, RAG retrieval, context management).
- **Domain**: A bounded area of knowledge within the book (Glossary, Hardware, Module Content, Capstone).
- **Session Context**: Conversation state maintained within a user session to support follow-up questions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Students receive accurate answers to glossary queries 95% of the time (measured by content match with book material).
- **SC-002**: Hardware guidance queries result in actionable recommendations within 2 conversation turns.
- **SC-003**: Module concept explanations include at least one relevant citation to book content.
- **SC-004**: Capstone guidance covers all four pipeline stages (voice, planning, navigation, manipulation) when relevant to the query.
- **SC-005**: Query delegation routes to the correct subagent 90% of the time without user intervention.
- **SC-006**: Multi-domain queries receive synthesized responses from relevant agents within acceptable response time.
- **SC-007**: System gracefully handles out-of-scope queries 100% of the time (no hallucinations or crashes).
- **SC-008**: Adding a new subagent can be accomplished without modifying existing agent implementations.

## Assumptions

- The existing RAG chatbot infrastructure (Part 1-3) is functional and provides vector-based retrieval from book content.
- Book content has been ingested into Qdrant with appropriate chunking for all five modules.
- Claude Code Subagents and Agent Skills are the implementation framework as specified in the constitution.
- Session context is maintained at the application level and passed to subagents as needed.
- Standard response time expectations for web applications apply (responses within 5 seconds).
