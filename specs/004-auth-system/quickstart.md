# Quickstart: Authentication System

**Feature**: 004-auth-system
**Time to Complete**: ~30 minutes
**Prerequisites**: Node.js 20+, Python 3.13, pnpm or npm

## Overview

This guide walks through setting up the authentication system with:
1. Better Auth server (Node.js)
2. Docusaurus frontend integration
3. FastAPI backend session validation

## Step 1: Install Better Auth Dependencies

```bash
# Navigate to Docusaurus project
cd physical-ai-humanoid-robotics

# Install Better Auth and React client
pnpm add better-auth

# Install SQLite adapter for development
pnpm add better-sqlite3
pnpm add -D @types/better-sqlite3
```

## Step 2: Create Better Auth Server

Create `auth-server/` directory in project root:

```bash
mkdir auth-server
cd auth-server
pnpm init
pnpm add better-auth better-sqlite3 express cors dotenv
pnpm add -D typescript @types/node @types/express tsx
```

Create `auth-server/src/auth.ts`:

```typescript
import { betterAuth } from "better-auth";
import Database from "better-sqlite3";

const db = new Database("../auth.db");

export const auth = betterAuth({
  database: db,
  emailAndPassword: {
    enabled: true,
    minPasswordLength: 8,
  },
  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24,     // Update session age daily
  },
  trustedOrigins: [
    process.env.FRONTEND_URL || "http://localhost:3000",
  ],
});
```

Create `auth-server/src/index.ts`:

```typescript
import express from "express";
import cors from "cors";
import { toNodeHandler } from "better-auth/node";
import { auth } from "./auth";
import "dotenv/config";

const app = express();
const PORT = process.env.AUTH_PORT || 3001;

app.use(cors({
  origin: process.env.FRONTEND_URL || "http://localhost:3000",
  credentials: true,
}));

// Mount Better Auth handler
app.all("/api/auth/*", toNodeHandler(auth));

app.get("/health", (req, res) => {
  res.json({ status: "ok", service: "better-auth" });
});

app.listen(PORT, () => {
  console.log(`Better Auth server running on http://localhost:${PORT}`);
});
```

Create `auth-server/.env`:

```env
BETTER_AUTH_SECRET=your-32-character-secret-key-here
BETTER_AUTH_URL=http://localhost:3001
FRONTEND_URL=http://localhost:3000
AUTH_PORT=3001
```

## Step 3: Generate Database Schema

```bash
cd auth-server
npx @better-auth/cli generate
npx @better-auth/cli migrate
```

This creates `auth.db` with user, session, account, and verification tables.

## Step 4: Create Frontend Auth Client

Create `physical-ai-humanoid-robotics/src/lib/auth.ts`:

```typescript
import { createAuthClient } from "better-auth/react";

export const authClient = createAuthClient({
  baseURL: process.env.BETTER_AUTH_URL || "http://localhost:3001",
});

export const { signIn, signUp, signOut, useSession } = authClient;
```

## Step 5: Create Auth Provider

Create `physical-ai-humanoid-robotics/src/components/auth/AuthProvider.tsx`:

```tsx
import React, { createContext, useContext, ReactNode } from "react";
import { useSession } from "../../lib/auth";

interface AuthContextType {
  user: { id: string; email: string; name?: string } | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoading: true,
  isAuthenticated: false,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const { data: session, isPending } = useSession();

  const value: AuthContextType = {
    user: session?.user || null,
    isLoading: isPending,
    isAuthenticated: !!session?.user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
```

## Step 6: Create Navbar Auth Buttons

Create `physical-ai-humanoid-robotics/src/components/auth/NavbarAuthButtons.tsx`:

```tsx
import React from "react";
import { useAuth } from "./AuthProvider";
import { signOut } from "../../lib/auth";

export default function NavbarAuthButtons() {
  const { user, isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return <span className="navbar__item">Loading...</span>;
  }

  if (isAuthenticated && user) {
    return (
      <div className="navbar__items">
        <span className="navbar__item">Welcome, {user.email}</span>
        <button
          className="navbar__item navbar__link"
          onClick={() => signOut()}
        >
          Logout
        </button>
      </div>
    );
  }

  return (
    <div className="navbar__items">
      <a href="/login" className="navbar__item navbar__link">
        Login
      </a>
      <a href="/signup" className="navbar__item navbar__link">
        Signup
      </a>
    </div>
  );
}
```

## Step 7: Update Root.tsx

Update `physical-ai-humanoid-robotics/src/theme/Root.tsx`:

```tsx
import React from "react";
import { AuthProvider } from "../components/auth/AuthProvider";
import ChatbotWidget from "./ChatbotWidget";

export default function Root({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      {children}
      <ChatbotWidget />
    </AuthProvider>
  );
}
```

## Step 8: Create Login Page

Create `physical-ai-humanoid-robotics/src/pages/login.tsx`:

```tsx
import React, { useState } from "react";
import Layout from "@theme/Layout";
import { signIn } from "../lib/auth";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const result = await signIn.email({ email, password });

    if (result.error) {
      setError("Invalid email or password");
      setLoading(false);
    } else {
      window.location.href = "/";
    }
  };

