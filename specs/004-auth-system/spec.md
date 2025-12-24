# Feature Specification: Authentication System for Physical AI Book

**Feature Branch**: `004-auth-system`
**Created**: 2025-12-20
**Status**: Draft
**Constitution**: v3.0.0 (Better Auth, Docusaurus/React, FastAPI)

**Input**: User description: "Implement secure authentication with Login/Signup buttons in Docusaurus navbar using Better Auth. Support email/password authentication with persistent sessions. Backend FastAPI must verify Better Auth tokens."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - User Signup (Priority: P1)

As a new visitor to the Physical AI & Humanoid Robotics book, I want to create an account using my email and password, so that I can access protected content and have a personalized experience.

**Why this priority**: Account creation is the entry point for all authenticated features. Without signup, no user can access protected content.

**Independent Test**: Can be fully tested by clicking "Signup" in the navbar, filling in email/password, submitting, and verifying the user is automatically logged in and the navbar shows "Welcome <email> | Logout".

**Acceptance Scenarios**:

1. **Given** a visitor is not authenticated, **When** they view the navbar, **Then** they see "Login | Signup" buttons.

2. **Given** a visitor clicks "Signup", **When** the signup form is displayed, **Then** they see email and password input fields with a "Create Account" button.

3. **Given** a visitor fills in a valid email and password (8+ characters), **When** they submit the signup form, **Then** a new account is created via Better Auth API and the user is automatically logged in.

4. **Given** a visitor successfully creates an account, **When** the signup completes, **Then** the navbar updates to show "Welcome <email> | Logout" without requiring a page refresh.

5. **Given** a visitor tries to signup with an email that already exists, **When** they submit the form, **Then** an error message is displayed: "An account with this email already exists."

6. **Given** a visitor submits a password with fewer than 8 characters, **When** they submit the form, **Then** an error message is displayed: "Password must be at least 8 characters."

---

### User Story 2 - User Login (Priority: P1)

As a returning user, I want to log in with my email and password, so that I can resume my authenticated session and access protected content.

**Why this priority**: Login is essential for returning users; equal priority with signup as both are required for basic authentication flow.

**Independent Test**: Can be tested by clicking "Login", entering valid credentials, submitting, and verifying navbar updates to "Welcome <email> | Logout".

**Acceptance Scenarios**:

1. **Given** a visitor clicks "Login" in the navbar, **When** the login form is displayed, **Then** they see email and password input fields with a "Sign In" button.

2. **Given** a user enters valid credentials, **When** they submit the login form, **Then** they are authenticated via Better Auth API and the navbar updates to "Welcome <email> | Logout".

3. **Given** a user enters an incorrect password, **When** they submit the login form, **Then** an error message is displayed: "Invalid email or password."

4. **Given** a user enters a non-existent email, **When** they submit the login form, **Then** an error message is displayed: "Invalid email or password." (same message for security).

5. **Given** a user successfully logs in, **When** they refresh the page, **Then** they remain logged in (session persists).

---

### User Story 3 - Session Persistence (Priority: P1)

As an authenticated user, I want my session to persist across page reloads and browser restarts, so that I don't have to log in repeatedly.

**Why this priority**: Session persistence is critical for user experience; without it, users would need to re-authenticate on every page navigation.

**Independent Test**: Can be tested by logging in, refreshing the page, closing and reopening the browser, and verifying the user remains authenticated in all cases.

**Acceptance Scenarios**:

1. **Given** a user is logged in, **When** they refresh the page, **Then** they remain logged in and see "Welcome <email> | Logout" in the navbar.

2. **Given** a user is logged in and closes the browser (with "Remember Me" enabled), **When** they reopen the browser and navigate to the site, **Then** they are still logged in.

3. **Given** a user is logged in, **When** they navigate between different pages (docs, home, chapters), **Then** their authentication state persists across all pages.

4. **Given** a user's session has expired (after 7 days default TTL), **When** they visit the site, **Then** they see "Login | Signup" and must re-authenticate.

---

### User Story 4 - User Logout (Priority: P2)

As an authenticated user, I want to log out of my account, so that I can secure my session when using a shared device.

**Why this priority**: Logout is important for security but less critical than login/signup for initial functionality.

**Independent Test**: Can be tested by logging in, clicking "Logout", and verifying the navbar reverts to "Login | Signup".

**Acceptance Scenarios**:

1. **Given** a user is logged in, **When** they click "Logout" in the navbar, **Then** their session is terminated and the navbar shows "Login | Signup".

2. **Given** a user logs out, **When** they try to access a protected API endpoint, **Then** they receive a 401 Unauthorized response.

3. **Given** a user logs out on one tab, **When** they check another tab of the same site, **Then** that tab also reflects the logged-out state (on next interaction or refresh).

---

### User Story 5 - Backend Token Verification (Priority: P2)

As a system, I want the FastAPI backend to verify Better Auth session tokens, so that protected API endpoints can authenticate users.

**Why this priority**: Backend verification enables protected content and API security; depends on frontend auth being in place.

**Independent Test**: Can be tested by making authenticated API requests with valid session cookies and verifying user data is returned, and unauthenticated requests receive 401.

**Acceptance Scenarios**:

1. **Given** an authenticated user with a valid session cookie, **When** they make a request to `GET /api/auth/session`, **Then** the backend returns user data (id, email).

2. **Given** a request without a session cookie, **When** sent to a protected endpoint, **Then** the backend returns HTTP 401 with message "Not authenticated".

3. **Given** a request with an expired or invalid session cookie, **When** sent to a protected endpoint, **Then** the backend returns HTTP 401 with message "Invalid session".

4. **Given** an authenticated user, **When** they make a request to `GET /api/chat` (RAG chatbot), **Then** the backend can identify the user from the session.

