---
id: 004
title: Better Auth Docusaurus FastAPI Constitution
stage: constitution
date: 2025-12-20
surface: agent
model: claude-opus-4-5-20251101
feature: none
branch: main
user: noorsahar001
command: /sp.constitution
labels: ["authentication", "better-auth", "docusaurus", "fastapi", "security"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - N/A (constitution update)
---

## Prompt

You are a Senior Full-Stack AI Engineer and Authentication Architect.

Your responsibility is to design and implement a secure, production-ready authentication system inside a Docusaurus-based book.

Core Rules

Use Better Auth (https://www.better-auth.com/)

Do NOT implement custom auth logic

Use email + password authentication

Auth must persist across page reloads

Code must be clean, modular, and reusable

Must work with Spec-Kit Plus architecture

Frontend is React (Docusaurus)

Backend is FastAPI

Follow security best practices

Use environment variables for secrets

You must think step-by-step and produce correct working code, not pseudo ideas.

## Response snapshot

Updated constitution from v2.0.0 to v3.0.0 (MAJOR version bump) adding Part 5: Secure Authentication Architecture with five new principles:

- **Principle XIV**: Better Auth as Single Authentication Provider - Mandates exclusive use of Better Auth library with email/password authentication
- **Principle XV**: Cookie-Based Session Persistence - Defines HTTP-only cookie session management with configurable TTL and encoding options
- **Principle XVI**: Frontend Authentication Integration - Specifies Docusaurus/React integration patterns including AuthProvider, LoginForm, SignupForm, ProtectedRoute components
- **Principle XVII**: Backend Authentication Middleware - Details FastAPI session validation with get_current_user dependency pattern
- **Principle XVIII**: Security and Environment Configuration - Establishes environment variable management and security practices

Updated existing principles IV, VI, VII, VIII to include authentication-related requirements. Updated Technology Stack to include Better Auth and TypeScript for authentication.

## Outcome

- Impact: Added comprehensive authentication architecture to constitution (5 new principles)
- Tests: N/A (constitution document)
- Files: 1 file modified (.specify/memory/constitution.md)
- Next prompts: /sp.specify for auth feature spec, /sp.plan for implementation planning
- Reflection: Major version bump appropriate due to new architectural requirements

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS - All placeholder tokens filled, version updated, sync impact report complete
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Implement auth feature using /sp.specify with the new constitution principles