  return (
    <Layout title="Login">
      <div className="container margin-vert--lg">
        <div className="row">
          <div className="col col--4 col--offset-4">
            <h1>Login</h1>
            <form onSubmit={handleSubmit}>
              {error && <div className="alert alert--danger">{error}</div>}
              <div className="margin-bottom--md">
                <label htmlFor="email">Email</label>
                <input
                  type="email"
                  id="email"
                  className="input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="margin-bottom--md">
                <label htmlFor="password">Password</label>
                <input
                  type="password"
                  id="password"
                  className="input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                />
              </div>
              <button
                type="submit"
                className="button button--primary button--block"
                disabled={loading}
              >
                {loading ? "Signing in..." : "Sign In"}
              </button>
            </form>
            <p className="margin-top--md">
              Don't have an account? <a href="/signup">Sign up</a>
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
```

## Step 9: Create Signup Page

Create `physical-ai-humanoid-robotics/src/pages/signup.tsx`:

```tsx
import React, { useState } from "react";
import Layout from "@theme/Layout";
import { signUp, signIn } from "../lib/auth";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const signUpResult = await signUp.email({
      email,
      password,
      name: email.split("@")[0],
    });

    if (signUpResult.error) {
      setError(signUpResult.error.message || "Signup failed");
      setLoading(false);
      return;
    }

    // Auto-login after signup
    const signInResult = await signIn.email({ email, password });

    if (signInResult.error) {
      setError("Account created but login failed. Please try logging in.");
      setLoading(false);
    } else {
      window.location.href = "/";
    }
  };

  return (
    <Layout title="Sign Up">
      <div className="container margin-vert--lg">
        <div className="row">
          <div className="col col--4 col--offset-4">
            <h1>Create Account</h1>
            <form onSubmit={handleSubmit}>
              {error && <div className="alert alert--danger">{error}</div>}
              <div className="margin-bottom--md">
                <label htmlFor="email">Email</label>
                <input
                  type="email"
                  id="email"
                  className="input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="margin-bottom--md">
                <label htmlFor="password">Password (min 8 characters)</label>
                <input
                  type="password"
                  id="password"
                  className="input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                />
              </div>
              <button
                type="submit"
                className="button button--primary button--block"
                disabled={loading}
              >
                {loading ? "Creating account..." : "Create Account"}
              </button>
            </form>
            <p className="margin-top--md">
              Already have an account? <a href="/login">Login</a>
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
```

## Step 10: FastAPI Session Validation

Add to `robotics-books-backend/app/routes/auth.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import aiosqlite
from datetime import datetime

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class SessionUser(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    authenticated: bool = True

async def get_current_user(request: Request) -> Optional[SessionUser]:
    """Validate session and return user."""
    token = request.cookies.get("better-auth.session_token")
    if not token:
        return None

    async with aiosqlite.connect("../auth.db") as db:
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

async def require_auth(request: Request) -> SessionUser:
    """Dependency that requires authentication."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@router.get("/session", response_model=SessionUser)
async def validate_session(user: SessionUser = Depends(require_auth)):
    """Validate session and return user data."""
    return user

@router.get("/me", response_model=SessionUser)
async def get_me(user: SessionUser = Depends(require_auth)):
    """Get current authenticated user."""
    return user
```

Register router in `main.py`:

```python
from app.routes.auth import router as auth_router
app.include_router(auth_router)
```

## Step 11: Environment Configuration

Create `.env.example` files:

**auth-server/.env.example**:
```env
BETTER_AUTH_SECRET=generate-32-char-secret-here
BETTER_AUTH_URL=http://localhost:3001
FRONTEND_URL=http://localhost:3000
AUTH_PORT=3001
```

**physical-ai-humanoid-robotics/.env.example**:
```env
BETTER_AUTH_URL=http://localhost:3001
```

## Step 12: Start Services

```bash
# Terminal 1: Better Auth server
cd auth-server
pnpm dev

# Terminal 2: Docusaurus frontend
cd physical-ai-humanoid-robotics
pnpm start

# Terminal 3: FastAPI backend
cd robotics-books-backend
uvicorn main:app --reload
```

## Verification Checklist

- [ ] Better Auth server starts on port 3001
- [ ] Docusaurus starts on port 3000
- [ ] FastAPI starts on port 8000
- [ ] `/signup` page loads and creates accounts
- [ ] `/login` page authenticates users
- [ ] Navbar shows "Welcome <email> | Logout" when logged in
- [ ] Session persists after page refresh
- [ ] Logout clears session and shows "Login | Signup"
- [ ] FastAPI `/api/auth/session` returns user data with valid cookie
- [ ] FastAPI `/api/auth/session` returns 401 without cookie

## Troubleshooting

**CORS errors**: Ensure `FRONTEND_URL` matches exactly (including trailing slash)

**Cookie not set**: Check browser dev tools > Application > Cookies for `better-auth.session_token`

**Session not persisting**: Verify `credentials: 'include'` in fetch requests

**Database errors**: Run `npx @better-auth/cli migrate` to ensure schema is up to date
