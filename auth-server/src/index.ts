/**
 * Better Auth Express Server
 * Constitution v3.0.0 - Principle XIV: Better Auth as Single Authentication Provider
 */

import express from "express";
import cors from "cors";
import { toNodeHandler } from "better-auth/node";
import { auth } from "./auth.js";
import "dotenv/config";

const app = express();
const PORT = process.env.AUTH_PORT || 3001;

// CORS configuration (Constitution Principle XVIII - allow frontend origin)
app.use(cors({
  origin: process.env.FRONTEND_URL || "http://localhost:3000",
  credentials: true, // Required for cookies
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Authorization"],
}));

// Parse JSON bodies
app.use(express.json());

// Health check endpoint
app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    service: "better-auth",
    timestamp: new Date().toISOString(),
  });
});

// Mount Better Auth handler at /api/auth/*
// This handles: sign-up, sign-in, sign-out, session, etc.
app.all("/api/auth/*", toNodeHandler(auth));

// Root endpoint
app.get("/", (req, res) => {
  res.json({
    message: "Better Auth Server",
    version: "1.0.0",
    health: "/health",
    auth: "/api/auth/*",
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Better Auth server running on http://localhost:${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`Auth endpoints: http://localhost:${PORT}/api/auth/*`);
});
