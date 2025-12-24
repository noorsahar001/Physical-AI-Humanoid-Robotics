# Tasks: Authentication System

**Input**: Design documents from `/specs/004-auth-system/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/, research.md, quickstart.md

**Tests**: Manual verification per quickstart.md checklist. No automated tests specified.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1-US6)
- Include exact file paths in descriptions

## Path Conventions

```text
auth-server/              # Node.js Better Auth server (NEW)
├── src/
│   ├── auth.ts
│   └── index.ts
├── package.json
├── tsconfig.json
└── .env

physical-ai-humanoid-robotics/  # Docusaurus frontend (MODIFIED)
├── src/
│   ├── lib/auth.ts
│   ├── components/auth/
│   ├── pages/
│   └── theme/Root.tsx
└── .env

robotics-books-backend/   # FastAPI backend (MODIFIED)
├── app/routes/auth.py
└── main.py
```

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and environment configuration

- [X] T001 Create auth-server/ directory structure with src/, package.json, tsconfig.json
- [X] T002 Initialize auth-server Node.js project with dependencies in auth-server/package.json
- [X] T003 [P] Create TypeScript configuration in auth-server/tsconfig.json
- [X] T004 [P] Create .env.example for auth-server with BETTER_AUTH_SECRET, BETTER_AUTH_URL, FRONTEND_URL, AUTH_PORT
- [X] T005 [P] Install better-auth dependency in physical-ai-humanoid-robotics/package.json
- [X] T006 [P] Create .env.example for frontend with BETTER_AUTH_URL in physical-ai-humanoid-robotics/.env.example
- [X] T007 [P] Add aiosqlite>=0.20.0 to robotics-books-backend/requirements.txt

**Checkpoint**: All projects have dependencies installed and environment templates created

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core auth infrastructure that MUST complete before user story work

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Implement Better Auth configuration in auth-server/src/auth.ts with SQLite adapter and emailAndPassword enabled
- [X] T009 Implement Express server entry point in auth-server/src/index.ts mounting Better Auth at /api/auth/*
- [X] T010 Generate database schema by running npx @better-auth/cli generate in auth-server/
- [X] T011 Apply database migration by running npx @better-auth/cli migrate in auth-server/
- [X] T012 Create Better Auth client configuration in physical-ai-humanoid-robotics/src/lib/auth.ts exporting signIn, signUp, signOut, useSession
- [X] T013 Create AuthProvider React context in physical-ai-humanoid-robotics/src/components/auth/AuthProvider.tsx wrapping useSession
- [X] T014 Update Root.tsx to wrap children with AuthProvider in physical-ai-humanoid-robotics/src/theme/Root.tsx
- [X] T015 Verify auth-server starts and responds on http://localhost:3001/health

**Checkpoint**: Foundation ready - auth server running, client configured, AuthProvider in place

---

## Phase 3: User Story 1 - User Signup (Priority: P1)

**Goal**: New visitors can create accounts with email/password and be auto-logged in

**Independent Test**: Click Signup, fill form, submit, verify navbar shows "Welcome <email> | Logout"

### Implementation for User Story 1

- [X] T016 [US1] Create signup page component in physical-ai-humanoid-robotics/src/pages/signup.tsx with email/password form
- [X] T017 [US1] Implement form validation in signup.tsx requiring password minimum 8 characters
- [X] T018 [US1] Implement signup form submission calling signUp.email() then signIn.email() for auto-login
- [X] T019 [US1] Add error handling in signup.tsx displaying "An account with this email already exists" for duplicates
- [X] T020 [US1] Add error handling in signup.tsx displaying "Password must be at least 8 characters" for short passwords
- [X] T021 [US1] Add success redirect to home page after successful signup in signup.tsx

**Checkpoint**: User Story 1 complete - signup flow works end-to-end with auto-login

---

## Phase 4: User Story 2 - User Login (Priority: P1)

**Goal**: Returning users can log in with email/password

**Independent Test**: Click Login, enter valid credentials, submit, verify navbar shows "Welcome <email> | Logout"

### Implementation for User Story 2

- [X] T022 [US2] Create login page component in physical-ai-humanoid-robotics/src/pages/login.tsx with email/password form
- [X] T023 [US2] Implement login form submission calling signIn.email() in login.tsx
- [X] T024 [US2] Add error handling in login.tsx displaying "Invalid email or password" for failed login
- [X] T025 [US2] Add success redirect to home page after successful login in login.tsx
- [X] T026 [US2] Add link to signup page from login.tsx ("Don't have an account? Sign up")

**Checkpoint**: User Story 2 complete - login flow works end-to-end

---

## Phase 5: User Story 6 - Navbar Authentication UI (Priority: P1)

**Goal**: Navbar dynamically displays Login/Signup or Welcome/Logout based on auth state

**Independent Test**: Check navbar shows "Login | Signup" when logged out, "Welcome <email> | Logout" when logged in

### Implementation for User Story 6

- [X] T027 [US6] Create NavbarAuthButtons component in physical-ai-humanoid-robotics/src/components/auth/NavbarAuthButtons.tsx
- [X] T028 [US6] Implement conditional rendering in NavbarAuthButtons: show Login/Signup links when not authenticated
- [X] T029 [US6] Implement conditional rendering in NavbarAuthButtons: show Welcome <email> and Logout button when authenticated
- [X] T030 [US6] Implement logout handler in NavbarAuthButtons calling signOut() and updating UI immediately
- [X] T031 [US6] Add loading state in NavbarAuthButtons showing "Loading..." while session loads
- [X] T032 [US6] Integrate NavbarAuthButtons into Docusaurus navbar via docusaurus.config.ts custom component or swizzle

**Checkpoint**: User Story 6 complete - navbar reflects auth state correctly

---

## Phase 6: User Story 3 - Session Persistence (Priority: P1)

**Goal**: Auth state persists across page reloads and browser restarts

**Independent Test**: Log in, refresh page, close/reopen browser, verify still logged in

### Implementation for User Story 3

- [X] T033 [US3] Verify Better Auth session cookie configuration in auth-server/src/auth.ts uses HTTP-only cookies
- [X] T034 [US3] Configure session expiration to 7 days (604800 seconds) in auth-server/src/auth.ts
- [X] T035 [US3] Ensure AuthProvider in physical-ai-humanoid-robotics/src/components/auth/AuthProvider.tsx initializes session on mount
- [X] T036 [US3] Verify useSession() hook in auth.ts properly hydrates from existing cookie on page load
- [ ] T037 [US3] Test session persistence by refreshing page after login and verifying auth state maintained

**Checkpoint**: User Story 3 complete - sessions persist correctly

---

## Phase 7: User Story 4 - User Logout (Priority: P2)

**Goal**: Authenticated users can log out to terminate session

**Independent Test**: Log in, click Logout, verify navbar shows "Login | Signup" and session cookie cleared

### Implementation for User Story 4

- [X] T038 [US4] Verify signOut() method is exported from physical-ai-humanoid-robotics/src/lib/auth.ts
- [X] T039 [US4] Ensure Logout button in NavbarAuthButtons.tsx calls signOut() correctly
- [ ] T040 [US4] Verify session cookie is cleared after logout by checking browser cookies
- [ ] T041 [US4] Test logout clears auth state immediately without page refresh required

**Checkpoint**: User Story 4 complete - logout works correctly

---

## Phase 8: User Story 5 - Backend Token Verification (Priority: P2)

**Goal**: FastAPI backend validates Better Auth sessions for protected endpoints

**Independent Test**: Make authenticated request to /api/auth/session, verify user data returned; unauthenticated request returns 401

### Implementation for User Story 5

- [X] T042 [US5] Create auth routes module in robotics-books-backend/app/routes/auth.py
- [X] T043 [US5] Implement SessionUser Pydantic model in robotics-books-backend/app/routes/auth.py with id, email, name fields
- [X] T044 [US5] Implement get_current_user() dependency in robotics-books-backend/app/routes/auth.py reading session cookie
- [X] T045 [US5] Implement session validation query in get_current_user() joining session and user tables from auth.db
- [X] T046 [US5] Implement require_auth() dependency raising HTTPException(401) if no valid session
- [X] T047 [US5] Create GET /api/auth/session endpoint in auth.py returning SessionUser for valid sessions
- [X] T048 [US5] Create GET /api/auth/me endpoint in auth.py returning current authenticated user
- [X] T049 [US5] Register auth router in robotics-books-backend/main.py with app.include_router()
- [X] T050 [US5] Update CORS middleware in main.py to allow credentials (cookies) from frontend origin
- [ ] T051 [US5] Test GET /api/auth/session returns 401 without session cookie
- [ ] T052 [US5] Test GET /api/auth/session returns user data with valid session cookie

**Checkpoint**: User Story 5 complete - backend validates sessions correctly

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, verification, and cleanup

- [X] T053 Create .env files from .env.example templates for all three projects (auth-server, frontend, backend)
- [X] T054 [P] Add CSS styles for auth forms in physical-ai-humanoid-robotics/src/css/custom.css
- [X] T055 [P] Add link to login page from signup.tsx ("Already have an account? Login")
- [ ] T056 Run full verification checklist from specs/004-auth-system/quickstart.md (MANUAL)
- [ ] T057 Verify no console errors during normal auth operations in browser dev tools (MANUAL)
- [ ] T058 Verify CORS configuration allows cross-origin cookies between frontend and auth-server (MANUAL)
- [X] T059 Document startup commands in README or quickstart for all three services (See quickstart.md Step 12)

**Checkpoint**: All user stories complete and verified

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 - **BLOCKS all user stories**
- **Phases 3-8 (User Stories)**: All depend on Phase 2 completion
  - US1 (Signup), US2 (Login), US6 (Navbar): Can run in parallel as P1 stories
  - US3 (Persistence): Depends on US1 or US2 being complete (need to test login first)
  - US4 (Logout): Depends on US6 (navbar logout button)
  - US5 (Backend): Can run independently after Phase 2
- **Phase 9 (Polish)**: Depends on all user stories being complete

### User Story Dependencies

| Story | Depends On | Can Start After |
|-------|------------|-----------------|
| US1 (Signup) | Foundational | Phase 2 complete |
| US2 (Login) | Foundational | Phase 2 complete |
| US6 (Navbar) | Foundational | Phase 2 complete |
| US3 (Persistence) | US1 or US2 | Either login path works |
| US4 (Logout) | US6 | Logout button exists |
| US5 (Backend) | Foundational | Phase 2 complete |

### Within Each User Story

1. Create component/module structure
2. Implement core functionality
3. Add error handling
4. Add success handling/redirects
5. Verify independently

### Parallel Opportunities

```bash
# Phase 1 parallel tasks:
T003, T004, T005, T006, T007 (all can run in parallel)

