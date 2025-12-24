/**
 * Auth Provider Component
 * Constitution v3.0.0 - Principle XVI: Frontend Authentication Integration
 *
 * Wraps the application to provide authentication state via React Context.
 */

import React, { createContext, useContext, ReactNode } from "react";
import { useSession } from "../../lib/auth";

// Auth context type definition
interface AuthContextType {
  user: {
    id: string;
    email: string;
    name?: string | null;
  } | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

// Create the context with default values
const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoading: true,
  isAuthenticated: false,
});

// Props for the AuthProvider component
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * AuthProvider component that wraps the application and provides
 * authentication state to all child components.
 */
export function AuthProvider({ children }: AuthProviderProps) {
  // Use the Better Auth useSession hook to get session data
  const { data: session, isPending } = useSession();

  // Construct the auth context value
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

/**
 * Custom hook to access authentication state from any component.
 *
 * @example
 * const { user, isAuthenticated, isLoading } = useAuth();
 */
export const useAuth = () => useContext(AuthContext);

export default AuthProvider;
