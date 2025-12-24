# Research: Authentication System for Physical AI Book

**Feature**: 004-auth-system
**Date**: 2025-12-20
**Status**: Complete

## Research Tasks

### 1. Better Auth Integration with Docusaurus/React

**Decision**: Use `better-auth` npm package with React client (`better-auth/react`)

**Rationale**:
- Better Auth provides `createAuthClient` for React with built-in hooks
- `useSession()` hook manages auth state reactively
- Works with React 19 (current Docusaurus version)
- Cookie-based sessions work seamlessly with SSR/SSG

**Alternatives Considered**:
- NextAuth.js: Designed for Next.js, not compatible with Docusaurus
- Auth0: SaaS dependency, more complex setup
- Custom JWT: Violates Constitution Principle XIV

### 2. Database Adapter Selection

**Decision**: SQLite for development, PostgreSQL for production

**Rationale**:
- SQLite requires no additional setup for local development
- Better Auth CLI can generate/migrate schemas automatically
- PostgreSQL provides production-grade reliability
- Both supported via `better-auth` database configuration

**Alternatives Considered**:
- MySQL: Similar to PostgreSQL but less common in Node ecosystem
- MongoDB: NoSQL adds complexity for relational session data
- Redis-only: Not recommended for primary user/session storage

### 3. Better Auth Server Hosting Architecture

**Decision**: Separate Better Auth server (Node.js/Express) alongside FastAPI

**Rationale**:
- Better Auth is a TypeScript library requiring Node.js runtime
- FastAPI (Python) cannot directly run Better Auth
- Two-service architecture: Better Auth handles auth, FastAPI validates sessions
- Shared database for session validation

**Architecture**:
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Docusaurus    │────▶│  Better Auth    │────▶│    Database     │
│   (React)       │     │  Server (Node)  │     │  (SQLite/PG)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                                               ▲
         │              ┌─────────────────┐              │
         └─────────────▶│    FastAPI      │──────────────┘
                        │    Backend      │ (validates sessions)
                        └─────────────────┘
```

**Alternatives Considered**:
- All-in-one FastAPI with custom auth: Violates Principle XIV
- Third-party auth service (Auth0, Clerk): External dependency
- Better Auth in serverless functions: Complex deployment

### 4. Session Validation in FastAPI

**Decision**: Direct database query to validate session tokens

**Rationale**:
- FastAPI reads `better-auth.session_token` cookie
- Queries shared database to validate session
- Returns user data from database if valid
- No HTTP call to Better Auth server needed (performance)

**Implementation Pattern**:
```python
async def validate_session(token: str) -> User | None:
    # Query session table directly
    session = await db.get_session_by_token(token)
    if not session or session.expires_at < datetime.utcnow():
        return None
    return await db.get_user_by_id(session.user_id)
```

**Alternatives Considered**:
- HTTP call to Better Auth `/api/auth/session`: Adds latency
- JWT validation only: Doesn't support session revocation
- Redis session cache: Additional infrastructure

### 5. Navbar Integration in Docusaurus

**Decision**: Swizzle NavbarItems and create custom NavbarAuthButtons component

**Rationale**:
- Docusaurus uses `@theme/NavbarItem` for navbar items
- Custom component can be added via `themeConfig.navbar.items`
- `useSession()` hook provides reactive auth state
- No need to modify Root.tsx beyond AuthProvider wrapping

**Component Hierarchy**:
```
Root.tsx
└── AuthProvider
    └── NavbarAuthButtons (in navbar items)
        ├── LoginButton (if !authenticated)
        ├── SignupButton (if !authenticated)
        ├── WelcomeText (if authenticated)
        └── LogoutButton (if authenticated)
```

**Alternatives Considered**:
- Full navbar swizzle: Too invasive, breaks updates
- Floating auth UI: Poor UX, not in navbar
- Custom theme: Over-engineered for this need

### 6. Auto-Login After Signup

**Decision**: Call `signIn.email()` immediately after successful `signUp.email()`

**Rationale**:
- Better Auth doesn't auto-login after signup by default
- Sequential API calls provide expected UX
- Single form handles both signup and implicit login

**Implementation**:
```typescript
const handleSignup = async (email: string, password: string) => {
  const signupResult = await authClient.signUp.email({ email, password, name: email });
  if (signupResult.data) {
    // Auto-login after signup
    await authClient.signIn.email({ email, password });
  }
};
```

**Alternatives Considered**:
- Custom Better Auth plugin: Over-complex
- Manual redirect to login: Poor UX
- Session cookie manipulation: Security risk

## Technology Decisions Summary

| Component | Technology | Reason |
|-----------|------------|--------|
| Auth Library | Better Auth | Constitution requirement |
| Auth Server | Node.js + Express | Better Auth requires Node runtime |
| Database | SQLite (dev) / PostgreSQL (prod) | Better Auth adapter support |
| Frontend Client | better-auth/react | React hooks integration |
| Session Cookie | HTTP-only, Secure | Security best practice |
| FastAPI Integration | Direct DB session query | Performance |
| Navbar Integration | Custom NavbarAuthButtons | Docusaurus pattern |

## Resolved Clarifications

| Item | Resolution |
|------|------------|
| Database choice | SQLite for development simplicity |
| Better Auth hosting | Separate Node.js server |
| Session validation | Direct database query in FastAPI |
| Auto-login after signup | Sequential signUp + signIn calls |
| Navbar UI pattern | Custom component in navbar items |
