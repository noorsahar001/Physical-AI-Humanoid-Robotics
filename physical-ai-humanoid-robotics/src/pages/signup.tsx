/**
 * Signup Page Component
 * Constitution v3.0.0 - User Story 1: User Signup
 *
 * Allows new visitors to create an account with email/password.
 * Auto-logs in after successful signup.
 */

import React, { useState, FormEvent } from "react";
import Layout from "@theme/Layout";
import { signUp, signIn } from "../lib/auth";

export default function SignupPage(): JSX.Element {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  /**
   * Handle form submission - creates account and auto-logs in
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    // Client-side validation: password minimum 8 characters
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setLoading(true);

    try {
      // Step 1: Create the account
      const signUpResult = await signUp.email({
        email,
        password,
        name: email.split("@")[0], // Use email prefix as name
      });

      if (signUpResult.error) {
        // Handle duplicate email error
        if (signUpResult.error.message?.includes("exists") ||
            signUpResult.error.code === "USER_ALREADY_EXISTS") {
          setError("An account with this email already exists");
        } else {
          setError(signUpResult.error.message || "Signup failed. Please try again.");
        }
        setLoading(false);
        return;
      }

      // Step 2: Auto-login after successful signup
      const signInResult = await signIn.email({
        email,
        password,
      });

      if (signInResult.error) {
        // Account created but login failed
        setError("Account created but login failed. Please try logging in.");
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
    <Layout title="Create Account">
      <div className="container margin-vert--lg">
        <div className="row">
          <div className="col col--4 col--offset-4">
            <h1>Create Account</h1>

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
                  Password (min 8 characters)
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
                  minLength={8}
                  autoComplete="new-password"
                  placeholder="Enter password"
                />
              </div>

              {/* Submit button */}
              <button
                type="submit"
                className="button button--primary button--block button--lg"
                disabled={loading}
              >
                {loading ? "Creating account..." : "Create Account"}
              </button>
            </form>

            {/* Link to login page */}
            <p className="margin-top--md text--center">
              Already have an account?{" "}
              <a href="/login">Login</a>
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
