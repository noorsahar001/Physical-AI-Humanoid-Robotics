/**
 * Better Auth Client Configuration
 * Constitution v3.0.0 - Principle XVI: Frontend Authentication Integration
 */

import { createAuthClient } from "better-auth/react";

// Auth server URL - Docusaurus doesn't expose process.env to browser code
// For production, this should be updated to the deployed auth server URL
const AUTH_SERVER_URL = "http://localhost:3001";

// Create the auth client pointing to the Better Auth server
export const authClient = createAuthClient({
  baseURL: AUTH_SERVER_URL,
});

// Export auth methods for use in components
export const { signIn, signUp, signOut, useSession } = authClient;