---

### User Story 6 - Navbar Authentication UI (Priority: P1)

As a visitor or user, I want the navbar to dynamically display authentication options based on my login state, so that I always see relevant actions.

**Why this priority**: The navbar is the primary UI for authentication; must work correctly for both states.

**Independent Test**: Can be tested by checking navbar in logged-out state shows "Login | Signup" and logged-in state shows "Welcome <email> | Logout".

**Acceptance Scenarios**:

1. **Given** a visitor is not authenticated, **When** they view any page, **Then** the navbar displays "Login | Signup" buttons on the right side.

2. **Given** a user is authenticated, **When** they view any page, **Then** the navbar displays "Welcome user@example.com | Logout" on the right side.

3. **Given** a user just logged in, **When** the authentication completes, **Then** the navbar updates immediately without requiring a page refresh.

4. **Given** a user just logged out, **When** the logout completes, **Then** the navbar updates immediately to show "Login | Signup".

---

### Edge Cases

- **Empty email or password**: Form displays inline validation error "Email is required" / "Password is required"
- **Invalid email format**: Form displays "Please enter a valid email address"
- **Network error during auth**: Display "Connection error. Please try again."
- **Better Auth service unavailable**: Display "Authentication service temporarily unavailable"
- **Concurrent login attempts**: Only the most recent request is processed
- **Session cookie tampering**: Invalid signature results in 401 and session cleared
- **CORS misconfiguration**: Frontend displays appropriate error; backend logs detail

## Requirements *(mandatory)*

### Functional Requirements

**Frontend (Docusaurus/React)**:

- **FR-001**: System MUST display "Login | Signup" buttons in the navbar when user is not authenticated
- **FR-002**: System MUST display "Welcome <email> | Logout" in the navbar when user is authenticated
- **FR-003**: System MUST provide a signup form with email and password fields
- **FR-004**: System MUST validate password is at least 8 characters before submission
- **FR-005**: System MUST provide a login form with email and password fields
- **FR-006**: System MUST display user-friendly error messages for authentication failures
- **FR-007**: System MUST update navbar state immediately after login/logout without page refresh
- **FR-008**: System MUST persist authentication state across page navigations
- **FR-009**: System MUST use Better Auth client SDK `signUp.email()`, `signIn.email()`, `signOut()` methods
- **FR-010**: System MUST use Better Auth `useSession()` hook for auth state management
- **FR-011**: System MUST implement auth state at Root component level using React Context

**Backend (FastAPI)**:

- **FR-012**: System MUST provide `GET /api/auth/session` endpoint to validate sessions and return user data
- **FR-013**: System MUST implement `get_current_user` dependency for protected endpoints
- **FR-014**: System MUST return HTTP 401 for unauthenticated requests to protected endpoints
- **FR-015**: System MUST validate session tokens from `better-auth.session_token` cookie
- **FR-016**: System MUST support CORS for cross-origin requests from Docusaurus frontend
- **FR-017**: System MUST NOT expose internal error details in API responses

**Security**:

- **FR-018**: System MUST use HTTP-only cookies for session tokens
- **FR-019**: System MUST use secure cookies (HTTPS-only) in production
- **FR-020**: System MUST store all secrets in environment variables (never in code)
- **FR-021**: System MUST enforce minimum 8-character password requirement
- **FR-022**: System MUST log authentication events (login, logout, failures) for auditing
- **FR-023**: System MUST NOT implement custom authentication logic (Better Auth only)

### Key Entities

- **User**: A registered account. Attributes: `id`, `email`, `name` (optional), `emailVerified` (boolean), `createdAt`, `updatedAt`
- **Session**: An active login session. Attributes: `id`, `sessionToken`, `userId`, `expiresAt`, `ipAddress`, `userAgent`, `createdAt`
- **Account**: OAuth account link (email/password is built-in). Attributes: `id`, `userId`, `providerId`, `providerAccountId`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully create an account and be auto-logged in within 3 seconds
- **SC-002**: Users can successfully log in within 2 seconds
- **SC-003**: Session persists across page refresh 100% of the time while within TTL
- **SC-004**: Navbar state updates within 500ms of authentication state change
- **SC-005**: 100% of protected API requests without valid session return 401
- **SC-006**: 100% of protected API requests with valid session return user data
- **SC-007**: No authentication-related console errors during normal operation
- **SC-008**: Authentication forms display appropriate error messages for all error scenarios

## Assumptions

- Better Auth library is compatible with Docusaurus/React 18+
- A database (PostgreSQL, SQLite, or compatible) is available for Better Auth session storage
- CORS is properly configured between Docusaurus (frontend) and FastAPI (backend)
- Environment variables are properly set in both development and production
- HTTPS is available for production deployment (required for secure cookies)
- Users have JavaScript enabled in their browsers

## Out of Scope

- OAuth social login (Google, GitHub, etc.) - can be added as future enhancement
- Email verification workflow
- Password reset / forgot password functionality
- Two-factor authentication (2FA)
- User profile management
- Role-based access control (RBAC)
- Admin dashboard for user management
- Rate limiting (can be added separately)

## Constitution Compliance

This specification aligns with Constitution v3.0.0 principles:

| Principle | Compliance |
|-----------|------------|
| XIV. Better Auth as Single Provider | FR-009, FR-010, FR-023 - Uses Better Auth exclusively |
| XV. Cookie-Based Session Persistence | FR-018, FR-019 - HTTP-only, secure cookies |
| XVI. Frontend Auth Integration | FR-001-011 - React components, useSession hook |
| XVII. Backend Auth Middleware | FR-012-016 - get_current_user dependency |
| XVIII. Security & Environment Config | FR-020-022 - Env vars, logging, no custom auth |
