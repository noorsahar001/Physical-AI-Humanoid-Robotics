# Implementation Plan: Authentication System

**Branch**: `004-auth-system` | **Date**: 2025-12-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-auth-system/spec.md`

## Summary

Implement secure email/password authentication for the Physical AI & Humanoid Robotics book using Better Auth. The system adds Login/Signup buttons to the Docusaurus navbar, creates a separate Node.js auth server for Better Auth, and integrates session validation into the existing FastAPI backend. Sessions persist via HTTP-only cookies with 7-day TTL.

## Technical Context

**Language/Version**: TypeScript 5.6 (frontend/auth), Python 3.13 (backend)
**Primary Dependencies**:
- Frontend: better-auth, React 19, Docusaurus 3.9
- Auth Server: better-auth, express, better-sqlite3
- Backend: FastAPI, aiosqlite

**Storage**: SQLite (development), PostgreSQL (production) - shared between auth server and FastAPI
**Testing**: Manual verification per quickstart checklist
**Target Platform**: Web (Chrome, Firefox, Safari)
**Project Type**: Web application (frontend + auth server + backend)
**Performance Goals**: Login/signup < 3s, session validation < 100ms
**Constraints**: HTTP-only cookies, CORS configured for cross-origin auth
**Scale/Scope**: Single user sessions, no concurrent device limit

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| XIV. Better Auth as Single Provider | PASS | Uses Better Auth exclusively; no custom auth logic |
| XV. Cookie-Based Session Persistence | PASS | HTTP-only cookies, 7-day TTL, session table with required fields |
| XVI. Frontend Auth Integration | PASS | AuthProvider, LoginForm, SignupForm, NavbarAuthButtons components |
| XVII. Backend Auth Middleware | PASS | get_current_user dependency, /api/auth/session endpoint |
| XVIII. Security & Environment Config | PASS | Env vars for secrets, .env.example templates |
| IV. Modular Backend Architecture | PASS | Auth routes separate from chat/ingest routes |
| VI. Dependency Integrity | PASS | All deps specified in package.json and requirements.txt |
| VIII. Verification Discipline | PASS | Quickstart includes verification checklist |

**All gates pass. Proceeding with implementation planning.**

## Project Structure

### Documentation (this feature)

```text
specs/004-auth-system/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research findings
├── data-model.md        # Entity definitions (User, Session, Account)
├── quickstart.md        # Step-by-step setup guide
└── contracts/
    ├── auth-api.yaml    # Better Auth server OpenAPI spec
    └── fastapi-auth.yaml # FastAPI auth endpoints spec
```

### Source Code (repository root)

```text
# Auth Server (NEW - Node.js Better Auth)
auth-server/
├── src/
│   ├── auth.ts          # Better Auth configuration
│   └── index.ts         # Express server entry point
├── package.json
├── tsconfig.json
└── .env

# Frontend (Docusaurus - MODIFIED)
physical-ai-humanoid-robotics/
├── src/
│   ├── lib/
│   │   └── auth.ts              # Better Auth client
│   ├── components/
│   │   └── auth/
│   │       ├── AuthProvider.tsx  # React context provider
│   │       ├── NavbarAuthButtons.tsx # Navbar buttons
│   │       ├── LoginForm.tsx     # Login form component
│   │       └── SignupForm.tsx    # Signup form component
│   ├── pages/
│   │   ├── login.tsx            # Login page
│   │   └── signup.tsx           # Signup page
│   └── theme/
│       └── Root.tsx             # Modified to wrap with AuthProvider
└── .env

# Backend (FastAPI - MODIFIED)
robotics-books-backend/
├── app/
│   └── routes/
│       └── auth.py              # Session validation routes (NEW)
└── main.py                      # Register auth router (MODIFIED)

# Shared
auth.db                          # SQLite database (development)
```

**Structure Decision**: Three-tier web application with separate auth server (Node.js) for Better Auth, React frontend (Docusaurus), and Python backend (FastAPI). Shared SQLite database enables FastAPI to validate sessions without HTTP calls to auth server.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Browser (Client)                               │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │   Login Page     │  │   Signup Page    │  │   Navbar Buttons │      │
│  │   /login         │  │   /signup        │  │   (dynamic)      │      │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘      │
│           │                     │                     │                 │
│           └──────────┬──────────┴──────────┬──────────┘                 │
│                      │                     │                            │
│              ┌───────▼───────┐     ┌───────▼───────┐                    │
│              │  Auth Client  │     │  useSession() │                    │
│              │  (better-auth)│     │     Hook      │                    │
│              └───────┬───────┘     └───────┬───────┘                    │
└──────────────────────┼─────────────────────┼────────────────────────────┘
                       │                     │
        ┌──────────────┼─────────────────────┼──────────────┐
        │              ▼                     ▼              │
        │    ┌─────────────────────────────────────┐       │
        │    │     Better Auth Server (Node.js)    │       │
        │    │     http://localhost:3001           │       │
        │    │     /api/auth/*                     │       │
        │    └─────────────────┬───────────────────┘       │
        │                      │                           │
        │                      ▼                           │
        │    ┌─────────────────────────────────────┐       │
        │    │           SQLite Database           │       │
        │    │           (auth.db)                 │       │
        │    │   ┌─────┐ ┌───────┐ ┌───────┐      │       │
        │    │   │user │ │session│ │account│      │       │
        │    │   └─────┘ └───────┘ └───────┘      │       │
        │    └─────────────────┬───────────────────┘       │
        │                      │                           │
        │                      ▼                           │
        │    ┌─────────────────────────────────────┐       │
        │    │      FastAPI Backend (Python)       │       │
        │    │      http://localhost:8000          │       │
        │    │      /api/auth/session (validate)   │       │
        │    │      /api/chatbot/chat (protected)  │       │
        │    └─────────────────────────────────────┘       │
        │                                                  │
        └──────────────────────────────────────────────────┘
                          Server Side
```

