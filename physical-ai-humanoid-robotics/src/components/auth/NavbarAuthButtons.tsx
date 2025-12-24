/**
 * Navbar Auth Buttons Component
 * Constitution v3.0.0 - User Story 6: Navbar Authentication UI
 *
 * Dynamically displays Login/Signup or Welcome/Logout based on auth state.
 */

import React, { JSX } from "react";
import { useAuth } from "./AuthProvider";
import { signOut } from "../../lib/auth";

/**
 * NavbarAuthButtons component for Docusaurus navbar
 *
 * - When not authenticated: Shows "Login | Signup" links
 * - When authenticated: Shows "Welcome <email> | Logout" button
 * - When loading: Shows "Loading..." text
 */
export default function NavbarAuthButtons(): JSX.Element {
  const { user, isLoading, isAuthenticated } = useAuth();

  /**
   * Handle logout - calls signOut and refreshes page
   */
  const handleLogout = async () => {
    try {
      await signOut();
      // Force refresh to clear auth state
      window.location.href = "/";
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <span className="navbar__item navbar-auth-buttons">
        Loading...
      </span>
    );
  }

  // Authenticated state: Show welcome message and logout button
  if (isAuthenticated && user) {
    return (
      <div className="navbar-auth-buttons">
        <span className="welcome-text">
          Welcome, {user.email}
        </span>
        <button
          onClick={handleLogout}
          className="logout-btn"
        >
          Logout
        </button>
      </div>
    );
  }

  // Unauthenticated state: Show login and signup links
  return (
    <div className="navbar-auth-buttons">
      <a href="/login" className="navbar__item navbar__link">
        Login
      </a>
      <span style={{ opacity: 0.5 }}>|</span>
      <a href="/signup" className="navbar__item navbar__link">
        Signup
      </a>
    </div>
  );
}
