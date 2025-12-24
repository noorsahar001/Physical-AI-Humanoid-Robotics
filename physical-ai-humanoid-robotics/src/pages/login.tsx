/**
 * Login Page Component
 * Constitution v3.0.0 - User Story 2: User Login
 *
 * Allows returning users to log in with email/password.
 */

import React, { useState, FormEvent } from "react";
import Layout from "@theme/Layout";
import { signIn } from "../lib/auth";

export default function LoginPage(): JSX.Element {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  /**
   * Handle form submission - authenticates user
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const result = await signIn.email({
        email,
        password,
      });

      if (result.error) {
        // Display generic error for security (don't reveal if email exists)
        setError("Invalid email or password");
        setLoading(false);
        return;
      }

      // Success - redirect to home page
      window.location.href = "/";
    } catch (err) {
      setError("Connection error. Please try again.");
      setLoading(false);
    }
  };

  return (
    <Layout title="Login">
      <div className="container margin-vert--lg">
        <div className="row">
          <div className="col col--4 col--offset-4">
            <h1>Login</h1>

            <form onSubmit={handleSubmit}>
              {/* Error message display */}
              {error && (
                <div
                  className="alert alert--danger margin-bottom--md"
                  role="alert"
                >
                  {error}
                </div>
              )}

              {/* Email input */}
              <div className="margin-bottom--md">
                <label htmlFor="email" className="margin-bottom--sm">
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  className="input--block"
                  style={{
                    width: "100%",
                    padding: "0.75rem",
                    fontSize: "1rem",
                    border: "1px solid var(--ifm-color-emphasis-300)",
                    borderRadius: "4px",
                  }}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  placeholder="you@example.com"
                />
              </div>

              {/* Password input */}
              <div className="margin-bottom--md">
                <label htmlFor="password" className="margin-bottom--sm">
                  Password
                </label>
                <input
                  type="password"
                  id="password"
                  className="input--block"
                  style={{
                    width: "100%",
                    padding: "0.75rem",
                    fontSize: "1rem",
                    border: "1px solid var(--ifm-color-emphasis-300)",
                    borderRadius: "4px",
                  }}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  placeholder="Enter password"
                />
              </div>

              {/* Submit button */}
              <button
                type="submit"
                className="button button--primary button--block button--lg"
                disabled={loading}
              >
                {loading ? "Signing in..." : "Sign In"}
              </button>
            </form>

            {/* Link to signup page */}
            <p className="margin-top--md text--center">
              Don't have an account?{" "}
              <a href="/signup">Sign up</a>
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
