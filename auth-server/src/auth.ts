/**
 * Better Auth Configuration
 * Constitution v3.0.0 - Principle XIV: Better Auth as Single Authentication Provider
 */

import { betterAuth } from "better-auth";
import Database from "better-sqlite3";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Database path - shared with FastAPI backend for session validation
const dbPath = path.resolve(__dirname, "../../auth.db");
const db = new Database(dbPath);

// Enable WAL mode for better concurrent access
db.pragma("journal_mode = WAL");

export const auth = betterAuth({
  database: db,

  // Email and password authentication (Constitution Principle XIV)
  emailAndPassword: {
    enabled: true,
    minPasswordLength: 8,
    maxPasswordLength: 128,
  },

  // Session configuration (Constitution Principle XV)
  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days in seconds
    updateAge: 60 * 60 * 24,     // Update session age daily
    cookieCache: {
      enabled: true,
      maxAge: 60 * 5, // 5 minutes cache
    },
  },

  // Trusted origins for CORS
  trustedOrigins: [
    process.env.FRONTEND_URL || "http://localhost:3000",
  ],

  // Base URL for callbacks
  baseURL: process.env.BETTER_AUTH_URL || "http://localhost:3001",

  // Secret for signing sessions
  secret: process.env.BETTER_AUTH_SECRET,
});

export type Auth = typeof auth;
