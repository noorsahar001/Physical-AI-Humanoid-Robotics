# Data Model: Authentication System

**Feature**: 004-auth-system
**Date**: 2025-12-20
**Database**: SQLite (dev) / PostgreSQL (prod)

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                          USER                                │
├─────────────────────────────────────────────────────────────┤
│ id: TEXT (PK, UUID)                                          │
│ email: TEXT (UNIQUE, NOT NULL)                               │
│ name: TEXT                                                   │
│ emailVerified: BOOLEAN (DEFAULT false)                       │
│ image: TEXT                                                  │
│ createdAt: TIMESTAMP (DEFAULT NOW)                           │
│ updatedAt: TIMESTAMP (DEFAULT NOW)                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         SESSION                              │
├─────────────────────────────────────────────────────────────┤
│ id: TEXT (PK, UUID)                                          │
│ userId: TEXT (FK -> user.id, NOT NULL)                       │
│ token: TEXT (UNIQUE, NOT NULL)                               │
│ expiresAt: TIMESTAMP (NOT NULL)                              │
│ ipAddress: TEXT                                              │
│ userAgent: TEXT                                              │
│ createdAt: TIMESTAMP (DEFAULT NOW)                           │
│ updatedAt: TIMESTAMP (DEFAULT NOW)                           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                         ACCOUNT                              │
├─────────────────────────────────────────────────────────────┤
│ id: TEXT (PK, UUID)                                          │
│ userId: TEXT (FK -> user.id, NOT NULL)                       │
│ accountId: TEXT (NOT NULL)                                   │
│ providerId: TEXT (NOT NULL, e.g., "credential")              │
│ accessToken: TEXT                                            │
│ refreshToken: TEXT                                           │
│ accessTokenExpiresAt: TIMESTAMP                              │
│ refreshTokenExpiresAt: TIMESTAMP                             │
│ scope: TEXT                                                  │
│ idToken: TEXT                                                │
│ password: TEXT (hashed, for credential provider)             │
│ createdAt: TIMESTAMP (DEFAULT NOW)                           │
│ updatedAt: TIMESTAMP (DEFAULT NOW)                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      VERIFICATION                            │
├─────────────────────────────────────────────────────────────┤
│ id: TEXT (PK, UUID)                                          │
│ identifier: TEXT (NOT NULL, e.g., email)                     │
│ value: TEXT (NOT NULL, verification token)                   │
│ expiresAt: TIMESTAMP (NOT NULL)                              │
│ createdAt: TIMESTAMP (DEFAULT NOW)                           │
│ updatedAt: TIMESTAMP (DEFAULT NOW)                           │
└─────────────────────────────────────────────────────────────┘
```

## Entity Definitions

### User

Represents a registered user account.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | TEXT | PK, UUID | Unique identifier |
| email | TEXT | UNIQUE, NOT NULL | User's email address |
| name | TEXT | nullable | Display name |
| emailVerified | BOOLEAN | DEFAULT false | Email verification status |
| image | TEXT | nullable | Profile image URL |
| createdAt | TIMESTAMP | DEFAULT NOW | Account creation time |
| updatedAt | TIMESTAMP | DEFAULT NOW | Last update time |

**Validation Rules**:
- Email must be valid format (RFC 5322)
- Email must be unique across all users
- Name max length: 255 characters

### Session

Represents an active authentication session.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | TEXT | PK, UUID | Unique identifier |
| userId | TEXT | FK -> user.id, NOT NULL | Associated user |
| token | TEXT | UNIQUE, NOT NULL | Session token (cookie value) |
| expiresAt | TIMESTAMP | NOT NULL | Session expiration time |
| ipAddress | TEXT | nullable | Client IP address |
| userAgent | TEXT | nullable | Client user agent string |
| createdAt | TIMESTAMP | DEFAULT NOW | Session creation time |
| updatedAt | TIMESTAMP | DEFAULT NOW | Last activity time |

**Validation Rules**:
- Token must be cryptographically random (32+ bytes)
- ExpiresAt default: 7 days from creation
- Session is invalid if expiresAt < NOW

**State Transitions**:
- CREATED: New session on login
- ACTIVE: Valid, expiresAt > NOW
- EXPIRED: expiresAt <= NOW (auto-cleanup)
- REVOKED: Explicitly logged out (deleted)

### Account

Represents an authentication provider link (email/password is "credential" provider).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | TEXT | PK, UUID | Unique identifier |
| userId | TEXT | FK -> user.id, NOT NULL | Associated user |
| accountId | TEXT | NOT NULL | Provider's user ID |
| providerId | TEXT | NOT NULL | Provider name ("credential") |
| accessToken | TEXT | nullable | OAuth access token |
| refreshToken | TEXT | nullable | OAuth refresh token |
| accessTokenExpiresAt | TIMESTAMP | nullable | Token expiration |
| refreshTokenExpiresAt | TIMESTAMP | nullable | Refresh token expiration |
| scope | TEXT | nullable | OAuth scopes |
| idToken | TEXT | nullable | OAuth ID token |
| password | TEXT | nullable | Hashed password (credential only) |
| createdAt | TIMESTAMP | DEFAULT NOW | Link creation time |
| updatedAt | TIMESTAMP | DEFAULT NOW | Last update time |

**Validation Rules**:
- For credential provider: password is required, hashed with scrypt
- Password min length: 8 characters (before hashing)
- (userId, providerId) should be unique

### Verification

Represents a verification request (email verification, password reset).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | TEXT | PK, UUID | Unique identifier |
| identifier | TEXT | NOT NULL | Target (email address) |
| value | TEXT | NOT NULL | Verification token |
| expiresAt | TIMESTAMP | NOT NULL | Token expiration |
| createdAt | TIMESTAMP | DEFAULT NOW | Request creation time |
| updatedAt | TIMESTAMP | DEFAULT NOW | Last update time |

**Note**: Verification entity is included for schema completeness but email verification is out of scope for MVP.

## Indexes

```sql
-- User indexes
CREATE INDEX idx_user_email ON user(email);

-- Session indexes
CREATE INDEX idx_session_user_id ON session(userId);
CREATE INDEX idx_session_token ON session(token);
CREATE INDEX idx_session_expires_at ON session(expiresAt);

-- Account indexes
CREATE INDEX idx_account_user_id ON account(userId);
CREATE INDEX idx_account_provider ON account(providerId, accountId);
```

## Schema Generation

Better Auth CLI generates and migrates schemas automatically:

```bash
# Generate schema migration
npx @better-auth/cli generate

# Apply migration
npx @better-auth/cli migrate
```

## FastAPI Session Query

For session validation in FastAPI, query the session table directly:

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import aiosqlite  # or asyncpg for PostgreSQL

class SessionUser(BaseModel):
    id: str
    email: str
    name: Optional[str] = None

async def get_user_from_session(token: str) -> Optional[SessionUser]:
    """Validate session token and return user if valid."""
    async with aiosqlite.connect("auth.db") as db:
        # Query session
        cursor = await db.execute(
            """
            SELECT u.id, u.email, u.name
            FROM session s
            JOIN user u ON s.userId = u.id
            WHERE s.token = ? AND s.expiresAt > ?
            """,
            (token, datetime.utcnow().isoformat())
        )
        row = await cursor.fetchone()
        if row:
            return SessionUser(id=row[0], email=row[1], name=row[2])
        return None
```