## Component Details

### Auth Server Components

| File | Purpose | Key Functions |
|------|---------|---------------|
| `auth.ts` | Better Auth configuration | Database adapter, email/password config, session settings |
| `index.ts` | Express server | Mount `toNodeHandler(auth)` at `/api/auth/*` |

### Frontend Components

| Component | Purpose | Dependencies |
|-----------|---------|--------------|
| `auth.ts` | Better Auth client | Exports `signIn`, `signUp`, `signOut`, `useSession` |
| `AuthProvider.tsx` | React context | Wraps app, provides `useAuth()` hook |
| `NavbarAuthButtons.tsx` | Navbar UI | Conditional Login/Signup or Welcome/Logout |
| `login.tsx` | Login page | Form with email/password, calls `signIn.email()` |
| `signup.tsx` | Signup page | Form, calls `signUp.email()` then `signIn.email()` |

### Backend Components

| File | Purpose | Key Functions |
|------|---------|---------------|
| `auth.py` | Auth routes | `get_current_user()` dependency, `/api/auth/session` endpoint |
| `main.py` | App entry | Register auth router |

## API Contracts Summary

### Better Auth Server (port 3001)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/sign-up/email` | POST | Create account |
| `/api/auth/sign-in/email` | POST | Login, set session cookie |
| `/api/auth/sign-out` | POST | Logout, clear cookie |
| `/api/auth/session` | GET | Get current session |

### FastAPI Backend (port 8000)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/session` | GET | Validate session from cookie |
| `/api/auth/me` | GET | Get authenticated user |

## Implementation Phases

### Phase 1: Auth Server Setup
- Create `auth-server/` directory structure
- Configure Better Auth with SQLite
- Generate database schema
- Test auth endpoints with curl

### Phase 2: Frontend Integration
- Install Better Auth client
- Create auth client configuration
- Implement AuthProvider context
- Create login and signup pages

### Phase 3: Navbar Integration
- Create NavbarAuthButtons component
- Update Root.tsx with AuthProvider
- Wire up navbar to show auth state

### Phase 4: Backend Integration
- Add aiosqlite dependency
- Create auth routes module
- Implement get_current_user dependency
- Register auth router in main.py

### Phase 5: Testing & Verification
- Run verification checklist from quickstart
- Test all user stories
- Verify session persistence

## Environment Variables

| Variable | Service | Purpose |
|----------|---------|---------|
| `BETTER_AUTH_SECRET` | Auth Server | Session signing key (32+ chars) |
| `BETTER_AUTH_URL` | Auth Server, Frontend | Auth server base URL |
| `FRONTEND_URL` | Auth Server | Allowed CORS origin |
| `AUTH_PORT` | Auth Server | Server port (default 3001) |

## Complexity Tracking

> No violations requiring justification.

| Consideration | Decision | Rationale |
|---------------|----------|-----------|
| Separate auth server | Required | Better Auth needs Node.js runtime |
| Shared SQLite DB | Chosen | Avoids HTTP calls for session validation |
| Manual auto-login | Implemented | Better Auth doesn't auto-login after signup |

## Dependencies

### New Dependencies (Auth Server)

```json
{
  "dependencies": {
    "better-auth": "^1.0.0",
    "better-sqlite3": "^11.0.0",
    "express": "^4.21.0",
    "cors": "^2.8.5",
    "dotenv": "^16.4.0"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "@types/node": "^22.0.0",
    "@types/express": "^5.0.0",
    "@types/better-sqlite3": "^7.6.0",
    "tsx": "^4.19.0"
  }
}
```

### New Dependencies (Frontend)

```json
{
  "dependencies": {
    "better-auth": "^1.0.0"
  }
}
```

### New Dependencies (Backend)

```
aiosqlite>=0.20.0
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Better Auth version changes | Breaking API changes | Pin version, monitor changelog |
| SQLite file locking | Concurrent access issues | Use WAL mode, consider PostgreSQL for production |
| CORS misconfiguration | Auth failures | Test thoroughly, document exact origins |
| Cookie not persisting | Session loss | Verify `credentials: 'include'`, check SameSite settings |

## Next Steps

After `/sp.tasks` generates the task list:
1. Start with Phase 1 (Auth Server Setup)
2. Test each phase independently
3. Integrate phases sequentially
4. Run full verification checklist

## Related Documents

- [Specification](./spec.md) - Feature requirements and user stories
- [Research](./research.md) - Technology decisions and alternatives
- [Data Model](./data-model.md) - Entity definitions and relationships
- [Quickstart](./quickstart.md) - Step-by-step setup guide
- [Auth API Contract](./contracts/auth-api.yaml) - Better Auth OpenAPI spec
- [FastAPI Auth Contract](./contracts/fastapi-auth.yaml) - Backend auth endpoints