# After Phase 2, these user stories can start in parallel:
- User Story 1 (Signup): T016-T021
- User Story 2 (Login): T022-T026
- User Story 6 (Navbar): T027-T032
- User Story 5 (Backend): T042-T052

# Phase 9 parallel tasks:
T054, T055 (independent styling/links)
```

---

## Implementation Strategy

### MVP First (Phases 1-5)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (Signup)
4. Complete Phase 4: User Story 2 (Login)
5. Complete Phase 5: User Story 6 (Navbar UI)
6. **STOP and VALIDATE**: Test signup, login, navbar independently
7. MVP delivers: Users can sign up, log in, see auth state in navbar

### Full Implementation

1. MVP complete (Phases 1-5)
2. Add Phase 6: Session Persistence
3. Add Phase 7: Logout
4. Add Phase 8: Backend Verification
5. Complete Phase 9: Polish
6. Full auth system operational

### Parallel Team Strategy

With multiple developers after Phase 2:
- Developer A: User Stories 1 + 2 (Signup/Login pages)
- Developer B: User Story 6 (Navbar UI)
- Developer C: User Story 5 (FastAPI backend)

---

## Summary

| Metric | Count |
|--------|-------|
| Total Tasks | 59 |
| Setup Phase | 7 tasks |
| Foundational Phase | 8 tasks |
| User Story 1 (Signup) | 6 tasks |
| User Story 2 (Login) | 5 tasks |
| User Story 6 (Navbar) | 6 tasks |
| User Story 3 (Persistence) | 5 tasks |
| User Story 4 (Logout) | 4 tasks |
| User Story 5 (Backend) | 11 tasks |
| Polish Phase | 7 tasks |
| Parallel Tasks | 12 tasks marked [P] |

**MVP Scope**: Phases 1-5 (US1, US2, US6) = 32 tasks

**Independent Test Criteria**:
- US1: Signup creates account and auto-logs in
- US2: Login authenticates and redirects
- US6: Navbar shows correct buttons per auth state
- US3: Session survives page refresh
- US4: Logout clears session
- US5: Backend returns 401/user data correctly
